# File 5: API and External Integrations
# Source: Extracted directly from api_server.py — no assumptions made.

---

## 5.1 Internal API Endpoints

**Source:** All `@app.route` decorators in `api_server.py`

| Method | Endpoint | Parameters | Returns | Line | Auth? |
|---|---|---|---|---|---|
| GET | `/` | None | `index.html` (HTML) | 242 | No |
| GET | `/editor` | None | `editor.html` (HTML) | 248 | No |
| GET | `/<path:path>` | path (URL segment) | Static file from `frontend/` | 254 | No |
| GET | `/api/health` | None | JSON: status, features, cache stats | 260 | No |
| POST | `/api/research` | Body: `{topic}` | Full research report JSON | 282 | No |
| POST | `/api/pdf` | Body: `{report, enhance}` | JSON: `{pdf_url, filename, pdf_base64, size_bytes}` | 355 | No |
| GET | `/api/pdf/download/<filename>` | filename (path param) | PDF file (application/pdf) | 407 | No |
| GET | `/api/history` | None | JSON: `{history: [...]}` | 420 | No |
| POST | `/api/deep/questions` | Body: `{topic, config}` | JSON: `{questions: [...], remaining_uses}` | 459 | No |
| POST | `/api/deep/plan` | Body: `{topic, config, answers}` | JSON: `{plan, research_focus, estimated_time}` | 489 | No |
| POST | `/api/deep/execute` | Body: `{topic, config, answers, plan}` | Full research report JSON | 515 | No |
| POST | `/api/research/enhanced` | Body: `{topic}` | Report JSON + `extraction_log` + `rag_stats` + `session_id` | 567 | No |
| POST | `/api/evidence` | Body: `{sentence, session_id}` | JSON: `{evidence: [...top matches...]}` | ~650 | No |
| POST | `/api/pro/chips` | Body: `{topic}` | JSON: `{chips: [...6 subtopics...]}` | ~700 | No |
| POST | `/api/pro/intake` | Body: `{topic, answers}` | JSON: structured context | ~720 | No |
| POST | `/api/pro/plan` | Body: `{context}` | JSON: `{plan, estimated_time}` | ~740 | No |
| POST | `/api/pro/execute` | Body: `{context, plan, agent_findings?}` | Full research report JSON | ~760 | No |
| POST | `/api/agent/start` | Body: `{topic, queries}` | JSON: `{session_id}` | ~800 | No |
| GET | `/api/agent/stream/<session_id>` | session_id (path param) | SSE stream (`text/event-stream`) | ~820 | No |

**No authentication on any endpoint. No API key required from client side.**

---

## 5.2 Rate Limiting (Extracted from `api_server.py`)

### Global Research Rate Limit (`check_rate_limit()`)
| Parameter | Value | Line |
|---|---|---|
| Window | 60 seconds | 188 |
| Max requests | 5 per window per IP | 189 |
| Storage | `rate_limit_store = {}` (global in-memory dict) | 191 |
| HTTP response on limit | 429 with `{"error": "Too many requests..."}` | 297 |

### Deep Research Monthly Limit (`check_deep_rate_limit()`)
| Parameter | Value | Line |
|---|---|---|
| Window | 30 days (30 × 24 × 60 × 60 seconds) | 440 |
| Max uses | 3 per month per IP | 434 |
| Storage | `deep_research_usage = {}` (global in-memory dict) | 433 |
| Response on limit | 429 with `{"error": "Monthly deep research limit reached (3/month)..."}` | 469 |

---

## 5.3 External APIs Used

### API 1: Groq API
**Source:** `paper_fetch.py` lines 26, 39-41; `pro_research.py` lines 25, 31-32; `pdf_generator.py` lines 42, 67-68; `browser_agent.py` lines 134, 142-146

| Property | Value | Source File |
|---|---|---|
| Package | `groq` | `requirements.txt` line 2 |
| Authentication | `GROQ_API_KEY` environment variable | All files: `os.getenv("GROQ_API_KEY")` |
| Model (research) | `"llama-3.3-70b-versatile"` | `paper_fetch.py` L41, `pro_research.py` L32, `deep_research.py` L32, `pdf_generator.py` L68 |
| Model (browser agent) | `"meta-llama/llama-4-scout-17b-16e-instruct"` | `browser_agent.py` line 143 |
| API call method | `groq_client.chat.completions.create(model, messages, temperature, max_tokens, response_format)` | All service files |
| JSON mode | `response_format={"type": "json_object"}` | All synthesis calls |
| Temperature (synthesis) | `0.4` | `_groq_call()` default in `pro_research.py` and `deep_research.py` |
| Temperature (enhancement) | `0.3` | `pdf_generator.py` line 373 |
| Temperature (agent) | `0.1` | `browser_agent.py` line 145 |
| Max tokens (short) | `2048` | `deep_research.py` `TOKEN_LIMITS` |
| Max tokens (medium) | `4096` | `deep_research.py` `TOKEN_LIMITS` |
| Max tokens (long) | `6000` | `deep_research.py` `TOKEN_LIMITS` |
| Max tokens (PDF enhance) | `4096` | `pdf_generator.py` line 379 |
| Retry on rate limit | Yes — 3 retries, exponential backoff `(2^attempt × 5)s` | `pro_research.py` `_groq_call()` |

### API 2: Tavily API
**Source:** `paper_fetch.py` lines 24, 40, 69-76; `pro_research.py` lines 23; `deep_research.py` lines 23

| Property | Value | Source File |
|---|---|---|
| Package | `tavily-python` | `requirements.txt` line 1 |
| Authentication | `TAVILY_API_KEY` environment variable | All files: `os.getenv("TAVILY_API_KEY")` |
| Client creation | `TavilyClient(api_key=TAVILY_API_KEY)` | All service files |
| Method 1 | `tavily.search(query, include_domains=[...], max_results=N)` | `search_sources()` in `paper_fetch.py` |
| Method 2 | `tavily.extract(urls=[...])` | `extract_content()` in `paper_fetch.py` |
| Academic domains searched | `arxiv.org`, `pubmed.ncbi.nlm.nih.gov`, `researchgate.net`, `ieee.org`, `sciencedirect.com`, `semanticscholar.org`, `scholar.google.com`, `ncbi.nlm.nih.gov`, `nature.com`, `springer.com` | `paper_fetch.py` L47-58 |
| Wikipedia domain | `en.wikipedia.org` | `paper_fetch.py` L60-62 |

---

## 5.4 Configuration and Constants (All Hardcoded Values)

**Source:** Extracted from all files

| Constant Name | Value | Found In | Purpose |
|---|---|---|---|
| `GROQ_MODEL` | `"llama-3.3-70b-versatile"` | `paper_fetch.py`, `pro_research.py`, `deep_research.py`, `pdf_generator.py` | LLM model for research synthesis |
| Browser Agent model | `"meta-llama/llama-4-scout-17b-16e-instruct"` | `browser_agent.py` L143 | LLM model for agentic browser |
| `CACHE_MAX_SIZE` | `50` | `api_server.py` L110 | Max LRU cache entries |
| `CACHE_TTL_SECONDS` | `86400` (24 hours) | `api_server.py` L111 | Cache expiry time |
| `RATE_LIMIT_WINDOW` | `60` (seconds) | `api_server.py` L188 | Rate limit time window |
| `RATE_LIMIT_MAX` | `5` | `api_server.py` L189 | Max requests per window |
| `MAX_TOPIC_LENGTH` | `200` | `api_server.py` L216 | Topic validation upper bound |
| `MIN_TOPIC_LENGTH` | `3` | `api_server.py` L217 | Topic validation lower bound |
| `DEEP_RESEARCH_MONTHLY_LIMIT` | `3` | `api_server.py` L434 | Monthly deep research cap |
| `SOURCE_LIMITS[3]` | `{papers:2, wiki:1, articles:2}` | `deep_research.py` L36 | Sources for 3-source config |
| `SOURCE_LIMITS[5]` | `{papers:3, wiki:1, articles:3}` | `deep_research.py` L37 | Sources for 5-source config |
| `SOURCE_LIMITS[7]` | `{papers:4, wiki:2, articles:4}` | `deep_research.py` L38 | Sources for 7-source config |
| `TOKEN_LIMITS["short"]` | `2048` | `deep_research.py` L43 | Max tokens for short reports |
| `TOKEN_LIMITS["medium"]` | `4096` | `deep_research.py` L44 | Max tokens for medium reports |
| `TOKEN_LIMITS["long"]` | `6000` | `deep_research.py` L45 | Max tokens for long reports |
| `EXTRACT_LIMITS["short"]` | `800` chars | `deep_research.py` L50 | Per-source extract limit (short) |
| `EXTRACT_LIMITS["medium"]` | `1500` chars | `deep_research.py` L51 | Per-source extract limit (medium) |
| `EXTRACT_LIMITS["long"]` | `2500` chars | `deep_research.py` L52 | Per-source extract limit (long) |
| `MARGIN` | `1 * inch` (72pt) | `pdf_generator.py` L75 | PDF page margins |
| `LINE_SPACING` | `18` pt | `pdf_generator.py` L133 | Body text leading (1.5× of 12pt) |
| `ACCENT_COLOR` | `HexColor("#1a1a2e")` | `pdf_generator.py` L78 | PDF accent color |
| `HEADING_COLOR` | `HexColor("#16213e")` | `pdf_generator.py` L79 | PDF heading color |
| `LINK_COLOR` | `HexColor("#0f4c75")` | `pdf_generator.py` L80 | PDF citation link color |
| Agent `max_steps` | `15` | `browser_agent.py` L188 | Max browser agent iterations |
| Agent `max_timeout` | `120` seconds | `browser_agent.py` L312 | SSE stream max wait |
| Agent temperature | `0.1` | `browser_agent.py` L145 | Low temp for deterministic browsing |
| Similarity threshold | `25%` | `rag_service.py` L184 | Minimum evidence match score |
| Evidence score formula | `(seq × 0.4) + (overlap × 0.6)` | `rag_service.py` L169 | Hybrid scoring weights |
| Chunk size | `3` sentences | `rag_service.py` L45 | Text chunking parameter |
| Min sentence length | `20` chars | `rag_service.py` L55 | Skip very short sentences |
| Min chunk length | `40` chars | `rag_service.py` L64 | Skip trivial chunks |
| Min source content | `50` chars | `rag_service.py` L90 | Skip near-empty sources |
| `STANDARD_UA` | `"Mozilla/5.0 (Windows NT 10.0..."` | `scraper_service.py` L24-28 | HTTP request User-Agent |
| Min scraped content | `200` chars | `scraper_service.py` L112, 156 | Reject boilerplate responses |
| Stealth HTTP timeout | `15` seconds | `scraper_service.py` L67 | Standard extract timeout |
| Auto-save interval | `30000` ms (30 seconds) | `editor.js` L77 | Editor draft auto-save interval |
| Markdown debounce | `150` ms | `editor.js` L52 | Preview render delay |
| `DB_PATH` | `./paperpilot.db` | `database.py` L22 | SQLite file location |
| `STEALTH_PRIORITY_DOMAINS` | 8 domains (researchgate, sciencedirect, ieee, springer, nature, wiley, tandfonline, sagepub) | `scraper_service.py` L31-40 | Domains to use stealth-first |
