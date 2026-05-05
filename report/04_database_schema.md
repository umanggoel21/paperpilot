# File 4: Database Schema
# Source: Extracted directly from database.py — no assumptions made.

---

## 4.1 Database System

| Property | Value | Source |
|---|---|---|
| Type | SQLite | `database.py` line 68: `'sqlite:///{DB_PATH}'` |
| ORM | SQLAlchemy via `Flask-SQLAlchemy` | `database.py` line 16: `from flask_sqlalchemy import SQLAlchemy` |
| Database file path | `d:\paperpilot\paperpilot.db` | `database.py` line 22: `DB_PATH = os.path.join(os.path.dirname(...), 'paperpilot.db')` |
| Auto-creation | Yes | `database.py` line 73: `db.create_all()` |
| Number of tables | 1 | Only `ResearchSession` model defined |

---

## 4.2 Complete Schema

### Table: `research_sessions`
**Source:** `database.py` lines 25-63 — `ResearchSession(db.Model)` class

| Field Name | SQLAlchemy Type | Python Type | Constraints | Description |
|---|---|---|---|---|
| `id` | `db.Integer` | `int` | PRIMARY KEY, AUTOINCREMENT | Auto-generated row identifier |
| `session_id` | `db.String(32)` | `str` | UNIQUE, NOT NULL, INDEX | SHA256 hash of topic (first 16 chars) generated in `api_server.py` |
| `topic` | `db.String(300)` | `str` | NOT NULL | Research topic string |
| `mode` | `db.String(10)` | `str` | DEFAULT `'lite'` | Research mode: `'lite'` or `'pro'` |
| `config_json` | `db.Text` | `str` | DEFAULT `'{}'` | JSON string of Pro intake form preferences |
| `report_json` | `db.Text` | `str` | NULLABLE | Full research report JSON (can be very large) |
| `total_sources` | `db.Integer` | `int` | DEFAULT `0` | Count of sources used, extracted from report |
| `elapsed_seconds` | `db.Float` | `float` | DEFAULT `0` | Research execution time in seconds |
| `created_at` | `db.DateTime` | `datetime` | DEFAULT UTC NOW | Row creation timestamp |

**No foreign keys. No secondary tables. Single flat table design.**

---

## 4.3 Session ID Generation (Critical Implementation Detail)

**Source:** `api_server.py` — `ResultCache._key()` method (lines 123-125)

```python
def _key(self, topic):
    normalized = topic.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
```

- Session IDs are **16-character SHA256 hex digest** of the normalized (stripped + lowercased) topic string
- **Consequence:** Searching the same topic twice will match the same `session_id` → `save_session()` will **UPDATE** the existing row (upsert behavior) rather than creating a new one
- This is confirmed in `database.py` lines 79-95: `existing = ResearchSession.query.filter_by(session_id=session_id).first(); if existing: existing.set_report(report)...`

---

## 4.4 ORM Queries Found in Code

**Source:** `database.py` lines 79-115

| Query | Location | Purpose |
|---|---|---|
| `ResearchSession.query.filter_by(session_id=session_id).first()` | `save_session()` line 79 | Upsert check |
| `ResearchSession.query.filter_by(session_id=session_id).first()` | `get_session()` line 101 | Retrieve by session ID |
| `ResearchSession.query.order_by(ResearchSession.created_at.desc()).limit(limit).all()` | `get_history()` line 109-113 | Get recent history sorted newest first |

---

## 4.5 Data Model Methods

### `ResearchSession.set_report(report_dict)`
- Serializes: `self.report_json = json.dumps(report_dict, ensure_ascii=False)`
- Extracts metadata: `self.total_sources = report_dict.get('total_sources', 0)`
- Extracts: `self.elapsed_seconds = report_dict.get('elapsed_seconds', 0)`

### `ResearchSession.get_report() -> dict | None`
- Deserializes: `json.loads(self.report_json)` → returns Python dict
- Returns `None` if `report_json` is empty/None

### `ResearchSession.to_history_dict() -> dict`
Returns:
```python
{
    'session_id': str,
    'topic': str,
    'mode': str,
    'total_sources': int,
    'elapsed_seconds': float,
    'created_at': str  # ISO format datetime
}
```

---

## 4.6 Report JSON Structure (stored in `report_json` column)

**Source:** Groq prompt schema enforced in `paper_fetch.py` and `pro_research.py`

This is the exact JSON structure stored as text in the `report_json` TEXT column:

```json
{
  "topic": "string",
  "executive_summary": "string (150-200 words)",
  "enhanced_abstract": "string (added by pdf_generator.py if enhance=True)",
  "sections": [
    {
      "title": "string",
      "content": "string (multi-paragraph)",
      "key_points": ["string", "string"]
    }
  ],
  "key_takeaways": ["string"],
  "conclusion": "string (added by pdf_generator.py if enhance=True)",
  "sources_used": [
    {
      "ref_id": "integer",
      "title": "string",
      "url": "string",
      "source_type": "research_paper | wikipedia | article_blog"
    }
  ],
  "source_breakdown": {
    "research_papers": 0,
    "wikipedia": 0,
    "articles_blogs": 0
  },
  "total_sources": "integer",
  "elapsed_seconds": "float",
  "generated_at": "ISO 8601 datetime string",
  "from_cache": "boolean",
  "session_id": "string (16-char hex)"
}
```
