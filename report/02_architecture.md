# File 2: System Architecture
# Source: Extracted directly from PaperPilot codebase — no assumptions made.

---

## 2.1 Architecture Pattern

- **Pattern Name:** MVC (Model-View-Controller)
- **Evidence from code:**
  - **Model** = `database.py` — `ResearchSession` SQLAlchemy model class (line 25)
  - **View** = `frontend/index.html`, `frontend/editor.html`, `frontend/main.js`, `frontend/editor.js`, `frontend/style.css`, `frontend/editor.css`
  - **Controller** = `api_server.py` — all Flask route handlers that orchestrate service calls
- **Service Layer** (between Controller and Model): `paper_fetch.py`, `pro_research.py`, `deep_research.py`, `rag_service.py`, `browser_agent.py`, `pdf_generator.py`, `scraper_service.py`
- **No justification comment found in code** — pattern inferred from structural separation.

---

## 2.2 Complete Folder Structure

```
d:\paperpilot\                         [Project Root]
│
├── api_server.py                      [Controller — Flask REST API + SSE]
├── paper_fetch.py                     [Service — Lite research pipeline]
├── pro_research.py                    [Service — Pro research wizard pipeline]
├── deep_research.py                   [Service — Deep conversational pipeline]
├── rag_service.py                     [Service — Evidence verification (fuzzy)]
├── rag_service_full.py                [Service — Evidence (ChromaDB version, paused)]
├── browser_agent.py                   [Service — Live browser automation via Playwright]
├── pdf_generator.py                   [Service — Academic PDF generator via ReportLab]
├── scraper_service.py                 [Service — Stealth web scraper fallback]
├── database.py                        [Model — SQLite + SQLAlchemy ORM]
├── test_evidence.py                   [Test — Evidence verification tests]
├── paperpilot.db                      [Data — SQLite database file (auto-created)]
├── requirements.txt                   [Config — Python dependencies (14 packages)]
├── .env                               [Config — API keys (GROQ_API_KEY, TAVILY_API_KEY)]
├── .gitignore                         [Config — Git ignore rules]
│
├── frontend\                          [View Layer]
│   ├── index.html                     [Main SPA page — search, modals, results]
│   ├── editor.html                    [Pro editor page — split-pane markdown editor]
│   ├── main.js                        [JS controller for index.html]
│   ├── editor.js                      [JS controller for editor.html]
│   ├── style.css                      [Styles for index.html]
│   └── editor.css                     [Styles for editor.html]
│
├── output\                            [Runtime — generated PDF files saved here]
│
├── report\                            [Documentation — project report files]
│
└── .agent\                            [Agent config — skills directory]
    └── skills\
        └── ui-ux-pro-max\
```

---

## 2.3 Layer Breakdown

### Layer 1 — View Layer (Frontend)
**Files:** `frontend/index.html`, `frontend/editor.html`, `frontend/main.js`, `frontend/editor.js`, `frontend/style.css`, `frontend/editor.css`

**Responsibility:** Render UI, collect user input, display results, stream SSE terminal output.

**Key classes/objects (JavaScript):**
- `TEMPLATES` object in `editor.js` (line 231): Stores 4 document templates (ieee, apa, litreview, executive)
- `ResultCache` — No JS equivalent; handled purely backend
- Functions in `main.js`: Handle search submission, Pro modal steps, SSE event listener for terminal
- Functions in `editor.js`: `initEditor()`, `initDividerDrag()`, `initTemplates()`, `initExports()`, `loadReportIntoEditor()`, `renderPreview()`, `reportToMarkdown()`

**How it connects to Application Layer:** Via `fetch()` / `XMLHttpRequest` HTTP calls to `http://localhost:5000/api/*` endpoints. SSE connection to `/api/agent/stream/<id>`.

---

### Layer 2 — Application Layer (Controller)
**File:** `api_server.py` (994 lines)

**Responsibility:** Route HTTP requests, apply rate limiting, check/populate cache, orchestrate service calls, return JSON responses or SSE streams.

**Key classes:**
- `ResultCache` (line 113-179): In-memory LRU cache. Fields: `cache` (OrderedDict), `max_size` (50), `ttl` (86400s/24h), `hits`, `misses`. Methods: `_key()`, `get()`, `put()`, `get_history()`, `stats()`

**Key constants:**
- `CACHE_MAX_SIZE = 50` (line 110)
- `CACHE_TTL_SECONDS = 86400` (24 hours, line 111)
- `RATE_LIMIT_WINDOW = 60` (seconds, line 188)
- `RATE_LIMIT_MAX = 5` (requests per window, line 189)
- `MAX_TOPIC_LENGTH = 200` (line 216)
- `MIN_TOPIC_LENGTH = 3` (line 217)
- `DEEP_RESEARCH_MONTHLY_LIMIT = 3` (line 434)

**How it connects:**
- Imports from: `paper_fetch`, `pdf_generator`, `deep_research`, `pro_research`, `database`, `browser_agent`, `rag_service`, `scraper_service`
- Serves frontend from: `static_folder='frontend'` (line 96)

---

### Layer 3 — Service Layer (Business Logic)
**Files:** `paper_fetch.py`, `pro_research.py`, `deep_research.py`, `rag_service.py`, `browser_agent.py`, `pdf_generator.py`, `scraper_service.py`

| Service File | Class/Function | Core Responsibility |
|---|---|---|
| `paper_fetch.py` | `fetch_research(topic)` | Lite pipeline: Tavily search+extract → Groq synthesis |
| `pro_research.py` | `generate_intake_chips()`, `process_intake()`, `generate_pro_plan()`, `execute_pro_research()` | Pro wizard pipeline |
| `deep_research.py` | `generate_questions()`, `generate_plan()`, `execute_deep_research()` | Deep conversational pipeline |
| `rag_service.py` | `RAGService` class | Fuzzy evidence matching via `difflib.SequenceMatcher` |
| `browser_agent.py` | `start_agent()`, `get_event_stream()`, `get_agent_result()` | Playwright browser automation via `browser-use` |
| `pdf_generator.py` | `generate_pdf()`, `enhance_content_academic()`, `build_pdf_content()` | ReportLab academic PDF |
| `scraper_service.py` | `StealthScraper` class | Standard HTTP → Scrapling stealth fallback |

---

### Layer 4 — Data Layer
**Files:** `database.py`, in-memory structures in `api_server.py`, `browser_agent.py`, `rag_service.py`

| Storage | Type | Location | Scope |
|---|---|---|---|
| `paperpilot.db` | SQLite (persistent) | `database.py` | Research sessions history |
| `ResultCache.cache` | `OrderedDict` (in-memory) | `api_server.py` L181 | LRU topic result cache |
| `rate_limit_store` | `dict` (in-memory) | `api_server.py` L191 | Per-IP request timestamps |
| `deep_research_usage` | `dict` (in-memory) | `api_server.py` L433 | Per-IP monthly deep research usage |
| `_agent_sessions` | `dict` (in-memory) | `browser_agent.py` L41 | SSE event queues per agent session |
| `_agent_results` | `dict` (in-memory) | `browser_agent.py` L43 | Final agent results per session |
| `_sessions` | `dict` (in-memory) | `rag_service.py` L26 | Evidence chunks per research session |
| `output/` directory | File system | `api_server.py` L103 | Generated PDF files |

---

## 2.4 Data Flow

### Feature: Lite Research (most common path)
```
[User types topic in index.html searchbar]
→ main.js: fetch('POST /api/research', {topic})
→ api_server.py: research()
  → check_rate_limit()          [IP-based 5 req/60s]
  → validate_topic()            [3-200 chars, strip control chars]
  → cache.get(topic)            [SHA256 hash key lookup in OrderedDict]
    → If HIT: return cached JSON immediately
    → If MISS:
      → paper_fetch.fetch_research(topic)
        → TavilyClient.search() × 3 categories (Academic, Wiki, Articles)
        → TavilyClient.extract() on top URLs
        → Groq.chat.completions.create() [llama-3.3-70b-versatile, JSON mode]
        → Returns structured dict
      → cache.put(topic, report)
      → (optional) database.save_session()
→ Returns JSON to frontend
→ main.js: renders results into DOM
```

### Feature: Pro Research Pipeline
```
[User opens Pro modal in index.html]
→ Step 1: main.js → POST /api/pro/chips {topic}
  → api_server.py → pro_research.generate_intake_chips(topic)
    → Groq: generate 6 sub-topic chips
→ User fills 6-question intake form
→ Step 2: main.js → POST /api/pro/plan {context}
  → api_server.py → pro_research.generate_pro_plan(context)
    → Groq: generate section-by-section JSON plan
→ User reviews plan, optionally starts Browser Agent
→ Step 3 (Agent): main.js → POST /api/agent/start {topic, queries}
  → api_server.py → browser_agent.start_agent(topic, queries)
    → Spawns daemon thread → asyncio loop → browser-use Agent
    → Playwright navigates Google Scholar
    → SSE events pushed to queue
  → main.js → GET /api/agent/stream/<session_id>  [SSE connection]
    → Renders live terminal events in UI
→ Step 4: main.js → POST /api/pro/execute {context, plan, agent_findings}
  → api_server.py → pro_research.execute_pro_research(context, plan, agent_findings)
    → Multi-query Tavily search per section
    → Tavily extract on URLs
    → Merge agent findings
    → Single Groq call with full aggregated context
    → Returns structured JSON report
  → api_server.py → database.save_session()
→ main.js: renders results
```

### Feature: Evidence Verification (RAG)
```
[User clicks on sentence in Results View]
→ main.js → POST /api/evidence {sentence, session_id}
→ api_server.py → rag_service.query_evidence(sentence, session_id)
  → Retrieves pre-indexed chunks from _sessions[session_id]
  → For each chunk: compute SequenceMatcher ratio (40%) + keyword overlap (60%)
  → Sort by combined score, filter >= 25% threshold
  → Return top 3 matching chunks with source URLs
→ main.js: highlights matching evidence snippet
```

---

## 2.5 Dependencies Map (Import Graph)

```
api_server.py imports:
  ├── paper_fetch        → fetch_research
  ├── pdf_generator      → generate_pdf
  ├── deep_research      → generate_questions, generate_plan, execute_deep_research
  ├── pro_research       → generate_intake_chips, process_intake, generate_pro_plan, execute_pro_research
  ├── database           → db, init_db, save_session, get_session, get_history
  ├── browser_agent      → start_agent, get_event_stream, get_agent_result
  ├── rag_service        → RAGService
  └── scraper_service    → StealthScraper

paper_fetch.py imports:
  ├── tavily (TavilyClient)
  └── groq (Groq)

pro_research.py imports:
  ├── tavily (TavilyClient)
  └── groq (Groq)

deep_research.py imports:
  ├── tavily (TavilyClient)
  └── groq (Groq)

pdf_generator.py imports:
  ├── groq (Groq)
  └── reportlab (many submodules)

browser_agent.py imports:
  ├── browser_use (Agent)
  └── browser_use.llm.groq.chat (ChatGroq)

rag_service.py imports:
  └── difflib (SequenceMatcher) [Python built-in — zero external deps]

scraper_service.py imports:
  ├── requests
  ├── bs4 (BeautifulSoup)
  └── scrapling (StealthyFetcher) [optional, checked at runtime]

database.py imports:
  └── flask_sqlalchemy (SQLAlchemy)
```

---

## 2.6 Design Patterns Used

| Pattern | Found In | Evidence |
|---|---|---|
| **Singleton** (effectively) | `api_server.py` L181: `cache = ResultCache()` | Single global `cache` object, single `rag_service` object |
| **Strategy** | `scraper_service.py` L221-268 | `extract()` tries `_standard_extract()` first, then falls back to `_stealth_extract()` — strategy switch based on result |
| **Observer / Event Queue** | `browser_agent.py` L41, L58 | `_agent_sessions` dict of `queue.Queue` objects; `push_event()` puts events, `get_event_stream()` yields them to SSE consumers |
| **Factory** (function-level) | `browser_agent.py` L80: `_make_step_callback(session_id)` | Closure factory that generates a step callback function per session |
| **Template Method** | `pdf_generator.py` L468: `build_pdf_content()` | Builds PDF in fixed sequence: Title → Abstract → TOC → Sections → Conclusion → References |
| **LRU Cache** | `api_server.py` L113: `ResultCache` | Uses `OrderedDict` with `move_to_end()` for LRU eviction, SHA256 keying |
| **Retry with Exponential Backoff** | `pro_research.py` L47: `_groq_call()`, `deep_research.py` L69 | Retries up to 3 times on rate limit errors, wait = `2^attempt * 5` seconds |
