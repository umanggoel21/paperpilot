# File 8: Figures Needed for Project Report
# Source: Based on actual codebase architecture — no assumptions made.

---

## 8.1 Mandatory Figures Table

| Fig No. | Caption | Chapter | What to Show | Tool |
|---|---|---|---|---|
| 1.1 | Research Process Gap: Manual vs. PaperPilot | 1 | Before/After comparison of manual vs. automated research | draw.io |
| 3.1 | System Architecture: MVC Layered View | 3 | All 4 layers with exact file names and connections | draw.io |
| 3.2 | Project Folder Structure | 3 | Directory tree (use the exact tree from 02_architecture.md) | Text/draw.io |
| 4.1 | App Navigation and User Flow | 4 | index.html → modes → results → editor.html | draw.io |
| 4.2 | Home Screen: Search Interface (index.html) | 4 | Screenshot / mockup of search bar, mode toggle, hero | Screenshot |
| 4.3 | Pro Research Wizard: Step 1 — Intake Form | 4 | Screenshot / mockup of 6-question modal | Screenshot |
| 4.4 | Pro Research Wizard: Step 2 — Research Plan | 4 | Screenshot / mockup of AI-generated plan display | Screenshot |
| 4.5 | Live Agent Terminal (SSE Stream) | 4 | Screenshot / mockup of macOS-style terminal | Screenshot |
| 4.6 | Results View with Action Bar | 4 | Screenshot showing metric cards and action buttons | Screenshot |
| 4.7 | Document Editor: Split-Pane View | 4 | Screenshot showing editor and live preview panes | Screenshot |
| 5.1 | Lite Research Pipeline Flowchart | 5 | Start → Cache → Tavily → Extract → Groq → End | draw.io / Mermaid |
| 5.2 | Deep Research Pipeline Flowchart | 5 | Start → Questions → Answers → Plan → Execute → End | draw.io / Mermaid |
| 5.3 | Pro Research Pipeline Flowchart | 5 | Intake → Chips → Plan → Agent → Execute → Save → End | draw.io / Mermaid |
| 5.4 | Evidence Verification Workflow | 5 | Indexing phase → Querying phase (two swim lanes) | draw.io / Mermaid |
| 6.1 | Sequence Diagram: Pro Research API Lifecycle | 6 | Frontend → Flask → pro_research → Tavily → Groq → SQLite → UI | PlantUML |
| 6.2 | Hybrid Evidence Scoring Formula Diagram | 6 | Visual formula: 40% SequenceMatcher + 60% keyword overlap | draw.io |
| 7.1 | Browser Agent Agentic Loop State Diagram | 7 | Init → Navigate → Extract → Groq Action → Loop/Done | draw.io |
| 7.2 | Stealth Extraction Decision Tree | 7 | Standard vs Stealth fallback decision flowchart | draw.io |
| 8.1 | PDF Generation Pipeline | 8 | JSON → ReportLab → Title → Abstract → Sections → References → File | draw.io |
| 8.2 | PDF Document Structure Diagram | 8 | Visual layout of generated PDF pages | draw.io |
| 9.1 | Use Case Diagram | 9 | Researcher + Tavily API + Groq API interacting with system | PlantUML |
| 9.2 | Entity-Relationship Diagram | 9 | `research_sessions` table schema with all fields | draw.io |
| 9.3 | Data Flow Diagram Level 0 (Context) | 9 | Central system with 4 external entities | draw.io |

---

## 8.2 Each Figure — Detailed Specification

### Figure 3.1 — System Architecture: MVC Layered View
- **Chapter:** 3
- **Type:** Layered architecture diagram
- **Tool:** draw.io
- **Exact content to include:**
  - Box 1 (top): "Layer 1: Presentation (Frontend)" containing `index.html`, `editor.html`, `main.js`, `editor.js`
  - Box 2: "Layer 2: Application (Flask Backend)" containing `api_server.py`, `ResultCache`, `rate_limit_store`
  - Box 3: "Layer 3: Service Layer" containing `paper_fetch.py`, `pro_research.py`, `deep_research.py`, `rag_service.py`, `browser_agent.py`, `pdf_generator.py`, `scraper_service.py`
  - Box 4 (bottom): "Layer 4: Data & External" containing `paperpilot.db (SQLite)`, `ChromaDB (listed)`, `Groq API (Cloud)`, `Tavily API (Cloud)`, `output/ (File System)`
  - Arrows: vertical bidirectional arrows between each layer
  - Dashed border around Groq API and Tavily API (external cloud services)

### Figure 4.1 — App Navigation and User Flow
- **Chapter:** 4
- **Type:** Flowchart
- **Tool:** draw.io or Mermaid
- **Exact content:**
  - Start: `[index.html /]`
  - Decision: Mode selector (3 branches)
  - Branch 1: Lite → `POST /api/research` → Results View
  - Branch 2: Deep → Questions Modal → Answers → Plan → `POST /api/deep/execute` → Results View
  - Branch 3: Pro → Intake Form → Chips → Plan → Agent Terminal → `POST /api/pro/execute` → Results View
  - From Results View: 5 actions: Download PDF, Export JSON, Export MD, Copy, Open in Editor
  - "Open in Editor" → `sessionStorage` transfer → `[editor.html /editor]`
  - In editor: Templates, Edit, Export MD, Export PDF

### Figure 5.1 — Lite Research Pipeline Flowchart
- **Exact steps from `paper_fetch.py`:**
  1. `START` → Receive topic
  2. Diamond: "In LRU Cache?" (SHA256 key check)
     - YES → Return cached report → `END`
     - NO → Continue
  3. `TavilyClient.search()` × 3 (Academic, Wiki, Articles)
  4. `TavilyClient.extract()` on found URLs
  5. Fallback: if extract fails → use snippet
  6. Build prompt (system + user with all content)
  7. `Groq.chat.completions.create()` (JSON mode, llama-3.3-70b-versatile)
  8. `cache.put(topic, report)`
  9. Return JSON → `END`

### Figure 5.4 — Evidence Verification Workflow
- **Exact content from `rag_service.py`:**
  - **Phase 1: Indexing** (triggered during research execution):
    - Extracted source text → `_chunk_text()` (3 sentences/chunk) → In-memory `_sessions[session_id]`
  - **Phase 2: Querying** (triggered by user clicking sentence in UI):
    - User clicks sentence → `POST /api/evidence {sentence, session_id}`
    - `query_evidence()` → encode query → For each chunk: SequenceMatcher (40%) + Keyword (60%) → filter >= 25% → return top 3

### Figure 6.1 — Sequence Diagram: Pro Research API Lifecycle
- **Exact lifelines (left to right):** `User Browser`, `Flask (api_server.py)`, `pro_research.py`, `Tavily API`, `Groq API`, `SQLite (database.py)`
- **Exact message sequence:**
  1. User → Flask: `POST /api/pro/execute {context, plan, agent_findings}`
  2. Flask → pro_research: `execute_pro_research(context, plan, agent_findings)`
  3. pro_research → Tavily: `search(section.query)` × N sections
  4. Tavily → pro_research: URL list + snippets
  5. pro_research → Tavily: `extract(urls)`
  6. Tavily → pro_research: full HTML/text
  7. pro_research → Groq: `chat.completions.create()` with aggregated context
  8. Groq → pro_research: JSON report
  9. pro_research → Flask: return report dict
  10. Flask → SQLite: `save_session(session_id, topic, report, mode='pro')`
  11. Flask → User: JSON response `200 OK`

### Figure 6.2 — Hybrid Evidence Scoring Formula
- **Exact formula from `rag_service.py` line 169:**
  - Visual equation: `Score = (SequenceMatcher_ratio × 0.4) + (Keyword_overlap_ratio × 0.6)`
  - Threshold: Score × 100 >= 25 to be included in results
  - Show: Query sentence → Method 1 (SequenceMatcher) → Method 2 (Keyword overlap) → Combine → Filter 25% → Top 3 results

### Figure 7.1 — Browser Agent State Diagram
- **Exact states from `browser_agent.py`:**
  - `[Init]` → `start_agent()` → session_id generated → daemon thread spawned
  - `[Browsing]` → `browser_use.Agent.run()` → Playwright navigates Google Scholar
  - `[Step N]` → `_make_step_callback()` fires → `push_event('step')` → SSE queue
  - `[Processing]` → Extract `final_result()` from agent output
  - Decision: "JSON in result?"
    - YES → parse `findings[]`
    - NO → use raw text as `overall_summary`
  - `[Complete]` → `push_event('complete')` → `push_event('done')` → loop ends
  - `[Error]` → `push_event('error')` → `push_event('done')`
  - Max iterations: 15 steps, Max timeout: 120 seconds

### Figure 8.1 — PDF Generation Pipeline
- **Exact steps from `pdf_generator.py`:**
  1. `generate_pdf(report_input, enhance=True)` called
  2. If `enhance=True`: `enhance_content_academic()` → Groq call (temp=0.3, max_tokens=4096) → enhanced JSON
  3. `register_fonts()` → check `C:\Windows\Fonts\times.ttf` → register or use fallback
  4. `build_styles(font_family)` → create 14 named paragraph styles
  5. `build_pdf_content(report, styles, font_family)` → returns list of Flowable objects:
     - Title Page (Spacer → Title → HR → Subtitle → Date → Source count → Abstract)
     - PageBreak
     - Table of Contents (section titles + key point sub-entries)
     - PageBreak
     - Body sections (Heading → Paragraphs → "X.1 Key Findings" bullets)
     - Conclusion section
     - References (formatted with hyperlinks)
     - Source Summary Table (2-column styled table)
  6. `SimpleDocTemplate.build(story, onFirstPage=HeaderFooter, onLaterPages=HeaderFooter)`
  7. Save PDF to `output/{topic_slug}_report.pdf`
  8. Return file path → `api_server.py` reads bytes → base64 encode → return to client

### Figure 9.2 — Entity-Relationship Diagram
- **Exact fields from `database.py` lines 29-43:**
  - Table: `research_sessions`
  - PK: `id (INTEGER, AUTOINCREMENT)`
  - `session_id (VARCHAR 32, UNIQUE, INDEX)`
  - `topic (VARCHAR 300, NOT NULL)`
  - `mode (VARCHAR 10, DEFAULT 'lite')`
  - `config_json (TEXT, DEFAULT '{}')`
  - `report_json (TEXT, NULLABLE)`
  - `total_sources (INTEGER, DEFAULT 0)`
  - `elapsed_seconds (FLOAT, DEFAULT 0)`
  - `created_at (DATETIME, DEFAULT UTC_NOW)`
  - **No foreign keys. No related tables.**

---

## 8.3 Figure Creation Instructions

### Using draw.io (app.diagrams.net):
1. Go to https://app.diagrams.net
2. Choose blank diagram
3. Use shapes: rounded rectangles for processes, diamonds for decisions, cylinders for databases, clouds for external APIs
4. Export: File → Export As → PNG → 300 DPI
5. Save as: `Figure_XX_[name].png`

### Using Mermaid (mermaid.live):
1. Go to https://mermaid.live
2. Paste Mermaid code (generated in `Diagram_Master_Prompts.md`)
3. Click PNG download
4. Save as: `Figure_XX_[name].png`

### Using PlantUML (plantuml.com/plantuml):
1. Go to https://www.plantuml.com/plantuml/uml/
2. Paste PlantUML code
3. Right-click image → Save image as PNG
4. Save as: `Figure_XX_[name].png`

### Screenshots (for Screens 4.2-4.7):
1. Run `python api_server.py` to start server
2. Open http://localhost:5000 in browser
3. Navigate to each screen/state
4. Use browser DevTools to set viewport to 1280×800
5. Press `Ctrl+Shift+P` → "Capture screenshot"
6. Save as: `Figure_4X_[screenname].png`
