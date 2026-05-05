"""
PaperPilot -- Live Browser Agent
================================
Uses `browser-use` to autonomously browse the web for research data.
Runs in a background thread with real-time step-by-step progress
streamed to the frontend via SSE (Server-Sent Events).

The agent:
  1. Searches Google Scholar / ArXiv for the topic
  2. Opens the top results
  3. Extracts text content from each page
  4. Returns structured findings

Progress events are pushed to a shared queue so the API can stream
them to the frontend in real-time.
"""

import asyncio
import os
import json
import time
import uuid
import queue
import threading
import logging
import re
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('paperpilot.agent')

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ──────────────────────────────────────────────
# Global session storage for SSE streaming
# ──────────────────────────────────────────────

# Maps session_id -> queue.Queue of SSE events
_agent_sessions = {}
# Maps session_id -> final result dict
_agent_results = {}


def get_agent_queue(session_id):
    """Get or create an event queue for a session."""
    if session_id not in _agent_sessions:
        _agent_sessions[session_id] = queue.Queue()
    return _agent_sessions[session_id]


def get_agent_result(session_id):
    """Get the final result for a completed session."""
    return _agent_results.get(session_id)


def push_event(session_id, event_type, data):
    """Push an SSE event to the session's queue."""
    q = get_agent_queue(session_id)
    event = {
        'type': event_type,
        'data': data,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    q.put(event)
    # Use ASCII-safe logging to avoid cp1252 errors on Windows
    msg = data.get('message', '')[:80]
    logger.info(f"[{session_id[:8]}] SSE event: {event_type} - {msg}")


def cleanup_session(session_id):
    """Clean up session data after streaming is done."""
    _agent_sessions.pop(session_id, None)
    # Keep results for a while (don't clean immediately)


# ──────────────────────────────────────────────
# Step callback for browser-use Agent
# ──────────────────────────────────────────────

def _make_step_callback(session_id):
    """
    Create a callback function that browser-use calls after each step.
    Compatible with browser-use v0.2+ callback signature.
    """
    def on_step(*args, **kwargs):
        """Flexible callback that handles varying browser-use signatures."""
        try:
            # Determine step number and agent output from args
            step_num = '?'
            message = 'Agent processing...'

            # Try to extract step info from positional args
            for arg in args:
                # If it's an integer, it's the step number
                if isinstance(arg, int):
                    step_num = arg
                    continue

                # If it has current_state, it's the AgentOutput
                if hasattr(arg, 'current_state') and arg.current_state:
                    cs = arg.current_state
                    thought = getattr(cs, 'thought', '') or ''
                    if thought:
                        message = thought[:150]
                        continue

                # If it has action info
                if hasattr(arg, 'action') and arg.action:
                    actions = arg.action
                    if isinstance(actions, list) and len(actions) > 0:
                        act = actions[0]
                        action_dict = act.model_dump() if hasattr(act, 'model_dump') else {}
                        for k, v in action_dict.items():
                            if v is not None:
                                message = f'{k}: {str(v)[:100]}'
                                break

            push_event(session_id, 'step', {
                'step': step_num,
                'message': message,
            })

        except Exception as e:
            push_event(session_id, 'step', {
                'step': '?',
                'message': f'Agent step in progress...',
            })

    return on_step


# ──────────────────────────────────────────────
# LLM initialization
# ──────────────────────────────────────────────

def _create_llm():
    """
    Create the LLM instance for browser-use.
    Uses langchain_groq.ChatGroq as the standard integration.
    Falls back to browser-use's built-in if langchain_groq is unavailable.
    """
    # Try the standard langchain integration first (most reliable)
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.1,
        )
    except ImportError:
        pass

    # Fallback: browser-use's built-in Groq wrapper
    try:
        from browser_use.llm.groq.chat import ChatGroq
        return ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.1,
        )
    except ImportError:
        pass

    # Last resort: use langchain-openai with Groq's OpenAI-compatible endpoint
    try:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            temperature=0.1,
        )
    except ImportError:
        raise ImportError(
            "No compatible LLM library found. "
            "Install one of: langchain-groq, langchain-openai"
        )


# ──────────────────────────────────────────────
# Async agent runner
# ──────────────────────────────────────────────

async def _run_agent_async(session_id, topic, search_queries):
    """
    Run the browser-use agent asynchronously.
    Searches for the topic, extracts content from results.
    """
    from browser_use import Agent

    push_event(session_id, 'status', {
        'message': 'Initializing browser agent...',
        'phase': 'init',
    })

    # Initialize the LLM
    llm = _create_llm()
    
    # Patch the LLM class to have a provider property if it's missing,
    # because newer browser-use versions crash if this doesn't exist.
    if not hasattr(llm, 'provider'):
        try:
            type(llm).provider = property(lambda self: 'groq')
        except Exception:
            pass

    # Build the research task prompt
    task = f"""You are a research assistant. Your goal is to find and extract academic content about: "{topic}"

Instructions:
1. Go to Google Scholar (https://scholar.google.com)
2. Search for: {search_queries[0] if search_queries else topic}
3. Click on the first 2-3 relevant results
4. For each result, read the page and extract:
   - The title
   - The URL
   - A summary of the key findings (2-3 sentences)
   - Any statistics, data points, or conclusions mentioned
5. After visiting 2-3 pages, stop and compile your findings.

IMPORTANT: Return your findings as a JSON object with this structure:
{{
  "findings": [
    {{
      "title": "Paper/Article title",
      "url": "https://...",
      "summary": "Key findings and conclusions",
      "key_data": "Any specific stats or data points"
    }}
  ],
  "overall_summary": "A paragraph synthesizing all findings"
}}

Be thorough but efficient. Focus on extracting factual information."""

    push_event(session_id, 'status', {
        'message': 'Launching browser - navigating to Google Scholar...',
        'phase': 'browsing',
    })

    try:
        # Build Agent kwargs — only include supported params
        agent_kwargs = {
            'task': task,
            'llm': llm,
            'max_steps': 15,
        }

        # Only add callback if supported (browser-use v0.2+)
        try:
            agent_kwargs['register_new_step_callback'] = _make_step_callback(session_id)
        except Exception:
            pass

        agent = Agent(**agent_kwargs)
        result = await agent.run()

        push_event(session_id, 'status', {
            'message': 'Browser agent finished - processing results...',
            'phase': 'processing',
        })

        # Extract the final text from the result
        final_text = _extract_result_text(result)

        # Try to parse as JSON
        agent_data = _parse_agent_json(final_text)

        if not agent_data:
            agent_data = {
                'findings': [],
                'overall_summary': final_text[:1000] if final_text else 'Agent completed but no structured data extracted.',
                'raw_text': final_text[:2000] if final_text else '',
            }

        return agent_data

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Browser agent error: {error_msg}", exc_info=True)
        push_event(session_id, 'error', {
            'message': f'Browser agent error: {error_msg[:150]}',
        })
        return {
            'findings': [],
            'overall_summary': f'Agent encountered an error: {error_msg[:200]}',
            'error': error_msg,
        }


def _extract_result_text(result):
    """
    Extract the final text output from a browser-use AgentHistoryList result.
    Handles multiple browser-use versions and result formats.
    """
    if not result:
        return ''

    # Method 1: final_result() method (browser-use v0.2+)
    if hasattr(result, 'final_result'):
        try:
            fr = result.final_result()
            if fr and isinstance(fr, str) and len(fr) > 10:
                return fr
        except Exception:
            pass

    # Method 2: Check the last history entry for extracted_content
    if hasattr(result, 'history') and result.history:
        try:
            last = result.history[-1]
            if hasattr(last, 'result') and last.result:
                for r in last.result:
                    if hasattr(r, 'extracted_content') and r.extracted_content:
                        return r.extracted_content
        except Exception:
            pass

    # Method 3: Check all history entries for any extracted content
    if hasattr(result, 'history') and result.history:
        try:
            all_content = []
            for entry in result.history:
                if hasattr(entry, 'result') and entry.result:
                    for r in entry.result:
                        if hasattr(r, 'extracted_content') and r.extracted_content:
                            all_content.append(r.extracted_content)
            if all_content:
                return '\n'.join(all_content)
        except Exception:
            pass

    # Method 4: str() fallback
    try:
        text = str(result)
        if text and len(text) > 10:
            return text
    except Exception:
        pass

    return ''


def _parse_agent_json(text):
    """
    Try to extract a valid JSON object with 'findings' from the agent's text output.
    """
    if not text:
        return None

    try:
        # Direct parse
        data = json.loads(text)
        if isinstance(data, dict) and 'findings' in data:
            return data
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        # Find JSON block in text
        json_match = re.search(r'\{[\s\S]*"findings"[\s\S]*\}', text)
        if json_match:
            data = json.loads(json_match.group())
            if isinstance(data, dict) and 'findings' in data:
                return data
    except (json.JSONDecodeError, AttributeError):
        pass

    return None


# ──────────────────────────────────────────────
# Thread-safe runner (called from Flask)
# ──────────────────────────────────────────────

def _run_in_thread(session_id, topic, search_queries):
    """Run the async agent in a new event loop inside a thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # On Windows, use WindowsSelectorEventLoopPolicy to avoid pipe errors
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            _run_agent_async(session_id, topic, search_queries)
        )
        _agent_results[session_id] = result
        push_event(session_id, 'complete', {
            'message': f'Browser agent finished - found {len(result.get("findings", []))} sources',
            'result': result,
        })
    except Exception as e:
        logger.error(f"Agent thread error: {e}", exc_info=True)
        _agent_results[session_id] = {'error': str(e), 'findings': []}
        push_event(session_id, 'error', {
            'message': f'Agent failed: {str(e)[:150]}',
        })
    finally:
        try:
            # Clean shutdown: cancel pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        loop.close()
        push_event(session_id, 'done', {'message': 'Stream closed'})


def start_agent(topic, search_queries=None):
    """
    Start the browser agent in a background thread.

    Returns: session_id to use for SSE streaming + result retrieval.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set - browser agent cannot start")

    session_id = uuid.uuid4().hex[:12]

    if not search_queries:
        search_queries = [f"{topic} research"]

    # Initialize the queue
    get_agent_queue(session_id)

    push_event(session_id, 'status', {
        'message': 'Starting browser agent...',
        'phase': 'starting',
    })

    thread = threading.Thread(
        target=_run_in_thread,
        args=(session_id, topic, search_queries),
        daemon=True,
    )
    thread.start()

    logger.info(f"Browser agent started: session={session_id}, topic='{topic}'")
    return session_id


def get_event_stream(session_id):
    """
    Generator that yields SSE events for a session.
    Used by the Flask endpoint to stream progress.
    """
    q = get_agent_queue(session_id)
    timeout_counter = 0
    max_timeout = 120  # 2 minutes max wait

    while timeout_counter < max_timeout:
        try:
            event = q.get(timeout=1)
            timeout_counter = 0  # Reset on event

            event_type = event.get('type', 'message')
            data_str = json.dumps(event)

            yield f"event: {event_type}\ndata: {data_str}\n\n"

            # Stop streaming only on terminal events
            if event_type in ('done',):
                break

        except queue.Empty:
            timeout_counter += 1
            # Send keepalive
            yield f": keepalive\n\n"

    # Final cleanup
    cleanup_session(session_id)
