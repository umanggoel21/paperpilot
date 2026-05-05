"""
PaperPilot — Deep Research Module
===================================
Enhanced research pipeline with conversational configuration.

Three-phase flow:
  1. generate_questions() — AI generates 3 topic-specific questions
  2. generate_plan()      — AI creates section-by-section plan
  3. execute_deep_research() — Enhanced pipeline with user context

Usage:
    from deep_research import generate_questions, generate_plan, execute_deep_research
"""

import os
import json
import time
import re
import logging
from datetime import datetime, timezone

from clients import tavily_client, groq_client

logger = logging.getLogger('paperpilot.deep')
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Source limits per config tier (per category)
SOURCE_LIMITS = {
    3: {"papers": 2, "wiki": 1, "articles": 2},
    5: {"papers": 3, "wiki": 1, "articles": 3},
    7: {"papers": 4, "wiki": 2, "articles": 4},
}

# Token limits per report length
TOKEN_LIMITS = {
    "short":  2048,
    "medium": 4096,
    "long":   6000,
}

# Content extraction limits per length
EXTRACT_LIMITS = {
    "short":  800,
    "medium": 1500,
    "long":   2500,
}

# Academic domains for targeted searching
ACADEMIC_DOMAINS = [
    "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "researchgate.net",
    "ieee.org", "sciencedirect.com", "semanticscholar.org",
    "scholar.google.com", "ncbi.nlm.nih.gov", "nature.com", "springer.com",
]

WIKI_DOMAINS = ["en.wikipedia.org"]


# ──────────────────────────────────────────────
# UTILITY: Groq call with retry
# ──────────────────────────────────────────────

def _groq_call(groq_client, messages, max_tokens=1024, temperature=0.4, json_mode=True, retries=3):
    """Call Groq with retry + exponential backoff for rate limits.
    
    HTTP 413 (Payload Too Large) is NOT retried — it's re-raised
    so callers can truncate content. Only 429 triggers backoff.
    """
    for attempt in range(retries):
        try:
            kwargs = {
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = groq_client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()

        except Exception as e:
            error_str = str(e).lower()
            # 413 = payload too large — don't retry, raise immediately
            if "413" in error_str or "payload too large" in error_str or "request too large" in error_str:
                logger.error(f"Groq payload too large (413). Content must be truncated.")
                raise
            # 429 = rate limit — retry with backoff
            if "rate_limit" in error_str or "429" in error_str:
                wait = (2 ** attempt) * 5  # 5s, 10s, 20s
                logger.warning(f"Groq rate limit hit, waiting {wait}s (attempt {attempt+1}/{retries})")
                time.sleep(wait)
            else:
                raise
    raise Exception("Groq rate limit exceeded after retries. Try again later.")


# ──────────────────────────────────────────────
# PHASE 1: Generate Personalized Questions
# ──────────────────────────────────────────────

def generate_questions(topic: str, config: dict) -> dict:
    """
    Generate 3 personalized questions about the user's topic.

    Args:
        topic: Research topic
        config: {sources: 3|5|7, length: short|medium|long, tone: simple|professional|friendly, focus: overview|technical|practical}

    Returns:
        {"questions": [{"id": 1, "question": "...", "placeholder": "..."}]}
    """
    # clients.py validates API keys at import time

    prompt = f"""You are a research assistant helping a user customize their research report.

Topic: "{topic}"
Config: Sources={config.get('sources', 5)}, Length={config.get('length', 'medium')}, Tone={config.get('tone', 'professional')}, Focus={config.get('focus', 'overview')}

Generate exactly 3 short, smart questions that will help you produce a BETTER, more targeted research report. The questions should:
1. Help narrow the scope (e.g., which sub-area or time period)
2. Clarify the user's purpose (e.g., academic paper, presentation, learning)
3. Identify specific interests (e.g., particular aspects, controversies, applications)

Output ONLY valid JSON:
{{
  "questions": [
    {{"id": 1, "question": "Your question here?", "placeholder": "Example answer..."}},
    {{"id": 2, "question": "Your question here?", "placeholder": "Example answer..."}},
    {{"id": 3, "question": "Your question here?", "placeholder": "Example answer..."}}
  ]
}}"""

    raw = _groq_call(
        groq_client,
        [{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.5,
    )

    result = json.loads(raw)
    logger.info(f"Generated {len(result.get('questions', []))} questions for '{topic}'")
    return result


# ──────────────────────────────────────────────
# PHASE 2: Generate Research Plan
# ──────────────────────────────────────────────

def generate_plan(topic: str, config: dict, answers: list) -> dict:
    """
    Generate a section-by-section research plan based on topic + config + user answers.

    Args:
        topic: Research topic
        config: User's configuration choices
        answers: List of {"question": "...", "answer": "..."} from Phase 1

    Returns:
        {"plan": [{"title": "...", "description": "..."}], "estimated_time": "..."}
    """
    # clients.py validates API keys at import time

    length = config.get('length', 'medium')
    section_count = {"short": "3-4", "medium": "4-6", "long": "6-8"}[length]

    answers_text = "\n".join([f"Q: {a.get('question', 'N/A')}\nA: {a.get('answer', 'N/A')}" for a in answers])

    prompt = f"""You are a research planner. Based on the topic, user preferences, and their answers to personalized questions, create a research report plan.

Topic: "{topic}"
Report Length: {length} ({section_count} sections)
Tone: {config.get('tone', 'professional')}
Focus: {config.get('focus', 'overview')}
Sources: {config.get('sources', 5)} per category

User's Answers:
{answers_text}

Create a plan with {section_count} sections. Each section should have a title and a 1-sentence description of what it will cover.

Output ONLY valid JSON:
{{
  "plan": [
    {{"title": "Section Title", "description": "What this section will cover"}},
    {{"title": "Section Title", "description": "What this section will cover"}}
  ],
  "research_focus": "A 1-sentence summary of the research direction based on user answers",
  "estimated_time": "30-60 seconds"
}}"""

    raw = _groq_call(
        groq_client,
        [{"role": "user", "content": prompt}],
        max_tokens=768,
        temperature=0.4,
    )

    result = json.loads(raw)
    logger.info(f"Generated plan with {len(result.get('plan', []))} sections for '{topic}'")
    return result


# ──────────────────────────────────────────────
# PHASE 3: Execute Deep Research
# ──────────────────────────────────────────────

def execute_deep_research(topic: str, config: dict, answers: list, plan: list) -> dict:
    """
    Run the full deep research pipeline with enhanced configuration.

    Args:
        topic: Research topic
        config: User's configuration
        answers: User's Q&A answers
        plan: Approved section plan

    Returns:
        Full research report dict (same structure as paper_fetch.fetch_research)
    """
    # clients.py validates API keys at import time
    tavily = tavily_client

    source_count = config.get('sources', 5)
    length = config.get('length', 'medium')
    tone = config.get('tone', 'professional')
    focus = config.get('focus', 'overview')

    limits = SOURCE_LIMITS.get(source_count, SOURCE_LIMITS[5])
    max_tokens = TOKEN_LIMITS.get(length, 4096)
    extract_limit = EXTRACT_LIMITS.get(length, 1500)

    logger.info(f"Deep research: '{topic}' | sources={source_count} length={length} tone={tone}")

    # ── STEP 1: Enhanced Search ──
    sources = {"research_papers": [], "wikipedia": [], "articles_blogs": []}

    # Build enhanced search queries using user answers
    answers_context = " ".join([a.get('answer', '') for a in answers if a.get('answer')])
    enhanced_query = f"{topic} {answers_context[:100]}" if answers_context else topic

    try:
        academic = tavily.search(
            query=f"{enhanced_query} research paper study findings",
            search_depth="advanced",
            max_results=limits["papers"],
            include_domains=ACADEMIC_DOMAINS,
        )
        sources["research_papers"] = [
            {"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": r.get("content", ""), "score": r.get("score", 0),
             "source_type": "research_paper"}
            for r in academic.get("results", [])
        ]
    except Exception as e:
        logger.warning(f"Academic search error: {e}")

    try:
        wiki = tavily.search(
            query=topic,
            search_depth="advanced",
            max_results=limits["wiki"],
            include_domains=WIKI_DOMAINS,
        )
        sources["wikipedia"] = [
            {"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": r.get("content", ""), "score": r.get("score", 0),
             "source_type": "wikipedia"}
            for r in wiki.get("results", [])
        ]
    except Exception as e:
        logger.warning(f"Wiki search error: {e}")

    try:
        blogs = tavily.search(
            query=f"{enhanced_query} explained analysis overview",
            search_depth="advanced",
            max_results=limits["articles"],
            exclude_domains=ACADEMIC_DOMAINS + WIKI_DOMAINS,
        )
        sources["articles_blogs"] = [
            {"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": r.get("content", ""), "score": r.get("score", 0),
             "source_type": "article_blog"}
            for r in blogs.get("results", [])
        ]
    except Exception as e:
        logger.warning(f"Blog search error: {e}")

    # ── STEP 2: Extract Content ──
    all_sources = sources["research_papers"] + sources["wikipedia"] + sources["articles_blogs"]
    urls = [s["url"] for s in all_sources if s.get("url")]

    if urls:
        try:
            extracted = tavily.extract(urls=urls)
            extracted_map = {item.get("url", ""): item.get("raw_content", "") for item in extracted.get("results", [])}

            for source in all_sources:
                url = source.get("url", "")
                if url in extracted_map and extracted_map[url]:
                    source["full_content"] = extracted_map[url][:extract_limit]
                else:
                    source["full_content"] = source.get("snippet", "")
        except Exception as e:
            logger.warning(f"Extract error: {e}")
            for source in all_sources:
                source["full_content"] = source.get("snippet", "")

    # ── STEP 3: Synthesize with Enhanced Prompt ──
    idx = 1
    numbered_sources = []
    for category in ["research_papers", "wikipedia", "articles_blogs"]:
        for s in sources[category]:
            numbered_sources.append({**s, "ref_id": idx})
            idx += 1

    if not numbered_sources:
        return {
            "topic": topic, "error": "No sources found.",
            "sections": [], "sources_used": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "deep_research": True,
        }

    source_context = ""
    for s in numbered_sources:
        content = s.get('full_content', s.get('snippet', ''))[:extract_limit]
        source_context += f"\n--- SOURCE [{s['ref_id']}] ---\nTitle: {s['title']}\nURL: {s['url']}\nType: {s['source_type']}\nContent:\n{content}\n"

    # Build the plan instruction
    plan_instruction = "\n".join([f"  {i+1}. {p['title']}: {p.get('description', '')}" for i, p in enumerate(plan)])

    # Build user context from Q&A
    qa_context = "\n".join([f"- {a.get('question', 'N/A')}: {a.get('answer', 'N/A')}" for a in answers])

    # Tone instructions
    tone_map = {
        "simple": "Use simple, everyday language. Avoid jargon. Explain concepts as if to a high school student.",
        "professional": "Use formal academic tone with precise terminology. Write as if for a peer-reviewed journal.",
        "friendly": "Use a conversational, engaging tone. Be informative but approachable, like explaining to a curious friend.",
    }
    tone_instruction = tone_map.get(tone, tone_map["professional"])

    system_prompt = f"""You are a research synthesis AI producing a deep, customized research report.

TONE: {tone_instruction}

REPORT STRUCTURE — Follow this exact section plan:
{plan_instruction}

USER CONTEXT — The user provided these details about what they want:
{qa_context}

Output MUST be valid JSON with this structure:
{{
  "topic": "the research topic",
  "executive_summary": "A comprehensive summary of key findings (3-5 sentences)",
  "sections": [
    {{
      "title": "Section Title (from the plan above)",
      "content": "Detailed content synthesized from sources with inline citations [1], [2] etc.",
      "key_points": ["bullet point 1", "bullet point 2"]
    }}
  ],
  "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"],
  "conclusion": "A concluding paragraph summarizing the findings and their implications",
  "sources_used": [
    {{
      "ref_id": 1,
      "title": "Source title",
      "url": "source url",
      "source_type": "research_paper|wikipedia|article_blog",
      "relevance": "Why this source is relevant"
    }}
  ]
}}

Rules:
1. Follow the section plan EXACTLY — use those titles in that order.
2. Synthesize across sources, don't just copy. Combine insights.
3. ALWAYS cite sources using [ref_id] notation inline.
4. Keep content factual. Don't fabricate.
5. Include ALL sources in sources_used.
6. Incorporate the user's specific interests from the USER CONTEXT.
7. Output ONLY valid JSON."""

    user_prompt = f"""Research Topic: {topic}

Collected Sources:
{source_context}

Synthesize these sources into a deep research report following the plan. Output ONLY valid JSON."""

    try:
        raw = _groq_call(
            groq_client,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
    except Exception as e:
        if "413" in str(e).lower() or "too large" in str(e).lower() or "rate_limit_exceeded" in str(e).lower():
            logger.warning("Deep Research: Payload too large or TPM limit hit -- truncating sources heavily and retrying...")
            truncated_context = ""
            half_limit = 250  # Very strict truncation
            for s in numbered_sources:
                content = s.get('full_content', s.get('snippet', ''))[:half_limit]
                truncated_context += f"\n--- SOURCE [{s['ref_id']}] ---\nTitle: {s['title']}\nURL: {s['url']}\nContent:\n{content}\n"
            user_prompt_short = f"""Research Topic: {topic}

Collected Sources:
{truncated_context}

Synthesize these sources into a deep research report following the plan. Output ONLY valid JSON."""
            
            fallback_max_tokens = min(max_tokens, 1500)
            
            raw = _groq_call(
                groq_client,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt_short},
                ],
                max_tokens=fallback_max_tokens,
                temperature=0.3,
            )
        else:
            raise

    try:
        report = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Deep research JSON parse error: {e}")
        return {
            "topic": topic,
            "error": f"Failed to parse LLM response: {e}",
            "sections": [],
            "sources_used": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "deep_research": True,
        }

    # Ensure required keys
    report.setdefault("topic", topic)
    report.setdefault("executive_summary", "")
    report.setdefault("sections", [])
    report.setdefault("key_takeaways", [])
    report.setdefault("conclusion", "")
    report.setdefault("sources_used", [])

    # Add metadata
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["total_sources"] = len(numbered_sources)
    report["source_breakdown"] = {
        "research_papers": len(sources["research_papers"]),
        "wikipedia": len(sources["wikipedia"]),
        "articles_blogs": len(sources["articles_blogs"]),
    }
    report["deep_research"] = True
    report["config"] = config

    logger.info(f"Deep research complete for '{topic}': {len(report['sections'])} sections, {report['total_sources']} sources")

    return report
