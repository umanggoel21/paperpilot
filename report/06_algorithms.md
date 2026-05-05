# File 6: Algorithms and Core Logic
# Source: Extracted directly from PaperPilot codebase — no assumptions made.

---

## Algorithm 1: LRU Cache with SHA256 Keying
**Found in:** `api_server.py` — `ResultCache` class, lines 113-179
**Purpose:** Avoid redundant API calls by caching research results for 24 hours

### Mathematical formula:
- Key = `SHA256(topic.strip().lower())[:16]`
- Eviction: LRU via `OrderedDict.popitem(last=False)` when `len >= 50`

```python
def _key(self, topic):
    normalized = topic.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
```

### Constants:
- `max_size = 50`, `ttl = 86400` seconds (24 hours)

---

## Algorithm 2: Hybrid Evidence Matching (Fuzzy + Keyword)
**Found in:** `rag_service.py` — `query_evidence()`, lines 126-193
**Purpose:** Find source paragraphs that best match an AI-generated claim

### Mathematical formula:
```
similarity_score = (SequenceMatcher_ratio x 0.4 + keyword_overlap_ratio x 0.6) x 100
```

### Steps:
1. Normalize query to lowercase
2. Extract keywords (3+ char words, exclude 25 stop words)
3. For each indexed chunk:
   - Method 1: `SequenceMatcher(None, query, chunk).ratio()` -> seq_score (40% weight)
   - Method 2: `|query_words AND chunk_words| / |query_words|` -> overlap (60% weight)
   - Combined score = weighted sum x 100
4. Sort descending, filter where score >= 25%, return top 3

```python
combined = (seq_score * 0.4) + (overlap * 0.6)
similarity = round(combined * 100, 1)
results = [s for s in scored[:top_k] if s["similarity_score"] >= 25]
```

### Edge cases handled:
- Empty session chunks: returns `[]`
- Empty query_words: overlap = 0 (avoids ZeroDivisionError)
- Below 25% threshold: filtered out

---

## Algorithm 3: Text Chunking for Evidence Indexing
**Found in:** `rag_service.py` — `_chunk_text()`, lines 44-73

### Steps:
1. Clean whitespace: `re.sub(r'\s+', ' ', text)`
2. Split sentences: `re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)`
3. Filter: sentences >= 20 chars
4. Group: sliding window of 3 sentences each
5. Filter: chunks >= 40 chars
6. Pre-compute: `text_lower` for search performance

### Constants:
- `chunk_size = 3` sentences, min sentence = 20 chars, min chunk = 40 chars

---

## Algorithm 4: Stealth Extraction Strategy (Fallback Chain)
**Found in:** `scraper_service.py` — `extract()`, lines 221-268

### Decision tree:
```
URL -> Is domain in STEALTH_PRIORITY_DOMAINS (8 sites)?
  YES -> _stealth_extract() directly
  NO  -> _standard_extract() first
           SUCCESS? -> return (method_used="standard")
           FAIL?   -> _stealth_extract()
                        SUCCESS? -> return (method_used="stealth")
                        FAIL?   -> return (success=False, method_used="failed")
```

### Bot detection patterns checked (8):
`"cf-browser-verification"`, `"challenge-platform"`, `"captcha"`, `"recaptcha"`, `"hCaptcha"`, `"cf-turnstile"`, `"Access Denied"`, `"bot detection"`

### Blocked HTTP codes: `[403, 429, 503]`

---

## Algorithm 5: Groq Retry with Exponential Backoff
**Found in:** `pro_research.py` lines 47-71, `deep_research.py` lines 69-96

### Wait times (seconds):
- Attempt 0: `(2^0) x 5 = 5s`
- Attempt 1: `(2^1) x 5 = 10s`
- Attempt 2: `(2^2) x 5 = 20s`

```python
wait = (2 ** attempt) * 5
time.sleep(wait)
```

- Triggers only on: `"rate_limit"` or `"429"` in error string
- All other errors: re-raised immediately
- After 3 failures: `raise Exception("Groq rate limit exceeded after retries.")`

---

## Algorithm 6: SSE Browser Agent Event Streaming
**Found in:** `browser_agent.py` — `get_event_stream()`, lines 305-334

### Steps:
1. Loop up to `max_timeout=120` iterations (1 per second)
2. `q.get(timeout=1)` blocking call
3. On event: reset counter, yield `"event: {type}\ndata: {json}\n\n"`
4. On terminal event `done`: break loop
5. On empty queue: `timeout_counter += 1`, yield `": keepalive\n\n"`
6. After loop: call `cleanup_session()`

---

## Algorithm 7: PDF Citation Superscript Formatting
**Found in:** `pdf_generator.py` — `_format_citation_refs()`, lines 455-465

```python
def replace_ref(match):
    ref = match.group(0)
    return f'<font color="#0f4c75"><super>{_escape_xml(ref)}</super></font>'

return re.sub(r'\[\d+\]', replace_ref, text)
```

- Converts `[1]`, `[2]` inline citations to ReportLab XML superscript spans in link color `#0f4c75`
