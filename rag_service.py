"""
PaperPilot — Evidence Matching Service (Fuzzy Text Matching)
=============================================================
Lightweight source verification engine using Python's built-in
difflib.SequenceMatcher. Zero external dependencies.

When the AI writes a sentence, this module finds the exact paragraph
from the original scraped sources that matches it most closely.

Usage:
    from rag_service import RAGService
    rag = RAGService()
    rag.index_sources(sources, session_id="abc123")
    evidence = rag.query_evidence("some AI claim", session_id="abc123")
"""

import re
import logging
import time
from difflib import SequenceMatcher
from typing import List, Dict, Optional

logger = logging.getLogger('paperpilot.evidence')

# In-memory store: { session_id: [list of paragraph dicts] }
_sessions: Dict[str, List[Dict]] = {}


class RAGService:
    """
    Lightweight evidence matcher using fuzzy text comparison.
    No ChromaDB, no PyTorch, no ONNX — pure Python.
    """

    def __init__(self, persist_dir: str = None):
        self.available = True
        self.init_error = None
        logger.info("Evidence Matching Service initialized (fuzzy text matching)")

    # ──────────────────────────────────────────
    # Text Chunking
    # ──────────────────────────────────────────

    def _chunk_text(self, text: str, source_url: str, source_title: str,
                    source_type: str = "unknown", chunk_size: int = 3) -> List[Dict]:
        """Split raw text into chunks of N sentences."""
        if not text or not text.strip():
            return []

        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) >= 20]

        if not sentences:
            return []

        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunk_text = " ".join(sentences[i:i + chunk_size])
            if len(chunk_text) < 40:
                continue
            chunks.append({
                "text": chunk_text,
                "text_lower": chunk_text.lower(),  # pre-compute for speed
                "source_url": source_url,
                "source_title": source_title,
                "source_type": source_type,
            })

        return chunks

    # ──────────────────────────────────────────
    # Indexing (Store in memory)
    # ──────────────────────────────────────────

    def index_sources(self, sources: List[Dict], session_id: str) -> Dict:
        """
        Chunk all source texts and store in memory for this session.
        """
        start_time = time.time()

        all_chunks = []
        sources_indexed = 0

        for source in sources:
            content = source.get("full_content", "") or source.get("snippet", "")
            if not content or len(content.strip()) < 50:
                continue

            chunks = self._chunk_text(
                text=content,
                source_url=source.get("url", ""),
                source_title=source.get("title", "Untitled"),
                source_type=source.get("source_type", "unknown"),
            )

            if chunks:
                all_chunks.extend(chunks)
                sources_indexed += 1

        # Store in memory
        _sessions[session_id] = all_chunks

        total_words = sum(len(c["text"].split()) for c in all_chunks)
        elapsed = round(time.time() - start_time, 3)

        logger.info(
            f"Indexed {len(all_chunks)} paragraphs from {sources_indexed} sources "
            f"({total_words} words) in {elapsed}s"
        )

        return {
            "total_chunks": len(all_chunks),
            "total_words": total_words,
            "sources_indexed": sources_indexed,
            "time_taken": elapsed,
        }

    # ──────────────────────────────────────────
    # Evidence Matching (Fuzzy)
    # ──────────────────────────────────────────

    def query_evidence(self, sentence: str, session_id: str, top_k: int = 3) -> List[Dict]:
        """
        Find source paragraphs most similar to the given AI sentence.
        Uses a HYBRID approach:
          1. difflib.SequenceMatcher (common subsequences)
          2. Keyword overlap ratio (shared important words)
        Combined score gives much better accuracy than either alone.
        """
        chunks = _sessions.get(session_id, [])
        if not chunks:
            return []

        sentence_lower = sentence.lower().strip()

        # Extract meaningful keywords (3+ chars, skip common words)
        stop_words = {'the', 'and', 'for', 'are', 'was', 'were', 'has', 'have',
                      'that', 'this', 'with', 'from', 'which', 'can', 'but',
                      'not', 'all', 'also', 'its', 'they', 'their', 'been',
                      'will', 'would', 'could', 'into', 'than', 'more', 'such',
                      'when', 'what', 'how', 'each', 'some', 'these', 'those'}
        query_words = set(
            w for w in re.findall(r'[a-z]{3,}', sentence_lower)
            if w not in stop_words
        )

        scored = []
        for chunk in chunks:
            # Method 1: SequenceMatcher (finds common character sequences)
            seq_score = SequenceMatcher(
                None, sentence_lower, chunk["text_lower"]
            ).ratio()

            # Method 2: Keyword overlap (how many important words match)
            chunk_words = set(
                w for w in re.findall(r'[a-z]{3,}', chunk["text_lower"])
                if w not in stop_words
            )
            if query_words:
                overlap = len(query_words & chunk_words) / len(query_words)
            else:
                overlap = 0

            # Hybrid score: 40% sequence matching + 60% keyword overlap
            combined = (seq_score * 0.4) + (overlap * 0.6)
            similarity = round(combined * 100, 1)

            scored.append({
                "text": chunk["text"],
                "source_url": chunk["source_url"],
                "source_title": chunk["source_title"],
                "source_type": chunk["source_type"],
                "similarity_score": similarity,
            })

        # Sort by similarity (highest first)
        scored.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Return top matches (only those above 25% threshold)
        results = [s for s in scored[:top_k] if s["similarity_score"] >= 25]

        if results:
            logger.info(
                f"Evidence match: top score {results[0]['similarity_score']}% "
                f"from '{results[0]['source_title'][:40]}'"
            )
        else:
            logger.info(f"Evidence match: no strong match found (all below 25%)")

        return results

    # ──────────────────────────────────────────
    # Session Stats
    # ──────────────────────────────────────────

    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """Return stats for a session's indexed data."""
        chunks = _sessions.get(session_id, [])
        if not chunks:
            return None
        return {
            "total_chunks": len(chunks),
            "sources": len(set(c["source_url"] for c in chunks)),
        }
