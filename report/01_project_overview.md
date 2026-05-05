# File 1: Project Overview
# Source: Extracted directly from PaperPilot codebase — no assumptions made.

---

## 1.1 Project Identity

| Property | Value | Source File |
|---|---|---|
| Project Name | PaperPilot | `api_server.py` line 265: `"service": "PaperPilot API"` |
| Version | Not specified | Not found in any config file |
| Platform | Web Application (Browser-based SPA + Flask Backend) | `api_server.py` line 96: `static_folder='frontend'` |
| Primary Language | Python 3 | `api_server.py`, `paper_fetch.py`, `pro_research.py` etc. |
| Secondary Language | JavaScript (Vanilla), HTML5, CSS3 | `frontend/main.js`, `frontend/editor.js`, `frontend/index.html`, `frontend/editor.html` |
| Backend Framework | Flask + Flask-CORS + Flask-SQLAlchemy | `requirements.txt` lines 6-8 |
| Architecture Pattern | MVC (Model-View-Controller) | Model=`database.py`, View=`frontend/`, Controller=`api_server.py` |
| Entry Point | `api_server.py` | `api_server.py` line 96: `app = Flask(...)` |
| Build System | None (plain Python, run directly) | `api_server.py` comment: `Run: python api_server.py` |
| Database File | `paperpilot.db` (SQLite) | `database.py` line 22: `DB_PATH = ... 'paperpilot.db'` |

---

## 1.2 Problem Being Solved

**Source:** `paper_fetch.py` docstring (lines 1-14), `pdf_generator.py` docstring (lines 1-32), `api_server.py` docstring (lines 1-13).

PaperPilot is described in its source code as:
- `paper_fetch.py`: *"Fetches information about a topic from research papers, Wikipedia, articles & blogs using Tavily, then structures it with Groq LLM."*
- `pdf_generator.py`: *"Takes structured JSON (from paper_fetch.py) and generates a professional academic-level PDF document using ReportLab. Uses Groq LLM to rewrite/enhance content to academic standards before rendering the PDF."*
- `api_server.py`: *"REST API that bridges the frontend with paper_fetch.py and pdf_generator.py."*
- `rag_service.py`: *"When the AI writes a sentence, this module finds the exact paragraph from the original scraped sources that matches it most closely."*
- `browser_agent.py`: *"Uses browser-use to autonomously browse the web for research data."*
- `scraper_service.py`: *"Fallback content extractor using Scrapling. When Tavily's extract() fails on protected sites (Cloudflare, etc.), this module uses stealth browsers to bypass anti-bot measures."*

---

## 1.3 Target Users

**Source:** Inferred from UI labels in `frontend/index.html` and role descriptions in `browser_agent.py`.

- **Students** — Quick Lite Mode research for any topic
- **Researchers** — Deep Mode (3 targeted questions) and Pro Mode (full wizard pipeline)
- No authentication system exists. No user table in database. All users are anonymous.

---

## 1.4 Core Features List

**Source:** Scanned from all API routes (`api_server.py`), all service files, and frontend UI elements.

| Feature Name | Where Found in Code | Technical Implementation |
|---|---|---|
| Lite Research | `GET /api/research` (api_server.py L282), `paper_fetch.py` | Single-shot: Tavily Search → Tavily Extract → Groq LLaMA synthesis |
| Deep Research | `POST /api/deep/questions`, `/api/deep/plan`, `/api/deep/execute` (api_server.py L459-560) | 3-phase: AI Questions → User Answers → AI Plan → Execute |
| Pro Research | `POST /api/pro/chips`, `/api/pro/intake`, `/api/pro/plan`, `/api/pro/execute` | Wizard: 6-question intake → AI plan → multi-query execution |
| Browser Agent | `POST /api/agent/start`, `GET /api/agent/stream/<id>` (api_server.py) | Playwright via `browser-use`, streams via SSE |
| PDF Generation | `POST /api/pdf`, `GET /api/pdf/download/<filename>` (api_server.py L355-417) | ReportLab → base64 encoded response |
| Evidence Verification | `POST /api/evidence` | Hybrid fuzzy matching (SequenceMatcher + keyword overlap) |
| Enhanced Research + RAG | `POST /api/research/enhanced` (api_server.py L567) | Tavily + StealthScraper + RAGService indexing |
| Research History | `GET /api/history` (api_server.py L420) | LRU Cache `get_history(limit=10)` |
| Document Editor | `/editor` route → `editor.html` | Split-pane Markdown editor with live HTML preview |
| PDF Export from Editor | Button in `editor.html` → `POST /api/pdf` | Calls same `/api/pdf` endpoint with editor content |
| Template System | `editor.js` lines 231-361 | 4 templates: IEEE, APA, Literature Review, Executive Brief |
| Auto-Save Draft | `editor.js` lines 76-97 | `localStorage.setItem('paperpilot_editor_draft', ...)` every 30s |
| Rate Limiting | `check_rate_limit()` in `api_server.py` L193 | IP-based: 5 req/60s per IP (global dict) |
| Deep Research Monthly Limit | `check_deep_rate_limit()` in `api_server.py` L436 | 3 uses/month per IP (global dict) |
| Health Check | `GET /api/health` (api_server.py L260) | Returns feature availability flags |

---

## 1.5 Technology Stack

**Source:** `requirements.txt` (all 14 lines), import statements across all files.

| Category | Technology | Version (from requirements.txt) | Used For |
|---|---|---|---|
| Frontend | HTML5 / CSS3 / Vanilla JavaScript | N/A | SPA UI, modal wizard, live terminal |
| Backend Framework | Flask | Latest (unversioned) | REST API + SSE streaming + static file serving |
| Cross-Origin | Flask-CORS | Latest | Enable CORS for frontend-backend communication |
| ORM | Flask-SQLAlchemy | Latest | Database abstraction layer |
| Database | SQLite (via Python built-in) | N/A | Persistent session storage (`paperpilot.db`) |
| LLM Inference | Groq (`groq` package) | Latest | LLaMA-3.3-70b-versatile for all synthesis |
| LLM (Agent) | `langchain-groq` | Latest | Used in `browser_agent.py` for `ChatGroq` |
| Web Search | `tavily-python` | Latest | Tavily Search + Extract API |
| PDF Generation | `reportlab` | Latest | Academic PDF creation |
| CLI UI | `rich` | Latest | Console spinners, panels, progress bars |
| Environment | `python-dotenv` | Latest | Load `.env` API keys |
| Vector DB (listed) | `chromadb` | Latest | Listed in requirements; RAG service uses fuzzy matching instead |
| Embeddings (listed) | `sentence-transformers` | Latest | Listed in requirements; current `rag_service.py` uses `difflib` |
| HTML Parsing | `beautifulsoup4` | Latest | `scraper_service.py` HTML-to-text conversion |
| Browser Automation | `browser-use` + `playwright` | Latest | `browser_agent.py` live web browsing |

---

## 1.6 Project Statistics

**Source:** Counted from directory listing and file views.

| Metric | Count | Notes |
|---|---|---|
| Total Python backend files | 8 | `api_server.py`, `paper_fetch.py`, `pro_research.py`, `deep_research.py`, `rag_service.py`, `rag_service_full.py`, `browser_agent.py`, `pdf_generator.py`, `database.py`, `scraper_service.py` |
| Total frontend files | 6 | `index.html`, `editor.html`, `main.js`, `editor.js`, `style.css`, `editor.css` |
| Total test files | 1 | `test_evidence.py` |
| API endpoints (routes) | 17 | Counted from all `@app.route` decorators in `api_server.py` |
| Database tables | 1 | `research_sessions` only (in `database.py`) |
| Service/module files | 7 | `paper_fetch`, `pro_research`, `deep_research`, `rag_service`, `browser_agent`, `pdf_generator`, `scraper_service` |
| External packages | 14 | From `requirements.txt` |
| UI Pages/Screens | 2 | `index.html` (main), `editor.html` (editor) |
| Environment variables required | 2 | `GROQ_API_KEY`, `TAVILY_API_KEY` (from `.env`) |
