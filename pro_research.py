"""
PaperPilot — Pro Research Pipeline
====================================
The Pro Search pipeline processes a 6-question intake form, generates a
research plan, then runs an enhanced search → extraction → synthesis flow.

Phases:
  1. generate_intake_chips() — AI generates topic-specific chips for Q5
  2. process_intake()        — Validates and structures the 6 answers
  3. generate_pro_plan()     — AI builds a section-by-section plan
  4. execute_pro_research()  — Full pipeline: search → extract → synthesize
"""

import os
import json
import time
import re
import hashlib
import logging
from datetime import datetime, timezone

from clients import tavily_client, groq_client

logger = logging.getLogger('paperpilot.pro')
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Academic domains for targeted searching
ACADEMIC_DOMAINS = [
    "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "researchgate.net",
    "ieee.org", "sciencedirect.com", "semanticscholar.org",
    "scholar.google.com", "ncbi.nlm.nih.gov", "nature.com", "springer.com",
]
WIKI_DOMAINS = ["en.wikipedia.org"]


# ──────────────────────────────────────────────
# UTILITY: Groq call with retry
# ──────────────────────────────────────────────

def _groq_call(groq_client, messages, max_tokens=1024, temperature=0.4, json_mode=True, retries=3):
    """Call Groq with retry + exponential backoff for rate limits.
    
    NOTE: HTTP 413 (Payload Too Large) is NOT retried — it's re-raised
    so callers can truncate their content and retry with less data.
    Only 429 (Too Many Requests) triggers backoff retry.
    """
    for attempt in range(retries):
        try:
            kwargs = {
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = groq_client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()

        except Exception as e:
            error_str = str(e).lower()
            # 413 = payload too large — don't retry, raise immediately
            if "413" in error_str or "payload too large" in error_str or "request too large" in error_str:
                logger.error(f"Groq payload too large (413). Content must be truncated.")
                raise
            # 429 = rate limit — retry with backoff
            if "rate_limit" in error_str or "429" in error_str:
                wait = (2 ** attempt) * 5
                logger.warning(f"Groq rate limit hit, waiting {wait}s (attempt {attempt+1}/{retries})")
                time.sleep(wait)
            else:
                raise
    raise Exception("Groq rate limit exceeded after retries.")


# ──────────────────────────────────────────────
# PHASE 1: Generate Intake Chips
# ──────────────────────────────────────────────

def generate_intake_chips(topic: str) -> dict:
    """
    Generate dynamic chip suggestions for the Pro Search intake form Q5
    (specific sub-topics the user might want to explore).

    Returns: {"chips": ["chip1", "chip2", ...]}
    """
    # clients.py validates API keys at import time

    prompt = f"""You are a research assistant. For the topic "{topic}", generate 6 specific sub-topics or aspects that a researcher might want to focus on.

These will be used as clickable chips in a research intake form.

Output ONLY valid JSON:
{{
  "chips": ["sub-topic 1", "sub-topic 2", "sub-topic 3", "sub-topic 4", "sub-topic 5", "sub-topic 6"]
}}

Rules:
- Each chip should be 2-5 words
- Cover diverse aspects (technical, practical, historical, ethical, etc.)
- Be specific to the topic, not generic"""

    raw = _groq_call(
        groq_client,
        [{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.6,
    )

    result = json.loads(raw)
    logger.info(f"Generated {len(result.get('chips', []))} intake chips for '{topic}'")
    return result


# ──────────────────────────────────────────────
# PHASE 2: Process Intake Form
# ──────────────────────────────────────────────

def process_intake(form_data: dict) -> dict:
    """
    Validate and structure the 6-question intake form answers.

    Expected form_data keys:
        topic, purpose, audience, depth, length, sub_topics, tone
    
    Returns structured context for plan and research generation.
    """
    topic = form_data.get('topic', '').strip()
    if not topic:
        raise ValueError("Topic is required")

    context = {
        'topic': topic,
        'purpose': form_data.get('purpose', 'academic research'),
        'audience': form_data.get('audience', 'academic'),
        'depth': form_data.get('depth', 'comprehensive'),
        'length': form_data.get('length', 'medium'),
        'sub_topics': form_data.get('sub_topics', []),
        'tone': form_data.get('tone', 'professional'),
    }

    # Map length to section count and token limits
    length_map = {
        'short': {'sections': '3-4', 'max_tokens': 2048, 'extract_limit': 800, 'source_count': 3},
        'medium': {'sections': '5-6', 'max_tokens': 4096, 'extract_limit': 1500, 'source_count': 5},
        'long': {'sections': '7-8', 'max_tokens': 6000, 'extract_limit': 2500, 'source_count': 7},
    }
    context['limits'] = length_map.get(context['length'], length_map['medium'])

    logger.info(f"Processed intake form for '{topic}': {context['length']}, {context['tone']}")
    return context


# ──────────────────────────────────────────────
# PHASE 3: Generate Pro Plan
# ──────────────────────────────────────────────

def generate_pro_plan(context: dict) -> dict:
    """
    Generate a section-by-section research plan from the intake context.
    
    Returns: {"plan": [...], "research_focus": "...", "estimated_time": "..."}
    """
    # clients.py validates API keys at import time
    limits = context.get('limits', {})

    sub_topics_str = ', '.join(context.get('sub_topics', [])) or 'general overview'

    prompt = f"""You are a research planner. Based on this intake form, create a research report plan.

Topic: "{context['topic']}"
Purpose: {context.get('purpose', 'research')}
Audience: {context.get('audience', 'academic')}
Depth: {context.get('depth', 'comprehensive')}
Report Length: {context.get('length', 'medium')} ({limits.get('sections', '5-6')} sections)
Tone: {context.get('tone', 'professional')}
Specific Focus Areas: {sub_topics_str}

Create a plan with {limits.get('sections', '5-6')} sections. Each section should have a title and a 1-sentence description.

Output ONLY valid JSON:
{{
  "plan": [
    {{"title": "Section Title", "description": "What this section will cover"}},
    {{"title": "Section Title", "description": "What this section will cover"}}
  ],
  "research_focus": "A 1-sentence summary of the research direction",
  "estimated_time": "30-60 seconds",
  "search_queries": ["query 1 for finding sources", "query 2 for finding sources", "query 3"]
}}"""

    raw = _groq_call(
        groq_client,
        [{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.4,
    )

    result = json.loads(raw)
    logger.info(f"Generated pro plan with {len(result.get('plan', []))} sections")
    return result


# ──────────────────────────────────────────────
# PHASE 4: Execute Pro Research
# ──────────────────────────────────────────────

def execute_pro_research(context: dict, plan: dict, agent_findings: dict = None) -> dict:
    """
    Full Pro Research pipeline:
      1. Multi-query source search (using plan's search_queries)
      2. Content extraction via Tavily
      3. Merge browser agent findings (if available)
      4. AI synthesis following the approved plan
    
    Returns: Full research report dict
    """
    # clients.py validates API keys at import time
    tavily = tavily_client

    topic = context['topic']
    limits = context.get('limits', {})
    source_count = limits.get('source_count', 5)
    max_tokens = limits.get('max_tokens', 4096)
    extract_limit = limits.get('extract_limit', 1500)

    logger.info(f"Pro research EXECUTE: '{topic}' | length={context.get('length')} tone={context.get('tone')} agent_findings={'yes' if agent_findings else 'no'}")

    # ── STEP 1: Enhanced Multi-query Search ──
    sources = {"research_papers": [], "wikipedia": [], "articles_blogs": []}
    search_queries = plan.get('search_queries', [f"{topic} research study"])

    # Academic search with multiple queries
    for query in search_queries[:2]:
        try:
            academic = tavily.search(
                query=f"{query} research paper study",
                search_depth="advanced",
                max_results=source_count,
                include_domains=ACADEMIC_DOMAINS,
            )
            for r in academic.get("results", []):
                if not any(s['url'] == r.get('url') for s in sources['research_papers']):
                    sources["research_papers"].append({
                        "title": r.get("title", ""), "url": r.get("url", ""),
                        "snippet": r.get("content", ""), "score": r.get("score", 0),
                        "source_type": "research_paper"
                    })
        except Exception as e:
            logger.warning(f"Academic search error: {e}")

    # Wikipedia
    try:
        wiki = tavily.search(
            query=topic,
            search_depth="advanced",
            max_results=2,
            include_domains=WIKI_DOMAINS,
        )
        sources["wikipedia"] = [
            {"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": r.get("content", ""), "score": r.get("score", 0),
             "source_type": "wikipedia"}
            for r in wiki.get("results", [])
        ]
    except Exception as e:
        logger.warning(f"Wiki search error: {e}")

    # Articles/Blogs
    try:
        blogs = tavily.search(
            query=f"{topic} explained analysis overview",
            search_depth="advanced",
            max_results=source_count,
            exclude_domains=ACADEMIC_DOMAINS + WIKI_DOMAINS,
        )
        sources["articles_blogs"] = [
            {"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": r.get("content", ""), "score": r.get("score", 0),
             "source_type": "article_blog"}
            for r in blogs.get("results", [])
        ]
    except Exception as e:
        logger.warning(f"Blog search error: {e}")

    # ── STEP 2: Extract Content ──
    all_sources = sources["research_papers"] + sources["wikipedia"] + sources["articles_blogs"]
    urls = [s["url"] for s in all_sources if s.get("url")]

    if urls:
        try:
            extracted = tavily.extract(urls=urls)
            extracted_map = {item.get("url", ""): item.get("raw_content", "") for item in extracted.get("results", [])}

            for source in all_sources:
                url = source.get("url", "")
                if url in extracted_map and extracted_map[url]:
                    source["full_content"] = extracted_map[url][:extract_limit]
                else:
                    source["full_content"] = source.get("snippet", "")
        except Exception as e:
            logger.warning(f"Extract error: {e}")
            for source in all_sources:
                source["full_content"] = source.get("snippet", "")

    # ── STEP 2.5: Merge Browser Agent Findings ──
    agent_sources = []
    agent_context_text = ""
    if agent_findings and isinstance(agent_findings, dict):
        findings = agent_findings.get('findings', [])
        for f in findings:
            agent_sources.append({
                "title": f.get("title", "Agent Finding"),
                "url": f.get("url", ""),
                "snippet": f.get("summary", ""),
                "full_content": f"{f.get('summary', '')} {f.get('key_data', '')}".strip(),
                "source_type": "agent_browsed",
                "score": 0.9,
            })
        # Also capture the overall summary
        overall = agent_findings.get('overall_summary', '')
        if overall:
            agent_context_text = f"\n--- BROWSER AGENT FINDINGS ---\n{overall}\n"

        if agent_sources:
            sources["agent_browsed"] = agent_sources
            all_sources.extend(agent_sources)
            logger.info(f"Merged {len(agent_sources)} agent findings into source pool")

    # ── STEP 3: Synthesize with Groq following the plan ──
    idx = 1
    numbered_sources = []
    for category in ["research_papers", "wikipedia", "articles_blogs"]:
        for s in sources[category]:
            numbered_sources.append({**s, "ref_id": idx})
            idx += 1

    # Add agent sources
    for s in agent_sources:
        numbered_sources.append({**s, "ref_id": idx})
        idx += 1

    if not numbered_sources:
        return {
            "topic": topic, "error": "No sources found.",
            "sections": [], "sources_used": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pro_search": True,
        }

    source_context = ""
    for s in numbered_sources:
        content = s.get('full_content', s.get('snippet', ''))[:extract_limit]
        source_context += f"\n--- SOURCE [{s['ref_id']}] ---\nTitle: {s['title']}\nURL: {s['url']}\nType: {s['source_type']}\nContent:\n{content}\n"

    # Build plan instruction
    plan_sections = plan.get('plan', [])
    plan_instruction = "\n".join([f"  {i+1}. {p['title']}: {p.get('description', '')}" for i, p in enumerate(plan_sections)])

    # Tone instructions
    tone_map = {
        "simple": "Use simple, everyday language. Avoid jargon.",
        "professional": "Use formal academic tone with precise terminology.",
        "friendly": "Use conversational, engaging tone.",
        "technical": "Use highly technical language with detailed specifications.",
    }
    tone_instruction = tone_map.get(context.get('tone', 'professional'), tone_map["professional"])

    system_prompt = f"""You are a research synthesis AI producing a professional, customized research report.

TONE: {tone_instruction}
AUDIENCE: {context.get('audience', 'academic')}
PURPOSE: {context.get('purpose', 'research')}

REPORT STRUCTURE — Follow this exact section plan:
{plan_instruction}

Output MUST be valid JSON:
{{
  "topic": "the research topic",
  "executive_summary": "A comprehensive summary (3-5 sentences)",
  "sections": [
    {{
      "title": "Section Title",
      "content": "Detailed content with inline citations [1], [2] etc.",
      "key_points": ["point 1", "point 2"]
    }}
  ],
  "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"],
  "conclusion": "Concluding paragraph",
  "sources_used": [
    {{
      "ref_id": 1,
      "title": "Source title",
      "url": "source url",
      "source_type": "research_paper|wikipedia|article_blog",
      "relevance": "Why this source is relevant"
    }}
  ]
}}

Rules:
1. Follow the section plan EXACTLY.
2. Synthesize across sources, don't just copy.
3. ALWAYS cite sources using [ref_id] notation inline.
4. Keep content factual.
5. Include ALL sources in sources_used.
6. Output ONLY valid JSON."""

    user_prompt = f"""Research Topic: {topic}

Collected Sources:
{source_context}
{agent_context_text}
Synthesize these sources into a research report following the plan. Output ONLY valid JSON."""

    # Try full content first; if 413 (too large), truncate and retry once
    try:
        raw = _groq_call(
            groq_client,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
    except Exception as e:
        if "413" in str(e).lower() or "too large" in str(e).lower() or "rate_limit_exceeded" in str(e).lower():
            logger.warning("Payload too large or TPM limit hit -- truncating sources heavily and retrying...")
            # Rebuild source_context with extremely short content to fit 6000 TPM limit
            truncated_context = ""
            half_limit = 250  # Very strict truncation
            for s in numbered_sources:
                content = s.get('full_content', s.get('snippet', ''))[:half_limit]
                truncated_context += f"\n--- SOURCE [{s['ref_id']}] ---\nTitle: {s['title']}\nURL: {s['url']}\nContent:\n{content}\n"
            user_prompt_short = f"""Research Topic: {topic}

Collected Sources:
{truncated_context}
{agent_context_text}
Synthesize these sources into a research report following the plan. Output ONLY valid JSON."""
            
            # Force max_tokens to be lower to fit within 6000 total tokens
            fallback_max_tokens = min(max_tokens, 1500)
            
            raw = _groq_call(
                groq_client,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt_short},
                ],
                max_tokens=fallback_max_tokens,
                temperature=0.3,
            )
        else:
            raise

    try:
        report = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Pro research JSON parse error: {e}")
        return {
            "topic": topic,
            "error": f"Failed to parse LLM response: {e}",
            "sections": [],
            "sources_used": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pro_search": True,
        }

    # Ensure required keys
    report.setdefault("topic", topic)
    report.setdefault("executive_summary", "")
    report.setdefault("sections", [])
    report.setdefault("key_takeaways", [])
    report.setdefault("conclusion", "")
    report.setdefault("sources_used", [])

    # Add metadata
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["total_sources"] = len(numbered_sources)
    report["source_breakdown"] = {
        "research_papers": len(sources["research_papers"]),
        "wikipedia": len(sources["wikipedia"]),
        "articles_blogs": len(sources["articles_blogs"]),
    }
    report["pro_search"] = True
    report["config"] = {
        'topic': context['topic'],
        'purpose': context.get('purpose'),
        'audience': context.get('audience'),
        'depth': context.get('depth'),
        'length': context.get('length'),
        'tone': context.get('tone'),
    }
    report["session_id"] = hashlib.sha256(topic.strip().lower().encode()).hexdigest()[:16]

    logger.info(f"Pro research complete for '{topic}': {len(report['sections'])} sections, {report['total_sources']} sources")

    return report
