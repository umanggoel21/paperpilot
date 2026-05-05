# File 3: Modules and Features Detail
# Source: Extracted directly from PaperPilot codebase — no assumptions made.

---

## Module: `paper_fetch.py`
**File path:** `d:\paperpilot\paper_fetch.py` (608 lines)
**Purpose:** *"Fetches information about a topic from research papers, Wikipedia, articles & blogs using Tavily, then structures it with Groq LLM."* (docstring line 2-3)
**Entry function:** `fetch_research(topic: str) -> dict`

### Constants (hardcoded values extracted from code):
| Constant | Value | Line | Purpose |
|---|---|---|---|
| `GROQ_MODEL` | `"llama-3.3-70b-versatile"` | 41 | LLM model name |
| `OUTPUT_DIR` | `./output/` | 42 | PDF/JSON save directory |
| `ACADEMIC_DOMAINS` | 10 domains (arxiv, pubmed, ieee, etc.) | 47-58 | Tavily domain filter |
| `WIKI_DOMAINS` | `["en.wikipedia.org"]` | 60-62 | Wikipedia search filter |

### `search_sources(topic, tavily)`
- **Returns:** `dict` with keys: `research_papers`, `wikipedia`, `articles_blogs`
- **What it does:** Runs 3 separate Tavily searches — (1) Academic domains, (2) Wikipedia, (3) general articles
- **Calls:** `tavily.search()` × 3

### `extract_content(results, tavily)`
- **Returns:** list of dicts with `full_content` field populated
- **What it does:** Calls `tavily.extract()` on all URLs found by `search_sources()`, adds extracted text to each result
- **Fallback:** If extraction fails, keeps the original `snippet` field

### `fetch_research(topic: str) -> dict`
- **Returns:** Structured JSON report dict
- **What it does:** Orchestrates the full Lite pipeline
  1. Creates `TavilyClient` and `Groq` clients from environment vars
  2. Calls `search_sources()` → categorized results
  3. Calls `extract_content()` → enriched with full text
  4. Builds a system prompt + user prompt with all content
  5. Calls `groq.chat.completions.create()` in JSON mode
  6. Returns parsed JSON dict
- **Key logic — prompt enforces this JSON schema:**
  ```json
  {
    "topic": "string",
    "executive_summary": "string",
    "sections": [{"title", "content", "key_points": []}],
    "key_takeaways": ["string"],
    "sources_used": [{"ref_id", "title", "url", "source_type"}],
    "total_sources": integer,
    "generated_at": "ISO timestamp"
  }
  ```

---

## Module: `pro_research.py`
**File path:** `d:\paperpilot\pro_research.py` (468 lines)
**Purpose:** *"The Pro Search pipeline processes a 6-question intake form, generates a research plan, then runs an enhanced search → extraction → synthesis flow."* (docstring lines 2-5)

### Constants:
| Constant | Value | Line | Purpose |
|---|---|---|---|
| `GROQ_MODEL` | `"llama-3.3-70b-versatile"` | 32 | LLM model |
| `ACADEMIC_DOMAINS` | 10 domains | 35-39 | Tavily academic filter |
| `WIKI_DOMAINS` | `["en.wikipedia.org"]` | 40 | Wikipedia filter |

### `_groq_call(groq_client, messages, max_tokens, temperature, json_mode, retries=3)`
- **What it does:** Wrapper for Groq API calls with exponential backoff on rate limits
- **Retry logic:** `wait = (2 ** attempt) * 5` seconds (5s, 10s, 20s)
- **Error handling:** Catches `rate_limit` or `429` errors; raises after 3 failures

### `generate_intake_chips(topic: str) -> dict`
- **Returns:** `{"chips": ["sub-topic 1", ..., "sub-topic 6"]}`
- **What it does:** Calls Groq to generate 6 context-specific sub-topic chips for the Pro intake form's Q5 field
- **Temperature:** 0.4 (from `_groq_call` default)

### `process_intake(topic, answers) -> dict`
- **Returns:** Structured context dict for Pro execution
- **What it does:** Validates and packages the 6 intake form answers into a standardized context object

### `generate_pro_plan(context: dict) -> dict`
- **Returns:** `{"plan": [{"section_title", "search_query", "objectives"}], "estimated_time": "..."}`
- **What it does:** Sends context to Groq to generate a section-by-section research plan

### `execute_pro_research(context, plan, agent_findings=None) -> dict`
- **Returns:** Full research report dict (same schema as Lite)
- **What it does:**
  1. For each section in plan: runs `tavily.search()` + `tavily.extract()` on academic, wiki, and article domains
  2. Merges `agent_findings` (from browser agent) if provided
  3. Builds ONE large aggregated prompt with all content
  4. Makes a single Groq call to synthesize the full report
  5. Saves session to database via `database.save_session()`

---

## Module: `deep_research.py`
**File path:** `d:\paperpilot\deep_research.py` (438 lines)
**Purpose:** *"Enhanced research pipeline with conversational configuration. Three-phase flow."* (docstring lines 2-4)

### Constants:
| Constant | Value | Line | Purpose |
|---|---|---|---|
| `GROQ_MODEL` | `"llama-3.3-70b-versatile"` | 32 | LLM model |
| `SOURCE_LIMITS` | `{3: {papers:2,wiki:1,articles:2}, 5: {papers:3,...}, 7: {papers:4,...}}` | 35-39 | Sources per config tier |
| `TOKEN_LIMITS` | `{short:2048, medium:4096, long:6000}` | 42-46 | Max tokens per length setting |
| `EXTRACT_LIMITS` | `{short:800, medium:1500, long:2500}` | 49-53 | Chars per source per length |

### `generate_questions(topic, config) -> dict`
- **Returns:** `{"questions": [{"id", "question", "placeholder"}]}`
- **What it does:** Calls Groq to generate 3 personalized clarifying questions about the topic

### `generate_plan(topic, config, answers) -> dict`
- **Returns:** `{"plan": [...], "research_focus": "...", "estimated_time": "..."}`
- **What it does:** Takes user answers to the 3 questions and builds a research section plan

### `execute_deep_research(topic, config, answers, plan) -> dict`
- **Returns:** Full research report dict
- **What it does:**
  1. Looks up `SOURCE_LIMITS` and `TOKEN_LIMITS` based on `config.sources` and `config.length`
  2. For each section in plan: Tavily search + Tavily extract (capped at `EXTRACT_LIMITS`)
  3. Builds context-aware prompt including user answers
  4. Single Groq call for final synthesis

---

## Module: `rag_service.py`
**File path:** `d:\paperpilot\rag_service.py` (209 lines)
**Purpose:** *"Lightweight source verification engine using Python's built-in difflib.SequenceMatcher. Zero external dependencies."* (docstring lines 2-5)

**IMPORTANT NOTE:** Despite `chromadb` and `sentence-transformers` being in `requirements.txt`, the **actual `rag_service.py` in use** is a pure-Python fallback using `difflib`. ChromaDB version is in `rag_service_full.py` (not imported by `api_server.py`).

### Global state:
- `_sessions: Dict[str, List[Dict]]` (line 26) — in-memory store mapping `session_id → list of paragraph chunks`

### Class: `RAGService`

#### `__init__(persist_dir=None)`
- Sets `self.available = True` unconditionally (pure Python, always works)

#### `_chunk_text(text, source_url, source_title, source_type, chunk_size=3)`
- **Returns:** `List[Dict]` — each dict has `text`, `text_lower`, `source_url`, `source_title`, `source_type`
- **Algorithm:**
  1. Cleans whitespace with `re.sub(r'\s+', ' ', text)`
  2. Splits into sentences on pattern `(?<=[.!?])\s+(?=[A-Z])`
  3. Filters sentences shorter than 20 chars
  4. Groups into chunks of `chunk_size=3` sentences
  5. Filters chunks shorter than 40 chars
- **Pre-computes:** `text_lower` for performance

#### `index_sources(sources: List[Dict], session_id: str) -> Dict`
- **Returns:** `{"total_chunks", "total_words", "sources_indexed", "time_taken"}`
- **What it does:** Iterates all sources, calls `_chunk_text()`, stores all chunks in `_sessions[session_id]`
- **Minimum content length:** 50 chars (skips shorter)

#### `query_evidence(sentence, session_id, top_k=3) -> List[Dict]`
- **Returns:** List of dicts: `{text, source_url, source_title, source_type, similarity_score}`
- **Algorithm (HYBRID — 2 methods combined):**
  1. **Method 1:** `difflib.SequenceMatcher(None, sentence_lower, chunk_lower).ratio()` → `seq_score`
  2. **Method 2:** Keyword overlap = `|query_words ∩ chunk_words| / |query_words|` → `overlap`
  3. **Combined score formula:** `combined = (seq_score × 0.4) + (overlap × 0.6)`
  4. **Threshold filter:** Returns only results where `similarity_score >= 25%`
  5. **Stop words set:** 25 common English words excluded from keyword matching
- **Returns top `top_k=3` results sorted by combined score descending**

#### `get_session_stats(session_id) -> Optional[Dict]`
- **Returns:** `{"total_chunks", "sources"}` or `None`

---

## Module: `browser_agent.py`
**File path:** `d:\paperpilot\browser_agent.py` (335 lines)
**Purpose:** *"Uses browser-use to autonomously browse the web for research data. Runs in a background thread with real-time step-by-step progress streamed to the frontend via SSE."* (docstring lines 2-5)

### Global state:
- `_agent_sessions: dict` (line 41) — `session_id → queue.Queue`
- `_agent_results: dict` (line 43) — `session_id → final result dict`

### Constants:
| Constant | Value | Line | Purpose |
|---|---|---|---|
| `max_steps` | `15` | 188 | Max Playwright agentic loop iterations |
| `max_timeout` | `120` | 312 | Max seconds to wait for events (2 minutes) |
| LLM model | `"meta-llama/llama-4-scout-17b-16e-instruct"` | 143 | Browser agent uses different model than research |
| `temperature` | `0.1` | 145 | Agent LLM temperature |
| `use_vision` | `False` | 188 | Vision disabled (Groq free tier) |

### `start_agent(topic, search_queries=None) -> str`
- **Returns:** `session_id` (12-char hex from `uuid4().hex[:12]`)
- **What it does:** Spawns a daemon thread running `_run_in_thread()`
- **Default queries:** `[f"{topic} research"]`

### `_run_in_thread(session_id, topic, search_queries)`
- Runs `asyncio.new_event_loop()` and calls `_run_agent_async()`
- Stores result in `_agent_results[session_id]`

### `_run_agent_async(session_id, topic, search_queries)`
- **What it does:**
  1. Initializes `ChatGroq` (browser-use native wrapper, not `langchain-groq` directly)
  2. Builds task prompt instructing agent to search Google Scholar, open 2-3 results, extract key findings
  3. Creates `browser_use.Agent(task, llm, max_steps=15, use_vision=False, register_new_step_callback=...)`
  4. Calls `agent.run()` asynchronously
  5. Extracts `final_result()` or `extracted_content` from result history
  6. Attempts to parse JSON with `findings[]` structure from text
  7. Falls back to raw text summary if JSON parsing fails

### `get_event_stream(session_id) -> Generator`
- **Yields:** SSE-formatted strings: `"event: {type}\ndata: {json}\n\n"`
- **Event types:** `status`, `step`, `error`, `complete`, `done`
- **Timeout:** 120 seconds max wait, sends `": keepalive\n\n"` every 1s while waiting
- **Terminal event:** `done` — stops the generator

### `push_event(session_id, event_type, data)`
- Puts event dict into `_agent_sessions[session_id]` queue

---

## Module: `pdf_generator.py`
**File path:** `d:\paperpilot\pdf_generator.py` (870 lines)
**Purpose:** *"Takes structured JSON (from paper_fetch.py) and generates a professional academic-level PDF document using ReportLab. Uses Groq LLM to rewrite/enhance content to academic standards before rendering the PDF."* (docstring)

### Constants/Config (extracted from code):
| Constant | Value | Line | Purpose |
|---|---|---|---|
| `GROQ_MODEL` | `"llama-3.3-70b-versatile"` | 68 | Enhancement LLM |
| `PAGE_WIDTH, PAGE_HEIGHT` | A4 (595.27 × 841.89 pt) | 74 | Page size |
| `MARGIN` | `1 * inch` (72pt) | 75 | All page margins |
| `ACCENT_COLOR` | `HexColor("#1a1a2e")` | 78 | Title/heading color |
| `HEADING_COLOR` | `HexColor("#16213e")` | 79 | Heading text color |
| `LINK_COLOR` | `HexColor("#0f4c75")` | 80 | Citation link color |
| `LINE_SPACING` | `18` pt | 133 | 1.5× of 12pt body |

### PDF Style Definitions (from `build_styles()`):
| Style Name | Font | Size | Alignment | Notes |
|---|---|---|---|---|
| `title` | TimesNR-Bold (fallback: Times-Bold) | 16pt | CENTER | Title page |
| `subtitle` | TimesNR | 12pt | CENTER | Date, source count |
| `section_heading` | TimesNR-Bold | 14pt | LEFT | Numbered sections |
| `sub_heading` | TimesNR-Bold | 12pt | LEFT | Key findings header |
| `body` | TimesNR | 12pt | JUSTIFY | Body text, 18pt leading |
| `body_indent` | TimesNR | 12pt | JUSTIFY | First line indent 24pt |
| `bullet` | TimesNR | 12pt | JUSTIFY | Left indent 24pt |
| `reference` | TimesNR | 11pt | JUSTIFY | Hanging indent -24pt |
| `header` | TimesNR | 10pt | LEFT | Page header (page > 1) |
| `footer` | TimesNR | 10pt | CENTER | Page numbers |
| `abstract_body` | TimesNR-Italic | 12pt | JUSTIFY | Abstract text |

### Font Registration (`register_fonts()`):
- Tries to load from `C:\Windows\Fonts\times.ttf` (and bold/italic variants)
- Falls back to built-in ReportLab `"Times-Roman"` if not found

### `enhance_content_academic(report: dict) -> dict`
- **What it does:** Calls Groq with `temperature=0.3`, `max_tokens=4096`, `json_mode=True`
- **Academic rules enforced in system prompt:** third-person tone, preserve citations `[1]`, 150-250 words per section, transition phrases, 4-5 sentences per paragraph
- **Returns enhanced report** with new `enhanced_abstract`, updated `sections[].content`, new `conclusion`

### `generate_pdf(report_input, output_path=None, enhance=True) -> str`
- **Returns:** File path to generated PDF
- **Step 1:** If `enhance=True` → calls `enhance_content_academic()`
- **Step 2:** Calls `build_pdf_content()` → list of ReportLab flowables
- **Step 3:** `SimpleDocTemplate.build(story, onFirstPage=HeaderFooter, onLaterPages=HeaderFooter)`

### PDF Document Structure (from `build_pdf_content()`):
1. **Title Page:** Topic title + HR divider + "Research Report" + date + source breakdown
2. **Abstract:** `enhanced_abstract` or `executive_summary` in italic
3. **Page Break**
4. **Table of Contents:** Section titles + key points as sub-entries
5. **Page Break**
6. **Body Sections:** For each section: numbered heading → paragraphs → "X.1 Key Findings" bullet list
7. **Conclusion** (if present): numbered section
8. **References:** `[ref_id] Title. [Type]. URL` — hyperlinked
9. **Source Summary Table:** Category | Count table with styled header row

### Citation formatting (`_format_citation_refs()`):
- Transforms `[1]`, `[2]` patterns into `<font color="#0f4c75"><super>[1]</super></font>`

---

## Module: `scraper_service.py`
**File path:** `d:\paperpilot\scraper_service.py` (281 lines)
**Purpose:** *"Fallback content extractor using Scrapling. When Tavily's extract() fails on protected sites (Cloudflare, etc.), this module uses stealth browsers to bypass anti-bot measures."*

### Constants:
| Constant | Value | Line | Purpose |
|---|---|---|---|
| `STANDARD_UA` | `"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."` | 24-28 | HTTP User-Agent |
| `STEALTH_PRIORITY_DOMAINS` | 8 domains (researchgate, sciencedirect, ieee, springer, nature, wiley, tandfonline, sagepub) | 31-40 | Skip-to-stealth domains |
| Blocked HTTP codes | `[403, 429, 503]` | 81 | Treat as bot-blocked |
| Min content length | `200` chars | 112, 156 | Skip short/boilerplate responses |

### Class: `StealthScraper`

#### `extract(url: str) -> Dict`
- **Returns:** `{"url", "text", "method_used", "word_count", "success"}`
- **Algorithm:**
  1. If URL domain is in `STEALTH_PRIORITY_DOMAINS` → skip straight to `_stealth_extract()`
  2. Else: try `_standard_extract()` first
  3. If standard fails → try `_stealth_extract()` (if Scrapling available)
  4. `method_used` field = `"standard"` | `"stealth"` | `"failed"`

#### `_standard_extract(url, timeout=15) -> Optional[str]`
- Uses `requests.get()` with standard User-Agent header
- Checks for bot-detection indicators: `"cf-browser-verification"`, `"challenge-platform"`, `"captcha"`, `"recaptcha"`, `"hCaptcha"`, `"cf-turnstile"`, `"Access Denied"`, `"bot detection"`
- Calls `_html_to_text()` on response

#### `_stealth_extract(url) -> Optional[str]`
- Uses `scrapling.StealthyFetcher().fetch(url)`
- Falls back gracefully if `scrapling` not installed

#### `_html_to_text(html) -> str`
- Uses `BeautifulSoup(html, 'html.parser')`
- Removes tags: `script`, `style`, `nav`, `header`, `footer`, `aside`, `form`, `noscript`, `iframe`
- Extracts text with `\n` separators

#### `batch_extract(urls: List[str]) -> List[Dict]`
- Calls `extract()` sequentially for each URL in list

---

## Module: `database.py`
**File path:** `d:\paperpilot\database.py` (116 lines)
**Purpose:** *"Persistent storage for research sessions and reports. Replaces the in-memory ResultCache for durable history."*

### Class: `ResearchSession(db.Model)`
- **Table:** `research_sessions`
- **Key methods:**
  - `set_report(report_dict)`: `json.dumps()` into `report_json`, extracts `total_sources`, `elapsed_seconds`
  - `get_report()`: `json.loads(report_json)` → returns dict
  - `to_history_dict()`: Returns lightweight dict with `session_id`, `topic`, `mode`, `total_sources`, `elapsed_seconds`, `created_at`

### Module-level functions:
- `init_db(app)`: Configures `SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'`, calls `db.create_all()`
- `save_session(session_id, topic, report, mode='lite', config=None)`: Upsert — updates if `session_id` exists, inserts if not
- `get_session(session_id)`: Returns `report_json` deserialized, or `None`
- `get_history(limit=20)`: Returns list of `to_history_dict()` sorted by `created_at DESC`
