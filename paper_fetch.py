"""
PaperPilot — Research Scraper & Synthesizer
============================================
Fetches information about a topic from research papers, Wikipedia,
articles & blogs using Tavily, then structures it with Groq LLM.

Usage:
    python paper_fetch.py "your research topic here"

Returns:
    - Pretty CLI output via Rich
    - Saves structured JSON to output/{topic}_report.json
    - Exposes `fetch_research(topic)` for import into other files
"""

import sys
import os
import json
import re
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from tavily import TavilyClient
from groq import Groq
from clients import tavily_client, groq_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

console = Console()
IS_TTY = sys.stdout.isatty()  # False when called from Flask; prevents UnicodeEncodeError on Windows

# Domain lists for targeted searching
ACADEMIC_DOMAINS = [
    "arxiv.org",
    "pubmed.ncbi.nlm.nih.gov",
    "researchgate.net",
    "ieee.org",
    "sciencedirect.com",
    "semanticscholar.org",
    "scholar.google.com",
    "ncbi.nlm.nih.gov",
    "nature.com",
    "springer.com",
]

WIKI_DOMAINS = [
    "en.wikipedia.org",
]


# ──────────────────────────────────────────────
# 1. SEARCH SOURCES  (Tavily Search API)
# ──────────────────────────────────────────────

def search_sources(topic: str, tavily: TavilyClient) -> dict:
    """
    Run 3 targeted Tavily searches:
      1) Academic / Research Papers
      2) Wikipedia
      3) General Articles & Blogs
    Returns a dict with categorized results.
    """
    results = {
        "research_papers": [],
        "wikipedia": [],
        "articles_blogs": [],
    }

    if IS_TTY:
        with Progress(
            TextColumn("[bold cyan]{task.description}"),
            console=console,
        ) as progress:

            # ── Search 1: Academic sources ──
            t1 = progress.add_task("Searching research papers & academic sources...", total=None)
            try:
                academic = tavily.search(
                    query=f"{topic} research paper study findings",
                    search_depth="advanced",
                    max_results=5,
                    include_domains=ACADEMIC_DOMAINS,
                )
                results["research_papers"] = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", ""),
                        "score": r.get("score", 0),
                        "source_type": "research_paper",
                    }
                    for r in academic.get("results", [])
                ]
            except Exception as e:
                console.print(f"[yellow]! Academic search warning: {e}[/]")
            progress.update(t1, completed=True)

            # ── Search 2: Wikipedia ──
            t2 = progress.add_task("Searching Wikipedia...", total=None)
            try:
                wiki = tavily.search(
                    query=f"{topic}",
                    search_depth="advanced",
                    max_results=3,
                    include_domains=WIKI_DOMAINS,
                )
                results["wikipedia"] = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", ""),
                        "score": r.get("score", 0),
                        "source_type": "wikipedia",
                    }
                    for r in wiki.get("results", [])
                ]
            except Exception as e:
                console.print(f"[yellow]! Wikipedia search warning: {e}[/]")
            progress.update(t2, completed=True)

            # ── Search 3: Articles & Blogs ──
            t3 = progress.add_task("Searching articles & blogs...", total=None)
            try:
                blogs = tavily.search(
                    query=f"{topic} explained analysis overview",
                    search_depth="advanced",
                    max_results=5,
                    exclude_domains=ACADEMIC_DOMAINS + WIKI_DOMAINS,
                )
                results["articles_blogs"] = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("url", ""),
                        "snippet": r.get("content", ""),
                        "score": r.get("score", 0),
                        "source_type": "article_blog",
                    }
                    for r in blogs.get("results", [])
                ]
            except Exception as e:
                console.print(f"[yellow]! Blog/article search warning: {e}[/]")
            progress.update(t3, completed=True)
    else:
        # Non-TTY context (Flask) — run searches directly without spinners
        try:
            academic = tavily.search(
                query=f"{topic} research paper study findings",
                search_depth="advanced",
                max_results=5,
                include_domains=ACADEMIC_DOMAINS,
            )
            results["research_papers"] = [
                {
                    "title": r.get("title", "Untitled"),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "score": r.get("score", 0),
                    "source_type": "research_paper",
                }
                for r in academic.get("results", [])
            ]
        except Exception as e:
            pass

        try:
            wiki = tavily.search(
                query=f"{topic}",
                search_depth="advanced",
                max_results=3,
                include_domains=WIKI_DOMAINS,
            )
            results["wikipedia"] = [
                {
                    "title": r.get("title", "Untitled"),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "score": r.get("score", 0),
                    "source_type": "wikipedia",
                }
                for r in wiki.get("results", [])
            ]
        except Exception as e:
            pass

        try:
            blogs = tavily.search(
                query=f"{topic} explained analysis overview",
                search_depth="advanced",
                max_results=5,
                exclude_domains=ACADEMIC_DOMAINS + WIKI_DOMAINS,
            )
            results["articles_blogs"] = [
                {
                    "title": r.get("title", "Untitled"),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "score": r.get("score", 0),
                    "source_type": "article_blog",
                }
                for r in blogs.get("results", [])
            ]
        except Exception as e:
            pass

    return results


# ──────────────────────────────────────────────
# 2. EXTRACT CONTENT  (Tavily Extract API)
# ──────────────────────────────────────────────

def extract_content(sources: dict, tavily: TavilyClient) -> dict:
    """
    For each discovered URL, use Tavily Extract to pull clean full-text.
    Updates sources in-place with extracted content.
    """
    all_sources = (
        sources["research_papers"]
        + sources["wikipedia"]
        + sources["articles_blogs"]
    )

    urls = [s["url"] for s in all_sources if s.get("url")]

    if not urls:
        if IS_TTY:
            console.print("[yellow]! No URLs found to extract content from.[/]")
        return sources

    def _do_extract():
        try:
            # Tavily extract accepts a list of URLs
            extracted = tavily.extract(urls=urls)
            extracted_map = {}
            for item in extracted.get("results", []):
                extracted_map[item.get("url", "")] = item.get("raw_content", "")

            # Merge extracted content back into sources
            for source in all_sources:
                url = source.get("url", "")
                if url in extracted_map and extracted_map[url]:
                    # Truncate to ~1500 chars to keep within Groq free-tier limits
                    full_text = extracted_map[url]
                    source["full_content"] = full_text[:1500]
                else:
                    source["full_content"] = source.get("snippet", "")

        except Exception as e:
            if IS_TTY:
                console.print(f"[yellow]! Extract warning: {e}[/]")
            # Fall back to snippets
            for source in all_sources:
                source["full_content"] = source.get("snippet", "")

    if IS_TTY:
        with Progress(
            TextColumn("[bold cyan]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Extracting full content from {len(urls)} sources...", total=None
            )
            _do_extract()
            progress.update(task, completed=True)
    else:
        _do_extract()

    return sources


# ──────────────────────────────────────────────
# 3. SYNTHESIZE REPORT  (Groq LLM)
# ──────────────────────────────────────────────

def synthesize_report(topic: str, sources: dict, groq_client: Groq) -> dict:
    """
    Send all collected source content to Groq LLM.
    Returns a structured Python dict with the synthesized report.
    """
    # Build a flat numbered list of all sources
    all_sources = []
    idx = 1
    for category in ["research_papers", "wikipedia", "articles_blogs"]:
        for s in sources[category]:
            all_sources.append({**s, "ref_id": idx})
            idx += 1

    if not all_sources:
        return {
            "topic": topic,
            "error": "No sources found. Try a different topic or check your API keys.",
            "sections": [],
            "sources": [],
        }

    # Build the source context for the LLM
    source_context = ""
    for s in all_sources:
        # Cap content at 800 chars per source to stay under TPM limits
        content_text = s.get('full_content', s.get('snippet', 'No content available'))[:800]
        source_context += f"""
--- SOURCE [{s['ref_id']}] ---
Title: {s['title']}
URL: {s['url']}
Type: {s['source_type']}
Content:
{content_text}

"""

    system_prompt = """You are a research synthesis AI. Given a topic and collected sources, 
produce a well-structured research report as valid JSON.

Your output MUST be a single JSON object with this exact structure:
{
  "topic": "the research topic",
  "executive_summary": "A concise 3-5 sentence summary of the key findings across all sources",
  "sections": [
    {
      "title": "Section Title",
      "content": "Detailed content synthesized from sources. Use inline citations like [1], [2] etc.",
      "key_points": ["bullet point 1", "bullet point 2"]
    }
  ],
  "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"],
  "sources_used": [
    {
      "ref_id": 1,
      "title": "Source title",
      "url": "source url",
      "source_type": "research_paper|wikipedia|article_blog",
      "relevance": "Brief note on why this source is relevant"
    }
  ]
}

Rules:
1. Create 4-6 logical sections that organize information BY THEME, not by source.
2. Synthesize — don't just copy. Combine insights from multiple sources.
3. ALWAYS cite sources using [ref_id] notation inline.
4. Keep content factual. Don't fabricate information not present in sources.
5. Include ALL sources in sources_used, even if only partially used.
6. Output ONLY valid JSON, no markdown fences, no explanation text."""

    user_prompt = f"""Research Topic: {topic}

Collected Sources:
{source_context}

Synthesize these sources into a structured research report. Output ONLY valid JSON."""

    def _do_synthesize():
        nonlocal all_sources
        _user_prompt = user_prompt  # Start with full content

        for attempt in range(2):  # Max 2 attempts (full content + truncated)
            try:
                response = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": _user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=4096,
                    response_format={"type": "json_object"},
                )

                raw = response.choices[0].message.content.strip()

                # Parse the JSON response
                report = json.loads(raw)

                # Ensure required keys exist
                report.setdefault("topic", topic)
                report.setdefault("executive_summary", "")
                report.setdefault("sections", [])
                report.setdefault("key_takeaways", [])
                report.setdefault("sources_used", [])
                return report

            except json.JSONDecodeError as e:
                if IS_TTY:
                    console.print(f"[red]X JSON parse error: {e}[/]")
                return {
                    "topic": topic,
                    "error": f"Failed to parse LLM response: {e}",
                    "raw_response": raw if 'raw' in dir() else "",
                    "sections": [],
                    "sources_used": [],
                }
            except Exception as e:
                error_str = str(e).lower()
                # On 413 or TPM limits, truncate content and retry once
                if attempt == 0 and ("413" in error_str or "too large" in error_str or "rate_limit_exceeded" in error_str):
                    logger.warning("Lite: Payload too large or TPM limit hit -- truncating sources heavily and retrying...")
                    truncated_ctx = ""
                    for s in all_sources:
                        content = s.get('full_content', s.get('snippet', ''))[:250]
                        truncated_ctx += f"\n--- SOURCE ---\nTitle: {s.get('title','')}\nURL: {s.get('url','')}\nContent:\n{content}\n"
                    _user_prompt = f"""Research Topic: {topic}\n\nCollected Sources:\n{truncated_ctx}\n\nSynthesize these sources into a structured research report. Output ONLY valid JSON."""
                    
                    try:
                        # Force max_tokens to be lower on fallback to fit within 6000 TPM limit
                        response = groq_client.chat.completions.create(
                            model=GROQ_MODEL,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": _user_prompt},
                            ],
                            temperature=0.3,
                            max_tokens=1500,
                            response_format={"type": "json_object"},
                        )
                        raw = response.choices[0].message.content.strip()
                        report = json.loads(raw)
                        report.setdefault("topic", topic)
                        report.setdefault("executive_summary", "")
                        report.setdefault("sections", [])
                        report.setdefault("key_takeaways", [])
                        report.setdefault("sources_used", [])
                        return report
                    except Exception as fallback_e:
                        if IS_TTY:
                            console.print(f"[red]X Groq fallback error: {fallback_e}[/]")
                        return {
                            "topic": topic,
                            "error": str(fallback_e),
                            "sections": [],
                            "sources_used": [],
                        }
                    
                if IS_TTY:
                    console.print(f"[red]X Groq API error: {e}[/]")
                return {
                    "topic": topic,
                    "error": str(e),
                    "sections": [],
                    "sources_used": [],
                }

    if IS_TTY:
        with Progress(
            TextColumn("[bold cyan]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Synthesizing report with Groq LLM...", total=None)
            report = _do_synthesize()
            progress.update(task, completed=True)
    else:
        report = _do_synthesize()

    # Add metadata
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["total_sources"] = len(all_sources)
    report["source_breakdown"] = {
        "research_papers": len(sources["research_papers"]),
        "wikipedia": len(sources["wikipedia"]),
        "articles_blogs": len(sources["articles_blogs"]),
    }

    return report


# ──────────────────────────────────────────────
# 4. SAVE REPORT
# ──────────────────────────────────────────────

def save_report(topic: str, report: dict) -> str:
    """Save the report dict as JSON. Returns the file path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Sanitize topic for filename
    safe_name = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')[:50]
    filename = f"{safe_name}_report.json"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return filepath


# ──────────────────────────────────────────────
# 5. DISPLAY REPORT  (Rich CLI Output)
# ──────────────────────────────────────────────

def display_report(report: dict) -> None:
    """Pretty-print the structured report to the console using Rich."""

    console.print()

    # ── Title ──
    console.print(
        Panel(
            f"[bold white]{report.get('topic', 'Unknown Topic')}[/]",
            title="[bold green]📄 RESEARCH REPORT[/]",
            border_style="bright_green",
            padding=(1, 4),
        )
    )

    # ── Error check ──
    if report.get("error"):
        console.print(
            Panel(
                f"[red]{report['error']}[/]",
                title="[bold red]Error[/]",
                border_style="red",
            )
        )
        return

    # ── Source Breakdown ──
    breakdown = report.get("source_breakdown", {})
    source_table = Table(
        title="📊 Sources Collected",
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
    )
    source_table.add_column("Category", style="cyan")
    source_table.add_column("Count", justify="center", style="bold white")
    source_table.add_row("📚 Research Papers", str(breakdown.get("research_papers", 0)))
    source_table.add_row("📖 Wikipedia", str(breakdown.get("wikipedia", 0)))
    source_table.add_row("📝 Articles & Blogs", str(breakdown.get("articles_blogs", 0)))
    source_table.add_row(
        "[bold]Total[/]",
        f"[bold]{report.get('total_sources', 0)}[/]",
    )
    console.print(source_table)
    console.print()

    # ── Executive Summary ──
    summary = report.get("executive_summary", "")
    if summary:
        console.print(
            Panel(
                f"[white]{summary}[/]",
                title="[bold yellow]✨ Executive Summary[/]",
                border_style="yellow",
                padding=(1, 2),
            )
        )
        console.print()

    # ── Sections ──
    for i, section in enumerate(report.get("sections", []), 1):
        console.print(Rule(f"[bold cyan]§{i}  {section.get('title', 'Section')}[/]"))
        console.print(f"\n{section.get('content', '')}\n")

        key_points = section.get("key_points", [])
        if key_points:
            console.print("[bold green]Key Points:[/]")
            for point in key_points:
                console.print(f"  [green]•[/] {point}")
            console.print()

    # ── Key Takeaways ──
    takeaways = report.get("key_takeaways", [])
    if takeaways:
        console.print(Rule("[bold magenta]🎯 Key Takeaways[/]"))
        for j, t in enumerate(takeaways, 1):
            console.print(f"  [bold magenta]{j}.[/] {t}")
        console.print()

    # ── References Table ──
    sources_used = report.get("sources_used", [])
    if sources_used:
        ref_table = Table(
            title="🔗 References",
            show_header=True,
            header_style="bold blue",
            border_style="dim",
            show_lines=True,
        )
        ref_table.add_column("#", style="bold", width=4, justify="center")
        ref_table.add_column("Title", style="white", max_width=40)
        ref_table.add_column("Type", style="cyan", width=16)
        ref_table.add_column("URL", style="dim blue", max_width=50)

        for src in sources_used:
            type_emoji = {
                "research_paper": "📚",
                "wikipedia": "📖",
                "article_blog": "📝",
            }.get(src.get("source_type", ""), "📄")

            ref_table.add_row(
                str(src.get("ref_id", "")),
                src.get("title", "Untitled"),
                f"{type_emoji} {src.get('source_type', 'unknown')}",
                src.get("url", ""),
            )

        console.print(ref_table)

    # ── Timestamp ──
    console.print(
        f"\n[dim]Generated: {report.get('generated_at', 'unknown')}[/]\n"
    )


# ──────────────────────────────────────────────
# 6. PUBLIC API — for importing into other files
# ──────────────────────────────────────────────

def fetch_research(topic: str) -> dict:
    """
    Main public function. Call from other Python files:

        from paper_fetch import fetch_research
        result = fetch_research("quantum computing")

    Returns a structured dict with the full report.
    """
    # Clients are initialized centrally in clients.py
    tavily = tavily_client

    if IS_TTY:
        console.print(
            Panel(
                f"[bold white]Topic:[/] [cyan]{topic}[/]",
                title="[bold green]PaperPilot Research Scraper[/]",
                border_style="bright_green",
                padding=(1, 2),
            )
        )
        console.print()

    # Step 1: Search across 3 source categories
    if IS_TTY:
        console.print(Rule("[bold]Step 1 / 3 -- Searching Sources[/]"))
    sources = search_sources(topic, tavily)

    total = sum(len(v) for v in sources.values())
    if IS_TTY:
        console.print(f"[green]OK Found {total} sources across 3 categories[/]\n")

    if total == 0:
        return {
            "topic": topic,
            "error": "No sources found. Try a broader topic.",
            "sections": [],
            "sources_used": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # Step 2: Extract full content from discovered URLs
    if IS_TTY:
        console.print(Rule("[bold]Step 2 / 3 -- Extracting Content[/]"))
    sources = extract_content(sources, tavily)
    if IS_TTY:
        console.print("[green]OK Content extracted and cleaned[/]\n")

    # Step 3: Synthesize with Groq LLM
    if IS_TTY:
        console.print(Rule("[bold]Step 3 / 3 -- Synthesizing Report[/]"))
    report = synthesize_report(topic, sources, groq_client)
    if IS_TTY:
        console.print("[green]OK Report synthesized[/]\n")

    return report


# ──────────────────────────────────────────────
# 7. CLI ENTRY POINT
# ──────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        console.print(
            Panel(
                "[red]Missing topic argument.[/]\n\n"
                '[white]Usage:[/] [cyan]python paper_fetch.py "your topic here"[/]\n'
                '[white]Example:[/] [cyan]python paper_fetch.py "artificial intelligence in healthcare"[/]',
                title="[bold red]Error[/]",
                border_style="red",
            )
        )
        sys.exit(1)

    topic = " ".join(sys.argv[1:])

    start = time.time()

    # Fetch & synthesize
    report = fetch_research(topic)

    # Save to JSON
    filepath = save_report(topic, report)

    # Display in CLI
    display_report(report)

    elapsed = time.time() - start

    console.print(
        Panel(
            f"[green]OK Report saved to:[/] [bold white]{filepath}[/]\n"
            f"[green]OK Time elapsed:[/] [bold white]{elapsed:.1f}s[/]\n\n"
            "[dim]Import in other files:[/]\n"
            '[cyan]from paper_fetch import fetch_research\n'
            'result = fetch_research("your topic")[/]',
            title="[bold green]Done[/]",
            border_style="bright_green",
        )
    )


if __name__ == "__main__":
    main()
