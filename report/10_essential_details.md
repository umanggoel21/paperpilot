# File 10: Essential Project Details for Report Writing
# Source: Extracted directly from PaperPilot codebase — no assumptions made.

---

## 10.1 Unique Selling Points (Verified from Code)

| USP | Evidence in Code |
|---|---|
| **Three distinct research modes** (Lite/Deep/Pro) with increasing depth | 3 separate pipeline files: `paper_fetch.py`, `deep_research.py`, `pro_research.py` |
| **Hybrid fuzzy evidence matching** without any vector database | `rag_service.py`: `SequenceMatcher (40%) + keyword overlap (60%)`, pure Python `difflib` |
| **Live browser automation** with real-time SSE terminal stream | `browser_agent.py`: Playwright + `browser-use`, `queue.Queue` SSE events |
| **Dual-layer stealth extraction** for bot-protected academic sites | `scraper_service.py`: Standard HTTP → Scrapling fallback, 8 bot-detection checks |
| **Groq LLM-enhanced academic PDF** with formal rewriting | `pdf_generator.py`: `enhance_content_academic()` call, 14 ReportLab style definitions |
| **Monthly rate-capped deep research** to prevent API cost overrun | `api_server.py` L434: `DEEP_RESEARCH_MONTHLY_LIMIT = 3` |
| **Zero-dependency evidence verification** (pure Python stdlib) | `rag_service.py` line 3: *"Zero external dependencies"*, imports only `difflib`, `re` |
| **In-memory LRU cache with SHA256 keying** | `api_server.py` `ResultCache`: `OrderedDict`, SHA256 first 16 chars, 24h TTL |

---

## 10.2 All Exact Numbers to Use in Report

| Value | What it Represents | Found In |
|---|---|---|
| `50` | Max LRU cache entries | `api_server.py` L110: `CACHE_MAX_SIZE = 50` |
| `86400` | Cache TTL in seconds (24 hours) | `api_server.py` L111: `CACHE_TTL_SECONDS` |
| `60` | Rate limit window (seconds) | `api_server.py` L188: `RATE_LIMIT_WINDOW` |
| `5` | Max requests per rate limit window | `api_server.py` L189: `RATE_LIMIT_MAX` |
| `3` | Monthly Deep Research cap per IP | `api_server.py` L434: `DEEP_RESEARCH_MONTHLY_LIMIT` |
| `200` | Max topic input characters | `api_server.py` L216: `MAX_TOPIC_LENGTH` |
| `3` | Min topic input characters | `api_server.py` L217: `MIN_TOPIC_LENGTH` |
| `16` | Length of SHA256-derived session ID | `api_server.py` L125: `.hexdigest()[:16]` |
| `0.40` | SequenceMatcher weight in evidence scoring | `rag_service.py` L169 |
| `0.60` | Keyword overlap weight in evidence scoring | `rag_service.py` L169 |
| `25%` | Minimum similarity threshold for evidence | `rag_service.py` L184: `>= 25` |
| `3` | Evidence top_k results returned | `rag_service.py`: `top_k=3` default |
| `3` | Sentences per text chunk | `rag_service.py` L45: `chunk_size=3` |
| `20` | Min sentence length (chars) | `rag_service.py` L55: `>= 20` |
| `40` | Min chunk length (chars) | `rag_service.py` L64: `< 40` skip |
| `50` | Min source content length (chars) | `rag_service.py` L90: `< 50` skip |
| `200` | Min scraped content length (chars) | `scraper_service.py` L112, L156 |
| `15` | Max browser agent steps | `browser_agent.py` L188: `max_steps=15` |
| `120` | SSE stream max timeout (seconds) | `browser_agent.py` L312: `max_timeout=120` |
| `0.1` | Browser agent LLM temperature | `browser_agent.py` L145 |
| `0.3` | PDF enhancement LLM temperature | `pdf_generator.py` L373 |
| `0.4` | Research synthesis LLM temperature | `_groq_call()` default in `pro_research.py` L47 |
| `3` | Groq retry attempts | `_groq_call()` parameter `retries=3` |
| `5, 10, 20` | Exponential backoff wait times (seconds) | `(2^attempt) * 5` |
| `2048` | Max tokens — short report | `deep_research.py` L43: `TOKEN_LIMITS["short"]` |
| `4096` | Max tokens — medium report / PDF enhance | `deep_research.py` L44, `pdf_generator.py` L379 |
| `6000` | Max tokens — long report | `deep_research.py` L45: `TOKEN_LIMITS["long"]` |
| `800` | Chars extracted per source — short | `deep_research.py` L50: `EXTRACT_LIMITS["short"]` |
| `1500` | Chars extracted per source — medium | `deep_research.py` L51: `EXTRACT_LIMITS["medium"]` |
| `2500` | Chars extracted per source — long | `deep_research.py` L52: `EXTRACT_LIMITS["long"]` |
| `1 inch` | PDF page margins (all sides) | `pdf_generator.py` L75: `MARGIN = 1 * inch` |
| `12pt` | PDF body text size | `pdf_generator.py` L174 (body style) |
| `14pt` | PDF section heading size | `pdf_generator.py` L154 (section_heading) |
| `16pt` | PDF title size | `pdf_generator.py` L139 (title style) |
| `18pt` | PDF line spacing (1.5x of 12pt) | `pdf_generator.py` L133: `LINE_SPACING = 18` |
| `30000` | Editor auto-save interval (ms = 30s) | `editor.js` ~L77 |
| `150` | Markdown preview debounce (ms) | `editor.js` ~L52 |
| `10` | History items returned by `/api/history` | `api_server.py` L424: `cache.get_history(limit=10)` |
| `20` | History items returned by `database.get_history()` | `database.py` L107: `limit=20` |
| `12` | Browser agent session ID length (chars) | `browser_agent.py` L281: `uuid.uuid4().hex[:12]` |
| `15` | HTTP request timeout (seconds) | `scraper_service.py` L67: `timeout=15` |
| `10` | Tavily API domains in academic filter | `paper_fetch.py` L47-58: 10 domains listed |
| `8` | Stealth-priority domains | `scraper_service.py` L31-40: 8 domains |
| `4` | Document templates in editor | `editor.js` TEMPLATES object: ieee, apa, litreview, executive |
| `17` | Total internal API endpoints | Counted from `@app.route` decorators |
| `1` | Number of database tables | Only `research_sessions` |
| `14` | External Python packages | `requirements.txt` line count |
| `2` | UI pages/screens | `index.html` + `editor.html` |

---

## 10.3 All Class Names (Exact Spelling)

| Class Name | File | Purpose |
|---|---|---|
| `ResultCache` | `api_server.py` L113 | In-memory LRU cache for research results |
| `HeaderFooter` | `pdf_generator.py` L415 | ReportLab canvas callback for page headers/footers |
| `ResearchSession` | `database.py` L25 | SQLAlchemy ORM model for `research_sessions` table |
| `RAGService` | `rag_service.py` L29 | Fuzzy text evidence matching service |
| `StealthScraper` | `scraper_service.py` L43 | Dual-mode web content extractor |

---

## 10.4 All Key Functions to Mention in Report

| Function | File | Chapter to Mention |
|---|---|---|
| `fetch_research(topic)` | `paper_fetch.py` | Ch. 5 — Lite Pipeline |
| `search_sources(topic, tavily)` | `paper_fetch.py` | Ch. 5 — Lite Pipeline |
| `extract_content(results, tavily)` | `paper_fetch.py` | Ch. 5 — Lite Pipeline |
| `generate_questions(topic, config)` | `deep_research.py` | Ch. 5 — Deep Pipeline |
| `generate_plan(topic, config, answers)` | `deep_research.py` | Ch. 5 — Deep Pipeline |
| `execute_deep_research(topic, config, answers, plan)` | `deep_research.py` | Ch. 5 — Deep Pipeline |
| `generate_intake_chips(topic)` | `pro_research.py` | Ch. 5 — Pro Pipeline |
| `process_intake(topic, answers)` | `pro_research.py` | Ch. 5 — Pro Pipeline |
| `generate_pro_plan(context)` | `pro_research.py` | Ch. 5 — Pro Pipeline |
| `execute_pro_research(context, plan, agent_findings)` | `pro_research.py` | Ch. 5 — Pro Pipeline |
| `_groq_call(client, messages, ...)` | `pro_research.py`, `deep_research.py` | Ch. 6 — LLM Integration |
| `RAGService.index_sources(sources, session_id)` | `rag_service.py` | Ch. 6 — Evidence |
| `RAGService.query_evidence(sentence, session_id)` | `rag_service.py` | Ch. 6 — Evidence |
| `RAGService._chunk_text(text, ...)` | `rag_service.py` | Ch. 6 — Evidence |
| `start_agent(topic, search_queries)` | `browser_agent.py` | Ch. 7 — Browser Agent |
| `get_event_stream(session_id)` | `browser_agent.py` | Ch. 7 — Browser Agent |
| `_run_agent_async(session_id, topic, queries)` | `browser_agent.py` | Ch. 7 — Browser Agent |
| `generate_pdf(report_input, output_path, enhance)` | `pdf_generator.py` | Ch. 8 — PDF |
| `enhance_content_academic(report)` | `pdf_generator.py` | Ch. 8 — PDF |
| `build_pdf_content(report, styles, font_family)` | `pdf_generator.py` | Ch. 8 — PDF |
| `build_styles(font_family)` | `pdf_generator.py` | Ch. 8 — PDF |
| `register_fonts()` | `pdf_generator.py` | Ch. 8 — PDF |
| `ResultCache.get(topic)` | `api_server.py` | Ch. 3 — Architecture |
| `ResultCache.put(topic, report)` | `api_server.py` | Ch. 3 — Architecture |
| `ResultCache._key(topic)` | `api_server.py` | Ch. 3 — Architecture |
| `check_rate_limit()` | `api_server.py` | Ch. 3 — Architecture |
| `validate_topic(topic)` | `api_server.py` | Ch. 3 — Architecture |
| `init_db(app)` | `database.py` | Ch. 3 — Architecture |
| `save_session(...)` | `database.py` | Ch. 3 — Architecture |
| `StealthScraper.extract(url)` | `scraper_service.py` | Ch. 7 — Browser/Scraper |
| `renderPreview()` | `editor.js` | Ch. 4 — Editor Screen |
| `reportToMarkdown(report)` | `editor.js` | Ch. 4 — Editor Screen |
| `loadReportIntoEditor()` | `editor.js` | Ch. 4 — Editor Screen |

---

## 10.5 Code Extracts Ready for Report

### Code Extract 5.1: Hybrid Evidence Scoring Formula
```python
# rag_service.py — query_evidence() lines 153-169
# Method 1: SequenceMatcher (finds common character sequences)
seq_score = SequenceMatcher(
    None, sentence_lower, chunk["text_lower"]
).ratio()

# Method 2: Keyword overlap (how many important words match)
if query_words:
    overlap = len(query_words & chunk_words) / len(query_words)
else:
    overlap = 0

# Hybrid score: 40% sequence matching + 60% keyword overlap
combined = (seq_score * 0.4) + (overlap * 0.6)
similarity = round(combined * 100, 1)
```
**Mention in:** Chapter 6, Section 6.X — Evidence Verification
**Explain as:** Combines character-level sequence matching (difflib) with semantic keyword overlap for accurate source attribution without requiring vector embeddings.

---

### Code Extract 5.2: LRU Cache Key Generation
```python
# api_server.py — ResultCache._key() lines 123-125
def _key(self, topic):
    normalized = topic.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
```
**Mention in:** Chapter 3, Section 3.X — Application Layer / Cache Design
**Explain as:** Generates a deterministic 16-character cache key from any topic string using SHA256 hashing, ensuring case-insensitive deduplication.

---

### Code Extract 5.3: Exponential Backoff Retry
```python
# pro_research.py — _groq_call() lines 63-70
except Exception as e:
    error_str = str(e).lower()
    if "rate_limit" in error_str or "429" in error_str:
        wait = (2 ** attempt) * 5
        logger.warning(f"Groq rate limit hit, waiting {wait}s
                        (attempt {attempt+1}/{retries})")
        time.sleep(wait)
    else:
        raise
```
**Mention in:** Chapter 6, Section 6.X — LLM Integration
**Explain as:** Implements resilient Groq API integration with exponential backoff (5s, 10s, 20s) triggered specifically on rate limit errors (HTTP 429), ensuring uninterrupted research execution.

---

### Code Extract 5.4: Browser Agent SSE Keepalive
```python
# browser_agent.py — get_event_stream() lines 314-331
while timeout_counter < max_timeout:  # 120 iterations
    try:
        event = q.get(timeout=1)
        timeout_counter = 0  # Reset on event
        yield f"event: {event_type}\ndata: {data_str}\n\n"
        if event_type in ('done',):
            break
    except queue.Empty:
        timeout_counter += 1
        yield f": keepalive\n\n"  # Prevent SSE connection drop
```
**Mention in:** Chapter 7, Section 7.X — Browser Agent Streaming
**Explain as:** Implements a producer-consumer pattern where the Flask endpoint yields SSE events from a thread-safe queue, with keepalive pings every second to prevent connection timeout.

---

### Code Extract 5.5: Stealth Extraction Decision
```python
# scraper_service.py — extract() lines 239-247
if self._should_try_stealth_first(url):
    logger.info(f"Known stealth-priority domain: {url}")
    text = self._stealth_extract(url)
    if text:
        result["text"] = text
        result["method_used"] = "stealth"
        result["success"] = True
        return result
```
**Mention in:** Chapter 7, Section 7.X — Stealth Scraper
**Explain as:** Implements a domain-aware strategy pattern that skips standard HTTP extraction for known bot-protected academic sites (ResearchGate, IEEE, Springer, etc.) and immediately invokes the Scrapling stealth browser.

---

### Code Extract 5.6: PDF Font Registration with Fallback
```python
# pdf_generator.py — register_fonts() lines 93-112
times_paths = [
    r"C:\Windows\Fonts\times.ttf",
    r"C:\Windows\Fonts\timesbd.ttf",
]
if all(os.path.exists(p) for p in times_paths):
    pdfmetrics.registerFont(TTFont("TimesNR", times_paths[0]))
    return "TimesNR"
else:
    return "Times-Roman"  # ReportLab built-in fallback
```
**Mention in:** Chapter 8, Section 8.X — PDF Generation
**Explain as:** Implements graceful font degradation — attempts to register system Times New Roman for authentic academic formatting, falling back to ReportLab's built-in Times-Roman on non-Windows systems.

---

## 10.6 Abbreviations List (Complete — from Codebase)

| Abbreviation | Full Form |
|---|---|
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| CORS | Cross-Origin Resource Sharing |
| CSS | Cascading Style Sheets |
| DOM | Document Object Model |
| DFD | Data Flow Diagram |
| ERD | Entity-Relationship Diagram |
| HTML | HyperText Markup Language |
| HTTP | HyperText Transfer Protocol |
| JSON | JavaScript Object Notation |
| JS | JavaScript |
| LLM | Large Language Model |
| LRU | Least Recently Used |
| MVC | Model-View-Controller |
| NLP | Natural Language Processing |
| ORM | Object Relational Mapper |
| PDF | Portable Document Format |
| RAG | Retrieval-Augmented Generation |
| REST | Representational State Transfer |
| SHA256 | Secure Hash Algorithm 256-bit |
| SPA | Single Page Application |
| SQL | Structured Query Language |
| SQLite | Self-Contained SQL Database Engine |
| SSE | Server-Sent Events |
| TTL | Time-To-Live |
| UI | User Interface |
| UML | Unified Modelling Language |
| URL | Uniform Resource Locator |
| UX | User Experience |
| UUID | Universally Unique Identifier |
| XML | Extensible Markup Language |

---

## 10.7 IEEE-Format References Suggested

Based on technologies detected in the codebase:

```
[1]  M. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,"
     in Proc. NeurIPS, 2020.

[2]  A. Dubey et al., "The Llama 3 Herd of Models," Meta AI, arXiv:2407.21783, Jul. 2024.

[3]  A. Ratner et al., "Snorkel: Rapid Training Data Creation with Weak Supervision,"
     VLDB J., vol. 29, pp. 709–730, 2020.

[4]  Tavily AI, "Tavily Search API Documentation," 2024. [Online].
     Available: https://docs.tavily.com

[5]  Groq Inc., "Groq Developer API Documentation," 2024. [Online].
     Available: https://console.groq.com/docs

[6]  Flask Community, "Flask Documentation (v3.0)," Pallets Project, 2024. [Online].
     Available: https://flask.palletsprojects.com

[7]  ReportLab Inc., "ReportLab PDF Library User Guide," 2024. [Online].
     Available: https://www.reportlab.com/docs/reportlab-userguide.pdf

[8]  Python Software Foundation, "difflib — Helpers for computing deltas,"
     Python 3.x Documentation, 2024. [Online].
     Available: https://docs.python.org/3/library/difflib.html

[9]  Microsoft Playwright Team, "Playwright for Python Documentation," 2024. [Online].
     Available: https://playwright.dev/python/

[10] J. Devlin, M. Chang, K. Lee, and K. Toutanova, "BERT: Pre-training of Deep Bidirectional
     Transformers for Language Understanding," in Proc. NAACL HLT, Minneapolis, Jun. 2019.

[11] Y. Liu et al., "RoBERTa: A Robustly Optimized BERT Pretraining Approach,"
     arXiv:1907.11692, Jul. 2019.

[12] T. Brown et al., "Language Models are Few-Shot Learners (GPT-3)," 
     in Proc. NeurIPS, 2020.

[13] SQLite Consortium, "SQLite Documentation," 2024. [Online].
     Available: https://www.sqlite.org/docs.html

[14] SQLAlchemy Authors, "SQLAlchemy ORM Documentation," 2024. [Online].
     Available: https://docs.sqlalchemy.org

[15] V. Karpukhin et al., "Dense Passage Retrieval for Open-Domain Question Answering,"
     in Proc. EMNLP, 2020, pp. 6769–6781.
```

---

## 10.8 Chapter-by-Chapter Writing Guide

### Chapter 1 — Introduction
- **Background:** Talk about exponential growth of academic literature; time cost of manual literature review; need for AI-assisted synthesis
- **Problem:** Researchers/students spend days manually reviewing papers; no tool combines automated search + LLM synthesis + evidence verification + academic PDF output in one system
- **Objectives:** Extract from features: (1) Automate literature search across 10+ academic domains, (2) Synthesize using LLM, (3) Provide 3 research depth modes, (4) Enable evidence verification, (5) Generate academic PDF with proper formatting, (6) Support live browser-based academic navigation
- **Scope:** Web application; Python backend; requires GROQ_API_KEY and TAVILY_API_KEY; Windows-supported; Lite/Deep/Pro modes; PDF export

### Chapter 2 — Literature Review
- **Section 2.1:** Automated Information Retrieval (Tavily API, web scraping, academic domain targeting)
- **Section 2.2:** Large Language Models for Text Synthesis (LLaMA-3.3, GPT-3, instruction tuning)
- **Section 2.3:** Retrieval-Augmented Generation — compare vector-based RAG (ChromaDB, listed in requirements but not active) vs. fuzzy matching approach used in `rag_service.py`
- **Section 2.4:** Browser Automation for Research (Playwright, browser-use framework, Google Scholar scraping)
- **Section 2.5:** Academic PDF Generation Tools (ReportLab vs. LaTeX vs. word processors)

### Chapter 3 — Architecture
- **Pattern:** MVC — cite specific files
- **Layers:** 4 layers (Presentation, Application, Service, Data)
- **Key design decisions:** LRU cache to avoid API costs, SHA256 keying, in-memory rate limiting, SSE for real-time agent streaming
- **Folder structure:** Use Table 3.1 exactly

### Chapter 4 — Application Screens
- **Screen 1:** `index.html` — Search Hub (Sections: Hero, Pro Modal Steps 1-3, Results View)
- **Screen 2:** `editor.html` — Document Editor (Split-pane, 4 templates, auto-save, live preview)
- Use UI component tables from `07_ui_screens.md`

### Chapter 5 — Functional Modules
- **5.1 Lite Pipeline:** Use flowchart + `fetch_research()` explanation
- **5.2 Deep Pipeline:** 3-phase conversational, configuration tiers
- **5.3 Pro Pipeline:** 6-question wizard, browser agent integration
- **5.4 Evidence Verification:** Hybrid scoring formula, chunking, indexing

### Chapter 6 — LLM Integration and Synthesis Engine (Core Technical Chapter)
- Groq API parameter table (Table 6.1)
- Evidence scoring formula (Code Extract 5.1, Table 6.2)
- Sequence diagram (Figure 6.1)
- Exponential backoff code (Code Extract 5.3)

### Chapter 7 — Browser Automation and Stealth Extraction
- Browser agent: Playwright + browser-use, max_steps=15, SSE streaming
- SSE code extract (Code Extract 5.4)
- Stealth scraper: Standard → Stealth fallback, 8 detection patterns
- Stealth code extract (Code Extract 5.5)

### Chapter 8 — PDF Report Generation
- ReportLab pipeline (Figure 8.1)
- Academic enhancement via Groq (temperature=0.3, formal rewrite rules)
- Typography table (Table 8.1)
- Font registration code (Code Extract 5.6)

### Chapter 9 — Testing Strategy
- Unit tests found in `test_evidence.py`
- Test the `RAGService` evidence matching
- Integration testing: API endpoints via Postman/curl
- Error path: rate limiting returns 429, topic validation returns 400

### Chapter 10 — Conclusion
- **Limitations (honest from code):**
  - `session_id` SHA256 collision means same topic → overwrites existing session (acknowledged in architecture)
  - In-memory rate limiting and caches are NOT thread-safe for multi-worker production (Gunicorn)
  - `chromadb` + `sentence-transformers` listed in requirements but full ChromaDB RAG is in `rag_service_full.py` (not active)
  - Browser agent requires Playwright installation and internet connection
  - No authentication/user accounts
- **Future work:** UUID-based session IDs, Redis for cache/rate limiting, ChromaDB integration, user accounts, multi-language support
