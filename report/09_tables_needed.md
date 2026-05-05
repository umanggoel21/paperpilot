# File 9: Tables Needed for Project Report
# Source: All data extracted directly from PaperPilot codebase.

---

## 9.1 All Tables Summary

| Table No. | Caption | Chapter | Data Source in Code |
|---|---|---|---|
| Table 3.1 | Project Folder and File Structure | 3 | Directory listing + file docstrings |
| Table 3.2 | Key System Constants and Configuration | 3 | `api_server.py` lines 110-217 |
| Table 4.1 | Research Mode Comparison | 4 | `paper_fetch.py`, `deep_research.py`, `pro_research.py` |
| Table 5.1 | Tavily API — Academic Search Domains | 5 | `paper_fetch.py` lines 47-62 |
| Table 5.2 | Deep Research Configuration Tiers | 5 | `deep_research.py` lines 35-53 |
| Table 6.1 | Groq API Parameters and Rationale | 6 | All service files |
| Table 6.2 | Evidence Scoring: Hybrid Algorithm Parameters | 6 | `rag_service.py` lines 126-184 |
| Table 7.1 | Stealth Scraper: Priority Domains | 7 | `scraper_service.py` lines 31-40 |
| Table 7.2 | Bot Detection Indicators | 7 | `scraper_service.py` lines 91-99 |
| Table 8.1 | PDF Typography Styles | 8 | `pdf_generator.py` lines 119-288 |
| Table 9.1 | Internal API Endpoints | 9 | `api_server.py` all `@app.route` decorators |
| Table 9.2 | Database Schema: `research_sessions` | 9 | `database.py` lines 29-43 |
| Table 10.1 | External Package Dependencies | App | `requirements.txt` (14 lines) |
| Table 10.2 | Design Patterns Used | 3 | `api_server.py`, `scraper_service.py`, `browser_agent.py`, `rag_service.py` |

---

## 9.2 Each Table — Full Content

### Table 3.1 — Project Folder and File Structure

| File / Folder | Type | Lines | Responsibility |
|---|---|---|---|
| `api_server.py` | Python | 994 | Controller: Flask REST API, rate limiting, cache, SSE streaming |
| `paper_fetch.py` | Python | 608 | Service: Lite research pipeline |
| `pro_research.py` | Python | 468 | Service: Pro research wizard pipeline |
| `deep_research.py` | Python | 438 | Service: Deep conversational research pipeline |
| `pdf_generator.py` | Python | 870 | Service: Academic PDF generation via ReportLab |
| `rag_service.py` | Python | 209 | Service: Fuzzy text evidence verification |
| `browser_agent.py` | Python | 335 | Service: Live browser automation via Playwright |
| `scraper_service.py` | Python | 281 | Service: Stealth web content extraction |
| `database.py` | Python | 116 | Model: SQLite + SQLAlchemy ORM |
| `rag_service_full.py` | Python | ~250 | Service (paused): ChromaDB vector RAG version |
| `test_evidence.py` | Python | ~80 | Test: Evidence verification unit tests |
| `frontend/index.html` | HTML | N/A | View: Main SPA — search, modals, results |
| `frontend/editor.html` | HTML | N/A | View: Pro document editor page |
| `frontend/main.js` | JavaScript | N/A | Controller: index.html behavior |
| `frontend/editor.js` | JavaScript | 556 | Controller: editor.html behavior |
| `frontend/style.css` | CSS | N/A | Styles for index.html |
| `frontend/editor.css` | CSS | N/A | Styles for editor.html |
| `requirements.txt` | Config | 14 | Python dependency list |
| `.env` | Config | 2 | API keys (GROQ_API_KEY, TAVILY_API_KEY) |
| `paperpilot.db` | SQLite | N/A | Runtime database (auto-created) |
| `output/` | Directory | N/A | Generated PDF files storage |

---

### Table 3.2 — Key System Constants and Configuration

| Constant | Value | File | Purpose |
|---|---|---|---|
| `CACHE_MAX_SIZE` | 50 | `api_server.py` L110 | Maximum LRU cache entries |
| `CACHE_TTL_SECONDS` | 86400 (24 hours) | `api_server.py` L111 | Cache entry expiry time |
| `RATE_LIMIT_WINDOW` | 60 seconds | `api_server.py` L188 | Rate limit measurement window |
| `RATE_LIMIT_MAX` | 5 requests | `api_server.py` L189 | Max requests per IP per window |
| `MAX_TOPIC_LENGTH` | 200 characters | `api_server.py` L216 | Topic input validation upper bound |
| `MIN_TOPIC_LENGTH` | 3 characters | `api_server.py` L217 | Topic input validation lower bound |
| `DEEP_RESEARCH_MONTHLY_LIMIT` | 3 uses | `api_server.py` L434 | Monthly cap per IP for Deep mode |
| `GROQ_MODEL` (research) | `llama-3.3-70b-versatile` | All service files | LLM model for synthesis |
| `GROQ_MODEL` (agent) | `llama-4-scout-17b-16e-instruct` | `browser_agent.py` L143 | LLM model for browser agent |

---

### Table 4.1 — Research Mode Comparison

| Feature | Lite Mode | Deep Mode | Pro Mode |
|---|---|---|---|
| **Entry file** | `paper_fetch.py` | `deep_research.py` | `pro_research.py` |
| **API endpoint** | `POST /api/research` | `POST /api/deep/execute` | `POST /api/pro/execute` |
| **User configuration** | Topic only | 3-question conversational Q&A | 6-question intake form |
| **AI planning step** | None | Yes (section-by-section plan) | Yes (wizard plan) |
| **Browser agent** | No | No | Optional (user-triggered) |
| **Tavily searches** | 3 (Academic, Wiki, Articles) | Per-section × 3 | Per-section × 3 |
| **Groq calls** | 1 | 2 (plan + execute) | 2-3 (chips + plan + execute) |
| **Monthly limit** | 5/min rate limit | 3 per month | 5/min rate limit |
| **DB save** | Optional | After execution | Yes (explicit save) |
| **Report length** | Fixed | Configurable (short/medium/long) | Configurable |
| **Token limit** | Default | 2048 / 4096 / 6000 | Context-dependent |

---

### Table 5.1 — Tavily API Academic Search Domains

| # | Domain | Source Type |
|---|---|---|
| 1 | `arxiv.org` | Academic preprints |
| 2 | `pubmed.ncbi.nlm.nih.gov` | Biomedical research |
| 3 | `researchgate.net` | Research papers |
| 4 | `ieee.org` | Engineering/CS papers |
| 5 | `sciencedirect.com` | Elsevier journals |
| 6 | `semanticscholar.org` | AI-indexed papers |
| 7 | `scholar.google.com` | Academic search |
| 8 | `ncbi.nlm.nih.gov` | Biomedical database |
| 9 | `nature.com` | Nature journals |
| 10 | `springer.com` | Springer publications |
| 11 | `en.wikipedia.org` | Wikipedia (separate search) |

---

### Table 5.2 — Deep Research Configuration Tiers

| Config: sources | Papers | Wiki | Articles | Total |
|---|---|---|---|---|
| 3 | 2 | 1 | 2 | 5 |
| 5 | 3 | 1 | 3 | 7 |
| 7 | 4 | 2 | 4 | 10 |

| Config: length | Max Tokens | Extract Limit per Source |
|---|---|---|
| `short` | 2048 | 800 chars |
| `medium` | 4096 | 1500 chars |
| `long` | 6000 | 2500 chars |

---

### Table 6.1 — Groq API Parameters and Rationale

| Parameter | Value | Used In | Rationale |
|---|---|---|---|
| `model` | `llama-3.3-70b-versatile` | All synthesis | Best available free-tier model for JSON generation |
| `model` (agent) | `llama-4-scout-17b-16e-instruct` | `browser_agent.py` | browser-use library's native Groq wrapper |
| `temperature` (synthesis) | 0.4 | `_groq_call()` default | Balanced creativity vs. factual accuracy |
| `temperature` (PDF enhance) | 0.3 | `pdf_generator.py` | Lower for more formal/consistent academic rewriting |
| `temperature` (agent) | 0.1 | `browser_agent.py` | Near-deterministic for reliable web navigation |
| `response_format` | `{"type": "json_object"}` | All synthesis calls | Enforce structured JSON output |
| `max_tokens` (short) | 2048 | `deep_research.py` | Concise report generation |
| `max_tokens` (medium) | 4096 | `deep_research.py` | Standard report generation |
| `max_tokens` (long) | 6000 | `deep_research.py` | Comprehensive report generation |
| `max_tokens` (PDF enhance) | 4096 | `pdf_generator.py` | Sufficient for multi-section rewrite |
| `retries` | 3 | `_groq_call()` | Handle transient rate limits |
| Backoff formula | `(2^attempt) x 5` | `_groq_call()` | Exponential: 5s, 10s, 20s |

---

### Table 6.2 — Evidence Scoring: Hybrid Algorithm Parameters

| Parameter | Value | Source | Role |
|---|---|---|---|
| SequenceMatcher weight | 0.4 (40%) | `rag_service.py` L169 | Character sequence similarity |
| Keyword overlap weight | 0.6 (60%) | `rag_service.py` L169 | Semantic keyword matching |
| Minimum threshold | 25% | `rag_service.py` L184 | Filter noise/irrelevant matches |
| Results returned | top_k = 3 | `query_evidence()` parameter | Top 3 matches shown to user |
| Chunk size | 3 sentences | `_chunk_text()` L45 | Semantic unit of evidence |
| Min sentence length | 20 chars | `_chunk_text()` L55 | Filter sentence fragments |
| Min chunk length | 40 chars | `_chunk_text()` L64 | Filter trivial chunks |
| Stop words excluded | 25 words | `query_evidence()` L141-145 | Improve keyword relevance |

---

### Table 7.1 — Stealth Scraper: Priority Domains (Skip Standard, Use Stealth First)

| # | Domain | Reason |
|---|---|---|
| 1 | `researchgate.net` | Requires login / blocks bots aggressively |
| 2 | `sciencedirect.com` | Elsevier paywall + bot detection |
| 3 | `ieee.org` | IEEE digital library bot protection |
| 4 | `springer.com` | Springer paywall |
| 5 | `nature.com` | Nature paywall |
| 6 | `wiley.com` | Wiley paywall |
| 7 | `tandfonline.com` | Taylor & Francis paywall |
| 8 | `sagepub.com` | SAGE paywall |

---

### Table 7.2 — Bot Detection Indicators Checked

| # | Pattern Checked | Type |
|---|---|---|
| 1 | `"cf-browser-verification"` | Cloudflare challenge |
| 2 | `"challenge-platform"` | Cloudflare challenge |
| 3 | `"captcha"` | Generic CAPTCHA |
| 4 | `"recaptcha"` | Google reCAPTCHA |
| 5 | `"hCaptcha"` | hCaptcha |
| 6 | `"cf-turnstile"` | Cloudflare Turnstile |
| 7 | `"Access Denied"` | Generic block |
| 8 | `"bot detection"` | Generic detection message |

---

### Table 8.1 — PDF Typography Styles Configuration

| Style Name | Font | Size | Leading | Alignment | Special |
|---|---|---|---|---|---|
| `title` | TimesNR-Bold | 16pt | 22pt | CENTER | Title page |
| `subtitle` | TimesNR | 12pt | 16pt | CENTER | Date/meta |
| `section_heading` | TimesNR-Bold | 14pt | 20pt | LEFT | `spaceBefore=18` |
| `sub_heading` | TimesNR-Bold | 12pt | 18pt | LEFT | `spaceBefore=12` |
| `body` | TimesNR | 12pt | 18pt | JUSTIFY | Main text, 1.5× spacing |
| `body_indent` | TimesNR | 12pt | 18pt | JUSTIFY | `firstLineIndent=24` |
| `bullet` | TimesNR | 12pt | 18pt | JUSTIFY | `leftIndent=24` |
| `reference` | TimesNR | 11pt | 15pt | JUSTIFY | Hanging indent `-24` |
| `header` | TimesNR | 10pt | 12pt | LEFT | Page header (page > 1) |
| `footer` | TimesNR | 10pt | 12pt | CENTER | Page numbers |
| `abstract_body` | TimesNR-Italic | 12pt | 18pt | JUSTIFY | `leftIndent=18, rightIndent=18` |
| `toc_entry` | TimesNR | 12pt | 18pt | LEFT | `leftIndent=12` |
| `toc_sub_entry` | TimesNR | 12pt | 18pt | LEFT | `leftIndent=36` |
| `table_header` | TimesNR-Bold | 11pt | 14pt | CENTER | White text |
| `table_cell` | TimesNR | 11pt | 14pt | LEFT | Body table data |

---

### Table 9.1 — Internal API Endpoints

| Method | Endpoint | Request Body | Response |
|---|---|---|---|
| GET | `/` | None | `index.html` |
| GET | `/editor` | None | `editor.html` |
| GET | `/api/health` | None | Status + feature flags + cache stats |
| POST | `/api/research` | `{topic}` | Full research JSON report |
| POST | `/api/pdf` | `{report, enhance}` | `{pdf_url, filename, pdf_base64, size_bytes}` |
| GET | `/api/pdf/download/<filename>` | None | PDF binary file |
| GET | `/api/history` | None | `{history: [...]}` |
| POST | `/api/deep/questions` | `{topic, config}` | `{questions, remaining_uses}` |
| POST | `/api/deep/plan` | `{topic, config, answers}` | `{plan, research_focus, estimated_time}` |
| POST | `/api/deep/execute` | `{topic, config, answers, plan}` | Full research JSON report |
| POST | `/api/research/enhanced` | `{topic}` | Report + `extraction_log` + `rag_stats` + `session_id` |
| POST | `/api/evidence` | `{sentence, session_id}` | `{evidence: [...top 3 matches...]}` |
| POST | `/api/pro/chips` | `{topic}` | `{chips: [...6 subtopics...]}` |
| POST | `/api/pro/intake` | `{topic, answers}` | Structured context dict |
| POST | `/api/pro/plan` | `{context}` | `{plan, estimated_time}` |
| POST | `/api/pro/execute` | `{context, plan, agent_findings?}` | Full research JSON report |
| POST | `/api/agent/start` | `{topic, queries}` | `{session_id}` |
| GET | `/api/agent/stream/<session_id>` | None | SSE stream (`text/event-stream`) |

---

### Table 9.2 — Database Schema: `research_sessions`

| Field Name | SQLAlchemy Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PRIMARY KEY, AUTOINCREMENT | Auto-generated row identifier |
| `session_id` | String(32) | UNIQUE, NOT NULL, INDEX | 16-char SHA256 of normalized topic |
| `topic` | String(300) | NOT NULL | Research topic |
| `mode` | String(10) | DEFAULT 'lite' | 'lite' or 'pro' |
| `config_json` | Text | DEFAULT '{}' | JSON string: Pro intake form preferences |
| `report_json` | Text | NULLABLE | JSON string: full research report |
| `total_sources` | Integer | DEFAULT 0 | Source count extracted from report |
| `elapsed_seconds` | Float | DEFAULT 0 | Execution time in seconds |
| `created_at` | DateTime | DEFAULT UTC_NOW | Row creation timestamp |

---

### Table 10.1 — External Package Dependencies

| # | Package | Version (requirements.txt) | Purpose |
|---|---|---|---|
| 1 | `tavily-python` | Latest | Web search + content extraction API |
| 2 | `groq` | Latest | Groq LLM API client (LLaMA-3.3) |
| 3 | `python-dotenv` | Latest | Load `.env` API keys |
| 4 | `rich` | Latest | CLI UI: spinners, panels, progress bars |
| 5 | `reportlab` | Latest | Academic PDF document generation |
| 6 | `flask` | Latest | Web framework + REST API |
| 7 | `flask-cors` | Latest | Enable CORS headers |
| 8 | `flask-sqlalchemy` | Latest | SQLAlchemy ORM for Flask |
| 9 | `chromadb` | Latest | Vector DB (listed; active RAG uses difflib) |
| 10 | `sentence-transformers` | Latest | Local embeddings (listed; not used in active code) |
| 11 | `beautifulsoup4` | Latest | HTML-to-text parsing in `scraper_service.py` |
| 12 | `browser-use` | Latest | Browser automation agent framework |
| 13 | `langchain-groq` | Latest | LangChain Groq integration (for browser-use) |
| 14 | `playwright` | Latest | Headless browser engine for `browser_agent.py` |

---

### Table 10.2 — Design Patterns Used

| Pattern | Found In | Evidence | Purpose |
|---|---|---|---|
| MVC | Entire project | `database.py` (Model), `frontend/` (View), `api_server.py` (Controller) | Separation of concerns |
| LRU Cache | `api_server.py` L113-179 | `ResultCache` using `OrderedDict` + `move_to_end()` | Avoid redundant API calls |
| Strategy | `scraper_service.py` L221-268 | `_standard_extract()` then `_stealth_extract()` fallback | Adaptive extraction method selection |
| Observer/Event Queue | `browser_agent.py` L41-66 | `queue.Queue` per session, `push_event()` producer, `get_event_stream()` consumer | Real-time SSE streaming |
| Closure/Factory | `browser_agent.py` L80-120 | `_make_step_callback(session_id)` returns function | Per-session step callbacks |
| Template Method | `pdf_generator.py` L468 | `build_pdf_content()` fixed sequence: Title→Abstract→TOC→Sections→References | Consistent PDF structure |
| Retry + Exponential Backoff | `pro_research.py` L47-71 | `_groq_call()` with `(2^attempt) x 5` wait | Groq API rate limit resilience |
