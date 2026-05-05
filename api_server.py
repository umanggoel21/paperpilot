"""
PaperPilot — Flask API Server
===============================
REST API that bridges the frontend with paper_fetch.py and pdf_generator.py.

Endpoints:
    POST /api/research    — Run full research pipeline, return JSON report
    POST /api/pdf         — Generate PDF from a report, return download link
    GET  /api/health      — Health check
    GET  /api/history     — Get cached research history

Run:  python api_server.py
"""

import sys
import os
import json
import time
import re
import hashlib
import base64
import logging
from datetime import datetime, timezone
from collections import OrderedDict
from functools import wraps

from flask import Flask, request, jsonify, send_file, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Add project root to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paper_fetch import fetch_research, search_sources, extract_content, synthesize_report
from pdf_generator import generate_pdf
from deep_research import generate_questions, generate_plan, execute_deep_research

# Pro Search pipeline
try:
    from pro_research import generate_intake_chips, process_intake, generate_pro_plan, execute_pro_research
    pro_available = True
except Exception as e:
    pro_available = False
    logger_init_msg_pro = f'Pro research unavailable: {e}'

# Database layer
try:
    from database import db, init_db, save_session, get_session, get_history as db_get_history
    db_available = True
except Exception as e:
    db_available = False
    logger_init_msg_db = f'Database unavailable: {e}'

# Browser agent (live computer use)
try:
    from browser_agent import start_agent, get_event_stream, get_agent_result
    agent_available = True
except Exception as e:
    agent_available = False
    logger_init_msg_agent = f'Browser agent unavailable: {e}'

# RAG + Stealth Scraper services (new v2 features)
try:
    from rag_service import RAGService
    rag_service = RAGService()
    logger_init_msg_rag = 'RAG service initialized'
except Exception as e:
    rag_service = None
    logger_init_msg_rag = f'RAG service unavailable: {e}'

try:
    from scraper_service import StealthScraper
    stealth_scraper = StealthScraper()
    logger_init_msg_scraper = 'Stealth scraper initialized'
except Exception as e:
    stealth_scraper = None
    logger_init_msg_scraper = f'Stealth scraper unavailable: {e}'

# ──────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('paperpilot')

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
# Allow CORS from any domain so Vercel can connect to the Render API
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize database
if db_available:
    init_db(app)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# RESULT CACHE (in-memory, topic-hash keyed)
# ──────────────────────────────────────────────

CACHE_MAX_SIZE = 50
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours

class ResultCache:
    """Simple in-memory LRU cache with TTL for research results."""

    def __init__(self, max_size=CACHE_MAX_SIZE, ttl=CACHE_TTL_SECONDS):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
        self.hits = 0
        self.misses = 0

    def _key(self, topic):
        normalized = topic.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def get(self, topic):
        key = self._key(topic)
        if key in self.cache:
            entry = self.cache[key]
            age = time.time() - entry['timestamp']
            if age < self.ttl:
                self.hits += 1
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                logger.info(f"Cache HIT for '{topic}' (age: {age:.0f}s)")
                return entry['report']
            else:
                # Expired
                del self.cache[key]
                logger.info(f"Cache EXPIRED for '{topic}' (age: {age:.0f}s)")

        self.misses += 1
        return None

    def put(self, topic, report):
        key = self._key(topic)
        if len(self.cache) >= self.max_size:
            # Remove oldest
            oldest_key, _ = self.cache.popitem(last=False)
            logger.info(f"Cache EVICT oldest entry")
        self.cache[key] = {
            'report': report,
            'topic': topic,
            'timestamp': time.time(),
        }
        logger.info(f"Cache STORE for '{topic}'")

    def get_history(self, limit=10):
        """Return recent cached topics for search history."""
        entries = list(self.cache.values())
        entries.sort(key=lambda e: e['timestamp'], reverse=True)
        return [
            {
                'topic': e['topic'],
                'total_sources': e['report'].get('total_sources', 0),
                'timestamp': datetime.fromtimestamp(e['timestamp'], tz=timezone.utc).isoformat(),
            }
            for e in entries[:limit]
        ]

    def stats(self):
        return {
            'entries': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{self.hits / max(1, self.hits + self.misses) * 100:.1f}%",
        }

cache = ResultCache()


# ──────────────────────────────────────────────
# RATE LIMITING (simple per-IP)
# ──────────────────────────────────────────────

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 5       # max requests per window

rate_limit_store = {}  # ip -> [timestamps]

def check_rate_limit():
    """Returns True if request is allowed, False if rate-limited."""
    ip = request.remote_addr or 'unknown'
    now = time.time()

    if ip not in rate_limit_store:
        rate_limit_store[ip] = []

    # Clean old timestamps
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < RATE_LIMIT_WINDOW]

    if len(rate_limit_store[ip]) >= RATE_LIMIT_MAX:
        logger.warning(f"Rate limit exceeded for {ip}")
        return False

    rate_limit_store[ip].append(now)
    return True


# ──────────────────────────────────────────────
# INPUT VALIDATION
# ──────────────────────────────────────────────

MAX_TOPIC_LENGTH = 200
MIN_TOPIC_LENGTH = 3

def validate_topic(topic):
    """Validate and sanitize research topic. Returns (clean_topic, error)."""
    if not topic or not topic.strip():
        return None, "Topic is required"

    topic = topic.strip()

    if len(topic) < MIN_TOPIC_LENGTH:
        return None, f"Topic must be at least {MIN_TOPIC_LENGTH} characters"

    if len(topic) > MAX_TOPIC_LENGTH:
        return None, f"Topic must be under {MAX_TOPIC_LENGTH} characters"

    # Basic sanitization — remove control characters
    topic = re.sub(r'[\x00-\x1f\x7f]', '', topic)

    return topic, None


# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────

@app.route('/')
def serve_frontend():
    """Serve the frontend."""
    return send_from_directory('frontend', 'index.html')


@app.route('/editor')
def serve_editor():
    """Serve the inline editor page."""
    return send_from_directory('frontend', 'editor.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from frontend directory."""
    return send_from_directory('frontend', path)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint with cache stats."""
    return jsonify({
        "status": "ok",
        "service": "PaperPilot API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "keys_configured": {
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "tavily": bool(os.getenv("TAVILY_API_KEY")),
        },
        "features": {
            "pro_search": pro_available,
            "database": db_available,
            "browser_agent": agent_available,
            "rag": rag_service is not None,
            "stealth_scraper": stealth_scraper is not None,
        },
        "cache": cache.stats(),
    })


@app.route('/api/research', methods=['POST'])
def research():
    """
    Run the full research pipeline.

    Request body:
        { "topic": "your research topic" }

    Returns:
        Full research report JSON with sections, sources, etc.
    """
    # Rate limit check
    if not check_rate_limit():
        logger.warning(f"Request rate-limited: {request.remote_addr}")
        return jsonify({
            "error": "Too many requests. Please wait a minute before trying again.",
        }), 429

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    # Validate topic
    topic, error = validate_topic(data.get('topic', ''))
    if error:
        return jsonify({"error": error}), 400

    logger.info(f"Research request: '{topic}' from {request.remote_addr}")

    # Check cache first
    cached = cache.get(topic)
    if cached:
        cached['from_cache'] = True
        cached['elapsed_seconds'] = 0
        logger.info(f"Returning cached result for '{topic}'")
        return jsonify(cached)

    try:
        start = time.time()

        # Run the research pipeline
        report = fetch_research(topic)

        elapsed = time.time() - start
        report['elapsed_seconds'] = round(elapsed, 1)
        report['from_cache'] = False

        # Generate a session_id for consistency with Pro/Deep modes
        report.setdefault('session_id', hashlib.sha256(topic.strip().lower().encode()).hexdigest()[:16])

        # Check for errors
        if report.get('error'):
            logger.error(f"Research error for '{topic}': {report['error']}")
            return jsonify(report), 500

        # Cache the result
        if report.get('sections') and len(report['sections']) > 0 and not report.get('error'):
            cache.put(topic, report)

        # Save to DB if available
        if db_available:
            try:
                save_session(
                    session_id=report.get('session_id', ''),
                    topic=topic,
                    report=report,
                    mode='lite',
                )
            except Exception as e:
                logger.warning(f"DB save failed for lite research: {e}")

        logger.info(f"Research complete for '{topic}' in {elapsed:.1f}s ({report.get('total_sources', 0)} sources)")
        return jsonify(report)

    except ValueError as e:
        logger.error(f"ValueError for '{topic}': {e}")
        return jsonify({
            "error": str(e),
            "hint": "Make sure GROQ_API_KEY and TAVILY_API_KEY are set in .env"
        }), 500
    except Exception as e:
        logger.error(f"Pipeline failed for '{topic}': {e}", exc_info=True)
        return jsonify({
            "error": f"Research pipeline failed: {str(e)}",
            "topic": topic
        }), 500


@app.route('/api/pdf', methods=['POST'])
def generate_pdf_endpoint():
    """
    Generate a PDF from a research report.

    Request body:
        { "report": { ... }, "enhance": true/false }

    Returns:
        { "pdf_url": "/api/pdf/download/<filename>", "filename": "..." }
    """
    # Rate limit check
    if not check_rate_limit():
        return jsonify({"error": "Too many requests. Please wait."}), 429

    data = request.get_json()

    if not data or not data.get('report'):
        return jsonify({"error": "Missing 'report' field"}), 400

    report = data['report']
    enhance = data.get('enhance', True)

    logger.info(f"PDF generation request for '{report.get('topic', 'unknown')}'")

    try:
        # Generate PDF
        pdf_path = generate_pdf(report, enhance=enhance)

        if not pdf_path or not os.path.exists(pdf_path):
            return jsonify({"error": "PDF generation failed — no file produced"}), 500

        filename = os.path.basename(pdf_path)

        # Also encode as base64 for direct download
        with open(pdf_path, 'rb') as f:
            pdf_base64 = base64.b64encode(f.read()).decode('utf-8')

        logger.info(f"PDF generated: {filename} ({os.path.getsize(pdf_path)} bytes)")

        return jsonify({
            "pdf_url": f"/api/pdf/download/{filename}",
            "filename": filename,
            "pdf_base64": pdf_base64,
            "size_bytes": os.path.getsize(pdf_path)
        })

    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500


@app.route('/api/pdf/download/<filename>', methods=['GET'])
def download_pdf(filename):
    """Download a generated PDF file."""
    # Sanitize filename to prevent path traversal
    filename = os.path.basename(filename)
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "PDF not found"}), 404

    return send_file(filepath, mimetype='application/pdf', as_attachment=True, download_name=filename)


@app.route('/api/history', methods=['GET'])
def get_history():
    """Return recent research history from cache."""
    return jsonify({
        "history": cache.get_history(limit=10),
    })


# ──────────────────────────────────────────────
# DEEP RESEARCH ENDPOINTS
# ──────────────────────────────────────────────

# Monthly rate limit for deep research (3 per month per IP)
deep_research_usage = {}  # ip -> [timestamps]
DEEP_RESEARCH_MONTHLY_LIMIT = 3

def check_deep_rate_limit():
    """Check if IP has exceeded monthly deep research limit."""
    ip = request.remote_addr or 'unknown'
    now = time.time()
    month_seconds = 30 * 24 * 60 * 60

    if ip not in deep_research_usage:
        deep_research_usage[ip] = []

    # Clean timestamps older than 30 days
    deep_research_usage[ip] = [t for t in deep_research_usage[ip] if now - t < month_seconds]

    remaining = DEEP_RESEARCH_MONTHLY_LIMIT - len(deep_research_usage[ip])
    return remaining > 0, remaining

def record_deep_usage():
    """Record a deep research usage."""
    ip = request.remote_addr or 'unknown'
    if ip not in deep_research_usage:
        deep_research_usage[ip] = []
    deep_research_usage[ip].append(time.time())


@app.route('/api/deep/questions', methods=['POST'])
def deep_questions():
    """
    Generate 3 personalized questions for the user's topic.

    Request: {"topic": "...", "config": {"sources": 5, "length": "medium", "tone": "professional", "focus": "overview"}}
    Returns: {"questions": [{"id": 1, "question": "...", "placeholder": "..."}]}
    """
    allowed, remaining = check_deep_rate_limit()
    if not allowed:
        return jsonify({"error": "Monthly deep research limit reached (3/month). Use normal Research mode instead."}), 429

    data = request.get_json()
    if not data or not data.get('topic', '').strip():
        return jsonify({"error": "Missing topic"}), 400

    topic = data['topic'].strip()
    config = data.get('config', {})

    logger.info(f"Deep research questions for '{topic}' | remaining: {remaining}")

    try:
        result = generate_questions(topic, config)
        result['remaining_uses'] = remaining
        return jsonify(result)
    except Exception as e:
        logger.error(f"Question generation failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/deep/plan', methods=['POST'])
def deep_plan():
    """
    Generate a research plan based on topic + config + user answers.

    Request: {"topic": "...", "config": {...}, "answers": [{"question": "...", "answer": "..."}]}
    Returns: {"plan": [{"title": "...", "description": "..."}], "research_focus": "...", "estimated_time": "..."}
    """
    data = request.get_json()
    if not data or not data.get('topic'):
        return jsonify({"error": "Missing topic"}), 400

    topic = data['topic'].strip()
    config = data.get('config', {})
    answers = data.get('answers', [])

    logger.info(f"Deep research plan for '{topic}'")

    try:
        result = generate_plan(topic, config, answers)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Plan generation failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/deep/execute', methods=['POST'])
def deep_execute():
    """
    Execute the full deep research pipeline.

    Request: {"topic": "...", "config": {...}, "answers": [...], "plan": [...]}
    Returns: Full research report JSON
    """
    allowed, remaining = check_deep_rate_limit()
    if not allowed:
        return jsonify({"error": "Monthly deep research limit reached (3/month)."}), 429

    data = request.get_json()
    if not data or not data.get('topic'):
        return jsonify({"error": "Missing topic"}), 400

    topic = data['topic'].strip()
    config = data.get('config', {})
    answers = data.get('answers', [])
    plan = data.get('plan', [])

    logger.info(f"Deep research EXECUTE for '{topic}' | config={config}")

    try:
        start = time.time()
        report = execute_deep_research(topic, config, answers, plan)
        elapsed = time.time() - start

        report['elapsed_seconds'] = round(elapsed, 1)
        report['from_cache'] = False

        if report.get('error'):
            return jsonify(report), 500

        # Record usage AFTER successful completion
        record_deep_usage()

        # Cache the result (only if report is valid)
        if report.get('sections') and len(report['sections']) > 0 and not report.get('error'):
            cache.put(topic, report)

        logger.info(f"Deep research complete for '{topic}' in {elapsed:.1f}s | remaining: {remaining - 1}")
        return jsonify(report)

    except Exception as e:
        logger.error(f"Deep research failed: {e}", exc_info=True)
        return jsonify({"error": f"Deep research failed: {str(e)}"}), 500


# ──────────────────────────────────────────────
# ENHANCED RESEARCH + RAG ENDPOINTS
# ──────────────────────────────────────────────

@app.route('/api/research/enhanced', methods=['POST'])
def enhanced_research():
    """
    Enhanced research pipeline with stealth extraction + RAG indexing.

    Request body:
        { "topic": "your research topic" }

    Returns:
        Full research report JSON + extraction_log + rag_stats + session_id
    """
    # Rate limit check
    if not check_rate_limit():
        return jsonify({"error": "Too many requests. Please wait."}), 429

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    topic, error = validate_topic(data.get('topic', ''))
    if error:
        return jsonify({"error": error}), 400

    logger.info(f"Enhanced research request: '{topic}' from {request.remote_addr}")

    # Check cache first
    cached = cache.get(topic)
    if cached and cached.get('session_id'):
        cached['from_cache'] = True
        cached['elapsed_seconds'] = 0
        return jsonify(cached)

    try:
        start = time.time()

        # ── Step 1: Run standard Tavily search ──
        from clients import tavily_client, groq_client
        
        tavily = tavily_client

        # Search sources
        sources = search_sources(topic, tavily)

        # ── Step 2: Extract content (Tavily + Stealth fallback) ──
        extraction_log = []
        all_sources = (
            sources.get('research_papers', []) +
            sources.get('wikipedia', []) +
            sources.get('articles_blogs', [])
        )

        urls = [s['url'] for s in all_sources if s.get('url')]

        # First try Tavily extract
        tavily_extracted = {}
        if urls:
            try:
                extracted = tavily.extract(urls=urls)
                for item in extracted.get('results', []):
                    url = item.get('url', '')
                    content = item.get('raw_content', '')
                    if url and content and len(content) > 100:
                        tavily_extracted[url] = content
            except Exception as e:
                logger.warning(f"Tavily extract error: {e}")

        # For each source, assign content and try stealth if needed
        for source in all_sources:
            url = source.get('url', '')
            if not url:
                continue

            # Check if Tavily got it
            if url in tavily_extracted:
                source['full_content'] = tavily_extracted[url][:3000]
                extraction_log.append({
                    'url': url,
                    'title': source.get('title', ''),
                    'method': 'standard',
                    'words': len(tavily_extracted[url].split()),
                    'success': True,
                })
            else:
                # Tavily failed — try stealth scraper
                stealth_result = None
                if stealth_scraper:
                    stealth_result = stealth_scraper.extract(url)

                if stealth_result and stealth_result.get('success'):
                    source['full_content'] = stealth_result['text'][:3000]
                    extraction_log.append({
                        'url': url,
                        'title': source.get('title', ''),
                        'method': 'stealth',
                        'words': stealth_result.get('word_count', 0),
                        'success': True,
                    })
                else:
                    source['full_content'] = source.get('snippet', '')
                    extraction_log.append({
                        'url': url,
                        'title': source.get('title', ''),
                        'method': 'failed',
                        'words': len(source.get('snippet', '').split()),
                        'success': False,
                    })

        # ── Step 3: Index in ChromaDB (RAG) ──
        session_id = hashlib.sha256(topic.strip().lower().encode()).hexdigest()[:16]
        rag_stats = {'total_chunks': 0, 'total_words': 0, 'sources_indexed': 0}

        if rag_service:
            try:
                rag_stats = rag_service.index_sources(all_sources, session_id)
            except Exception as e:
                logger.error(f"RAG indexing failed: {e}")

        # ── Step 4: Synthesize with Groq ──
        report = synthesize_report(topic, sources, groq_client)

        # ── Step 5: Attach enhanced metadata ──
        elapsed = time.time() - start
        report['elapsed_seconds'] = round(elapsed, 1)
        report['from_cache'] = False
        report['session_id'] = session_id
        report['extraction_log'] = extraction_log
        report['rag_stats'] = rag_stats
        report['enhanced'] = True

        # Cache the result (only if report is valid)
        if report.get('sections') and len(report['sections']) > 0 and not report.get('error'):
            cache.put(topic, report)

        logger.info(
            f"Enhanced research complete for '{topic}' in {elapsed:.1f}s "
            f"({report.get('total_sources', 0)} sources, "
            f"{rag_stats.get('total_chunks', 0)} RAG chunks)"
        )

        return jsonify(report)

    except Exception as e:
        logger.error(f"Enhanced research failed for '{topic}': {e}", exc_info=True)
        return jsonify({"error": f"Enhanced research failed: {str(e)}"}), 500


@app.route('/api/evidence', methods=['POST'])
def get_evidence():
    """
    Query the RAG engine for evidence supporting a claim.

    Request body:
        { "sentence": "claim to verify", "session_id": "abc123" }

    Returns:
        { "evidence": [{text, source_url, source_title, similarity_score}] }
    """
    if not rag_service:
        return jsonify({"error": "RAG service not available"}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    sentence = data.get('sentence', '').strip()
    session_id = data.get('session_id', '').strip()

    if not sentence or not session_id:
        return jsonify({"error": "Both 'sentence' and 'session_id' are required"}), 400

    try:
        evidence = rag_service.query_evidence(sentence, session_id, top_k=3)
        return jsonify({"evidence": evidence})
    except Exception as e:
        logger.error(f"Evidence query failed: {e}", exc_info=True)
        return jsonify({"error": f"Evidence query failed: {str(e)}"}), 500


@app.route('/api/evidence/sources/<session_id>', methods=['GET'])
def get_evidence_sources(session_id):
    """
    Get the list of indexed sources for a session.
    """
    if not rag_service:
        return jsonify({"error": "RAG service not available"}), 503

    stats = rag_service.get_session_stats(session_id)
    if not stats:
        return jsonify({"error": "Session not found"}), 404

    return jsonify({"stats": stats})


# ──────────────────────────────────────────────
# PRO SEARCH ENDPOINTS
# ──────────────────────────────────────────────

@app.route('/api/pro/intake-chips', methods=['POST'])
def pro_intake_chips():
    """
    Generate dynamic intake chips for Pro Search form.

    Request: {"topic": "..."}
    Returns: {"chips": ["chip1", "chip2", ...]}
    """
    if not pro_available:
        return jsonify({"error": "Pro Search not available"}), 503

    data = request.get_json()
    if not data or not data.get('topic', '').strip():
        return jsonify({"error": "Missing topic"}), 400

    topic = data['topic'].strip()

    try:
        result = generate_intake_chips(topic)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Intake chips failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/pro/plan', methods=['POST'])
def pro_plan():
    """
    Generate a Pro Search research plan from intake form answers.

    Request: {"topic": "...", "purpose": "...", "audience": "...", ...}
    Returns: {"plan": [...], "research_focus": "...", "estimated_time": "..."}
    """
    if not pro_available:
        return jsonify({"error": "Pro Search not available"}), 503

    data = request.get_json()
    if not data or not data.get('topic', '').strip():
        return jsonify({"error": "Missing topic"}), 400

    try:
        context = process_intake(data)
        result = generate_pro_plan(context)
        # Pass context back so frontend can send it with execute
        result['context'] = context
        return jsonify(result)
    except Exception as e:
        logger.error(f"Pro plan failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/pro/execute', methods=['POST'])
def pro_execute():
    """
    Execute the full Pro Search pipeline.

    Request: {"context": {...}, "plan": {...}, "agent_findings": {...}}
    Returns: Full research report JSON
    """
    if not pro_available:
        return jsonify({"error": "Pro Search not available"}), 503

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    context = data.get('context', {})
    plan = data.get('plan', {})
    agent_findings = data.get('agent_findings', None)

    if not context.get('topic'):
        return jsonify({"error": "Missing topic in context"}), 400

    logger.info(f"Pro research EXECUTE for '{context['topic']}' (agent_findings={'yes' if agent_findings else 'no'})")

    try:
        start = time.time()
        report = execute_pro_research(context, plan, agent_findings=agent_findings)
        elapsed = time.time() - start

        report['elapsed_seconds'] = round(elapsed, 1)
        report['from_cache'] = False

        if report.get('error'):
            return jsonify(report), 500

        # Cache & store in DB
        cache.put(context['topic'], report)
        if db_available:
            try:
                save_session(
                    session_id=report.get('session_id', ''),
                    topic=context['topic'],
                    report=report,
                    mode='pro',
                    config=context,
                )
            except Exception as e:
                logger.warning(f"DB save failed: {e}")

        logger.info(f"Pro research complete: '{context['topic']}' in {elapsed:.1f}s")
        return jsonify(report)

    except Exception as e:
        logger.error(f"Pro research failed: {e}", exc_info=True)
        return jsonify({"error": f"Pro research failed: {str(e)}"}), 500


@app.route('/api/history/db', methods=['GET'])
def get_db_history():
    """Return research history from the database."""
    if not db_available:
        return jsonify({"history": cache.get_history(limit=10)})

    try:
        history = db_get_history(limit=20)
        return jsonify({"history": history})
    except Exception as e:
        logger.error(f"DB history failed: {e}")
        return jsonify({"history": cache.get_history(limit=10)})


# ──────────────────────────────────────────────
# BROWSER AGENT ENDPOINTS
# ──────────────────────────────────────────────

@app.route('/api/agent/start', methods=['POST'])
def agent_start():
    """
    Start a browser agent session.

    Request: {"topic": "...", "search_queries": ["..."]}
    Returns: {"session_id": "...", "status": "started"}
    """
    if not agent_available:
        return jsonify({"error": "Browser agent not available"}), 503

    data = request.get_json()
    if not data or not data.get('topic', '').strip():
        return jsonify({"error": "Missing topic"}), 400

    topic = data['topic'].strip()
    search_queries = data.get('search_queries', [f"{topic} research"])

    try:
        session_id = start_agent(topic, search_queries)
        return jsonify({
            "session_id": session_id,
            "status": "started",
            "message": f"Browser agent started for '{topic}'",
        })
    except Exception as e:
        logger.error(f"Agent start failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/agent/stream/<session_id>', methods=['GET'])
def agent_stream(session_id):
    """
    SSE stream of browser agent progress events.

    Returns: Server-Sent Events stream with real-time agent steps.
    """
    if not agent_available:
        return jsonify({"error": "Browser agent not available"}), 503

    return Response(
        get_event_stream(session_id),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@app.route('/api/agent/result/<session_id>', methods=['GET'])
def agent_result(session_id):
    """
    Get the final result of a completed agent session.

    Returns: {"result": {...}} or {"status": "pending"}
    """
    if not agent_available:
        return jsonify({"error": "Browser agent not available"}), 503

    result = get_agent_result(session_id)
    if result is None:
        return jsonify({"status": "pending", "message": "Agent still running"})

    return jsonify({"status": "complete", "result": result})


@app.route('/api/agent/screenshot/<session_id>', methods=['GET'])
def agent_screenshot(session_id):
    """
    Poll endpoint for the Virtual Browser UI.
    Currently returns a graceful empty response as live screenshots
    are not exported by the async browser-use thread yet.
    """
    if not agent_available:
        return jsonify({"error": "Browser agent not available"}), 503

    # Returns null image so frontend ignores it without throwing 404s
    return jsonify({
        "image": None,
        "url": "Agent is browsing..."
    })


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    logger.info(f"Starting PaperPilot API on port {port}")
    logger.info(f"GROQ_API_KEY: {'configured' if os.getenv('GROQ_API_KEY') else 'MISSING'}")
    logger.info(f"TAVILY_API_KEY: {'configured' if os.getenv('TAVILY_API_KEY') else 'MISSING'}")

    print(f"""
+--------------------------------------------+
|   PaperPilot API Server                    |
|                                            |
|   Frontend:  http://localhost:{port}          |
|   API:       http://localhost:{port}/api      |
|   Health:    http://localhost:{port}/api/health|
|                                            |
|   Keys: GROQ={'OK' if os.getenv('GROQ_API_KEY') else 'NO'}  TAVILY={'OK' if os.getenv('TAVILY_API_KEY') else 'NO'}           |
|   Cache: {CACHE_MAX_SIZE} entries, {CACHE_TTL_SECONDS//3600}h TTL             |
|   Rate:  {RATE_LIMIT_MAX} req/{RATE_LIMIT_WINDOW}s per IP              |
+--------------------------------------------+
    """)

    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
