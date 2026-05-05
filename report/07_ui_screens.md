# File 7: UI Screens and Components
# Source: Extracted from frontend/index.html, frontend/editor.html, frontend/main.js, frontend/editor.js

---

## 7.1 Screen Inventory

| Screen No. | Screen Name | File | Route | Purpose |
|---|---|---|---|---|
| 1 | Main Research Hub | `frontend/index.html` + `main.js` | `/` | Search, run research in all 3 modes, view results |
| 2 | Pro Document Editor | `frontend/editor.html` + `editor.js` | `/editor` | Markdown editing, templates, live preview, export |

**No other screen/page files exist in the codebase.**

---

## 7.2 Navigation Flow

**Source:** `editor.js` lines 476-487, `main.js` (action buttons in results view)

```
[Screen 1: index.html (/)]
  --> User searches topic
  --> Results appear below (same page, no redirect)
  --> Click "Open in Editor" button in results
       --> sessionStorage.setItem('paperpilot_editor_report', JSON.stringify(report))
       --> window.location.href = '/editor'
  --> [Screen 2: editor.html (/editor)]
       --> loadReportIntoEditor() reads from sessionStorage
       --> Renders report as Markdown in textarea

[Screen 2: editor.html (/editor)]
  --> Click back arrow
  --> window.location.href = '/'
  --> [Screen 1: index.html (/)]
```

**Inter-screen data transfer:** via `sessionStorage` key `'paperpilot_editor_report'` (JSON string)

---

## 7.3 Screen 1 — Main Research Hub (`index.html` + `main.js`)

**File:** `d:\paperpilot\frontend\index.html`, `d:\paperpilot\frontend\main.js`
**Route:** `/`
**State management:** Global JavaScript variables + DOM manipulation (no framework)

### UI Sections found in `index.html`:

#### Section A: Hero / Search Bar
| Component | Type | Purpose | Data source |
|---|---|---|---|
| Search input `#search-input` | Text input | User types research topic | User input |
| "Research" submit button | Button | Triggers Lite research | Calls `handleResearch()` in main.js |
| Lite/Deep/Pro toggle | Radio buttons | Select research mode | Controls which API endpoint is called |
| "Try:" suggestion chips | Clickable spans | Pre-fill search bar with example topics | Hardcoded in HTML |
| "Recent:" history chips | Dynamically generated spans | Show past topics from API | `GET /api/history` |

#### Section B: Pro Research Modal (3-Step Wizard)
| Component | Type | Purpose |
|---|---|---|
| Step 1: Intake Form | 6-question form | Collect depth, tone, length, focus, subtopics, context |
| AI-generated subtopic chips | Clickable chips | `POST /api/pro/chips` response |
| Step 2: Research Plan | Read-only display | Shows AI-generated plan from `POST /api/pro/plan` |
| Step 3: Live Agent Terminal | Terminal-style div | Streams SSE events from `GET /api/agent/stream/<id>` |
| macOS-style terminal dots (red/yellow/green) | Decorative spans | Visual UI element |
| Phase progress bar | 3-phase indicator | Shows: Browser Agent → Deep Search → AI Synthesis |
| Stats bar (Steps/Pages/Findings) | Counter display | Shows agent metrics (currently hardcoded 0 per audit) |

#### Section C: Results View
| Component | Type | Purpose | Data source |
|---|---|---|---|
| Metric cards | Display cards | Sources, Papers, Wiki, Articles, Time, Quality | Report JSON fields |
| Action bar | Button group | Download PDF, Export JSON, Export Markdown, Copy Summary, Open in Editor | Calls API + triggers downloads |
| Collapsible sections | Accordion | Show report sections | `report.sections[]` |
| Evidence verify button | Per-sentence button | Calls `POST /api/evidence` | Fuzzy matching result |

### User Actions (from main.js):

| Action | Trigger | Function Called | Result |
|---|---|---|---|
| Lite Search | Click "Research" button | `handleResearch()` | `POST /api/research` |
| Deep Search | Select Deep mode + click | `startDeepResearch()` | `POST /api/deep/questions` → modal |
| Pro Search | Select Pro mode + click | Opens Pro modal | Multi-step wizard |
| Download PDF | Click "Download PDF" | `downloadPDF()` | `POST /api/pdf` → base64 download |
| Export JSON | Click "Export JSON" | `exportJSON()` | Creates blob download |
| Export Markdown | Click "Export Markdown" | `exportMarkdown()` | Creates blob download |
| Copy Summary | Click "Copy Summary" | `copySummary()` | `navigator.clipboard.writeText()` |
| Open in Editor | Click "Open in Editor" | Stores in sessionStorage + redirects | `window.location.href = '/editor'` |
| Verify Evidence | Click evidence button | `verifyEvidence(sentence, session_id)` | `POST /api/evidence` |
| History chip click | Click recent chip | Auto-fills search input | `document.getElementById('search-input').value = topic` |
| Start Browser Agent | Button in Pro modal | `startBrowserAgent()` | `POST /api/agent/start` + SSE stream |

---

## 7.4 Screen 2 — Pro Document Editor (`editor.html` + `editor.js`)

**File:** `d:\paperpilot\frontend\editor.html`, `d:\paperpilot\frontend\editor.js` (556 lines)
**Route:** `/editor`
**State management:** `localStorage` for draft persistence, `sessionStorage` for report loading

### UI Components (from `editor.js`):

| Component ID | Type | Purpose | Data source |
|---|---|---|---|
| `#editor-textarea` | Textarea | Markdown input area | User typing or loaded report |
| `#editor-preview` | Div | Live HTML preview | Rendered from textarea content |
| `#editor-divider` | Draggable div | Resize panes | Mouse drag events |
| `#editor-pane-left` | Div | Left pane (editor) | Flex layout |
| `#editor-pane-right` | Div | Right pane (preview) | Flex layout |
| `#template-select` | Dropdown/Select | Choose document template | 4 templates: ieee, apa, litreview, executive |
| `#btn-export-md` | Button | Export Markdown | Creates Blob download |
| `#btn-export-pdf` | Button | Export PDF | `POST /api/pdf` with editor content |
| `#word-count` | Span | Shows word count | Computed from textarea content |
| `#save-status` | Span | Shows "Saved" / "Unsaved changes" | Auto-save state |
| `#toast-container` | Div | Notification toasts | Dynamic DOM insertion |

### Document Templates (`TEMPLATES` object in `editor.js` lines 231-361):

| Template Key | Name | Sections |
|---|---|---|
| `ieee` | IEEE Research Paper | Abstract, Introduction, Related Work, Methodology, Results, Discussion, Conclusion, References |
| `apa` | APA Research Report | Abstract, Keywords, Introduction, Literature Review, Method (Participants, Materials, Procedure), Results, Discussion, References |
| `litreview` | Literature Review | Introduction, Background, Thematic Analysis (3 sub-themes), Critical Evaluation, Conclusion and Future Directions, References |
| `executive` | Executive Brief | Executive Summary, Key Findings, Analysis, Recommendations, Appendix |

### `reportToMarkdown(report)` function (editor.js lines 491-533):
Converts JSON report to Markdown:
1. Title: `# {report.topic}`
2. Meta: `*Generated: {date}*, *Sources: {count}*`
3. Abstract: `## Abstract` from `report.enhanced_abstract || report.executive_summary`
4. Sections: `## {i+1}. {section.title}` + content + `**Key Findings:**` bullets
5. Takeaways: numbered list
6. Conclusion: `## Conclusion`
7. References: `[ref_id] Title — URL`

### Auto-save behavior (editor.js lines 76-97):
- `setInterval(() => localStorage.setItem('paperpilot_editor_draft', textarea.value), 30000)` (every 30 seconds)
- `window.addEventListener('beforeunload')` → saves on tab close
- `window.addEventListener('beforeunload')` → shows browser "unsaved changes" warning if `hasUnsavedChanges`
- On page load: restores from `localStorage.getItem('paperpilot_editor_draft')` if no sessionStorage report

### Split-pane resize (editor.js lines 187-224):
- `mousedown` on divider → sets `isDragging = true`
- `mousemove` → calculates `ratio = offset / totalWidth`, clamped to `[0.2, 0.8]`
- Sets `leftPane.style.flex = ratio * 100%`, `rightPane.style.flex = (1-ratio-0.01) * 100%`

### Markdown rendering (`renderPreview()`, editor.js lines 112-172):
Custom lightweight renderer (no external library):
- Code blocks: triple-backtick → `<pre><code>`
- Headers: `# / ## / ###` → `<h1>/<h2>/<h3>`
- Bold/Italic: `*** / ** / *` → `<strong><em> / <strong> / <em>`
- Blockquotes: `>` → `<blockquote>`
- Horizontal rules: `---` → `<hr>`
- Unordered lists: `* / -` → `<li>` wrapped in `<ul>`
- Links: `[text](url)` → `<a href="url" target="_blank" rel="noopener">`
- Paragraphs: double newline → `</p><p>`
- Debounced: 150ms delay after user stops typing (line 52)
