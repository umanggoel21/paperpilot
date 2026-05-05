"""
PaperPilot — Academic PDF Generator
=====================================
Takes structured JSON (from paper_fetch.py) and generates
a professional academic-level PDF document using ReportLab.

Uses Groq LLM to rewrite/enhance content to academic standards
before rendering the PDF.

Usage:
    # From CLI — provide a JSON file path:
    python pdf_generator.py output/your_topic_report.json

    # From another Python file:
    from pdf_generator import generate_pdf
    generate_pdf(report_dict)              # pass a dict
    generate_pdf("output/report.json")     # or a file path

Academic Formatting Rules Applied:
    - Font: Times New Roman, 12pt body
    - Page: A4 (210mm × 297mm)
    - Margins: 1 inch (72pt) all sides
    - Line spacing: 1.5×
    - Section headings: 14pt bold, numbered
    - Sub-headings: 12pt bold, numbered (e.g. 1.1, 1.2)
    - Header: Project title on every page (10pt)
    - Footer: Page numbers centered
    - Justified text alignment
    - Proper paragraph indentation
    - References in IEEE format
    - Table of Contents
"""

import sys
import os
import json
import re
import textwrap
from datetime import datetime, timezone

from dotenv import load_dotenv
from groq import Groq
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

console = Console()

# Page config
PAGE_WIDTH, PAGE_HEIGHT = A4  # 595.27 × 841.89 pt
MARGIN = 1 * inch  # 72pt = 1 inch margins

# Colors
ACCENT_COLOR = HexColor("#1a1a2e")
HEADING_COLOR = HexColor("#16213e")
LINK_COLOR = HexColor("#0f4c75")


# ──────────────────────────────────────────────
# FONT REGISTRATION
# ──────────────────────────────────────────────

def register_fonts():
    """
    Register Times New Roman if available on system,
    otherwise fall back to ReportLab's built-in Times.
    """
    # Try to find system Times New Roman
    times_paths = [
        r"C:\Windows\Fonts\times.ttf",
        r"C:\Windows\Fonts\timesbd.ttf",
        r"C:\Windows\Fonts\timesi.ttf",
        r"C:\Windows\Fonts\timesbi.ttf",
    ]

    if all(os.path.exists(p) for p in times_paths):
        pdfmetrics.registerFont(TTFont("TimesNR", times_paths[0]))
        pdfmetrics.registerFont(TTFont("TimesNR-Bold", times_paths[1]))
        pdfmetrics.registerFont(TTFont("TimesNR-Italic", times_paths[2]))
        pdfmetrics.registerFont(TTFont("TimesNR-BoldItalic", times_paths[3]))
        addMapping("TimesNR", 0, 0, "TimesNR")
        addMapping("TimesNR", 1, 0, "TimesNR-Bold")
        addMapping("TimesNR", 0, 1, "TimesNR-Italic")
        addMapping("TimesNR", 1, 1, "TimesNR-BoldItalic")
        return "TimesNR"
    else:
        # Fallback to built-in Times-Roman
        return "Times-Roman"


# ──────────────────────────────────────────────
# STYLES
# ──────────────────────────────────────────────

def build_styles(font_family: str) -> dict:
    """
    Build all paragraph styles for the academic document.
    Matches the reference PDF formatting:
      - Title: 16pt bold centered
      - Section heading: 14pt bold
      - Sub-heading: 12pt bold
      - Body: 12pt regular, justified, 1.5× line spacing
      - Header/Footer: 10pt
    """
    bold_font = f"{font_family}-Bold" if font_family == "TimesNR" else "Times-Bold"
    italic_font = f"{font_family}-Italic" if font_family == "TimesNR" else "Times-Italic"
    bold_italic = f"{font_family}-BoldItalic" if font_family == "TimesNR" else "Times-BoldItalic"

    LINE_SPACING = 18  # 1.5× of 12pt = 18pt leading

    styles = {
        "title": ParagraphStyle(
            "DocTitle",
            fontName=bold_font,
            fontSize=16,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=ACCENT_COLOR,
        ),
        "subtitle": ParagraphStyle(
            "DocSubtitle",
            fontName=font_family,
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            spaceAfter=4,
            textColor=HexColor("#444444"),
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading",
            fontName=bold_font,
            fontSize=14,
            leading=20,
            spaceBefore=18,
            spaceAfter=10,
            textColor=HEADING_COLOR,
            keepWithNext=True,
        ),
        "sub_heading": ParagraphStyle(
            "SubHeading",
            fontName=bold_font,
            fontSize=12,
            leading=LINE_SPACING,
            spaceBefore=12,
            spaceAfter=6,
            textColor=HEADING_COLOR,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "BodyText",
            fontName=font_family,
            fontSize=12,
            leading=LINE_SPACING,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            firstLineIndent=0,
        ),
        "body_indent": ParagraphStyle(
            "BodyIndent",
            fontName=font_family,
            fontSize=12,
            leading=LINE_SPACING,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            firstLineIndent=24,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName=font_family,
            fontSize=12,
            leading=LINE_SPACING,
            alignment=TA_JUSTIFY,
            spaceAfter=4,
            leftIndent=24,
            bulletIndent=12,
        ),
        "reference": ParagraphStyle(
            "Reference",
            fontName=font_family,
            fontSize=11,
            leading=15,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            leftIndent=24,
            firstLineIndent=-24,
        ),
        "header": ParagraphStyle(
            "Header",
            fontName=font_family,
            fontSize=10,
            leading=12,
            textColor=HexColor("#666666"),
        ),
        "footer": ParagraphStyle(
            "Footer",
            fontName=font_family,
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            textColor=HexColor("#666666"),
        ),
        "abstract_label": ParagraphStyle(
            "AbstractLabel",
            fontName=bold_font,
            fontSize=12,
            leading=LINE_SPACING,
            alignment=TA_CENTER,
            spaceBefore=12,
            spaceAfter=6,
            textColor=HEADING_COLOR,
        ),
        "abstract_body": ParagraphStyle(
            "AbstractBody",
            fontName=italic_font,
            fontSize=12,
            leading=LINE_SPACING,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leftIndent=18,
            rightIndent=18,
        ),
        "toc_heading": ParagraphStyle(
            "TOCHeading",
            fontName=bold_font,
            fontSize=14,
            leading=20,
            spaceBefore=12,
            spaceAfter=10,
            textColor=HEADING_COLOR,
        ),
        "toc_entry": ParagraphStyle(
            "TOCEntry",
            fontName=font_family,
            fontSize=12,
            leading=18,
            leftIndent=12,
            spaceAfter=4,
        ),
        "toc_sub_entry": ParagraphStyle(
            "TOCSubEntry",
            fontName=font_family,
            fontSize=12,
            leading=18,
            leftIndent=36,
            spaceAfter=3,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontName=bold_font,
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=HexColor("#ffffff"),
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            fontName=font_family,
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
        ),
    }

    return styles


# ──────────────────────────────────────────────
# GROQ: ENHANCE CONTENT TO ACADEMIC QUALITY
# ──────────────────────────────────────────────

def enhance_content_academic(report: dict) -> dict:
    """
    Use Groq LLM to rewrite the report content to proper
    academic writing standards:
      - Formal tone, third person
      - Proper citations maintained
      - Expanded paragraphs with transitions
      - Academic vocabulary
      - Logical flow between sections
    Returns enhanced report dict.
    """
    if not GROQ_API_KEY:
        console.print("[yellow]! No GROQ_API_KEY — skipping academic enhancement[/]")
        return report

    groq_client = Groq(api_key=GROQ_API_KEY)

    # Build compact representation of sections
    sections_text = ""
    for i, section in enumerate(report.get("sections", []), 1):
        sections_text += f"\n## Section {i}: {section['title']}\n"
        sections_text += f"Content: {section['content']}\n"
        kp = section.get("key_points", [])
        if kp:
            sections_text += "Key points: " + "; ".join(kp) + "\n"

    # Build sources reference
    sources_text = ""
    for src in report.get("sources_used", []):
        sources_text += f"[{src['ref_id']}] {src['title']} — {src['url']} ({src['source_type']})\n"

    system_prompt = """You are an academic writing expert. Rewrite the given research report sections 
to meet academic standards. Output valid JSON only.

Academic writing rules:
1. Use formal, third-person tone ("This study examines..." not "We look at...")
2. Preserve ALL citation references [1], [2] etc. exactly as given
3. Write substantial paragraphs (at least 4-5 sentences each)
4. Use transition phrases between ideas ("Furthermore...", "In contrast...", "Moreover...")
5. Include topic sentences for each paragraph
6. Use academic vocabulary appropriately
7. Each section content should be 150-250 words minimum
8. Add proper context and background to claims
9. Maintain logical flow and argumentation

Output format — ONLY valid JSON:
{
  "enhanced_abstract": "A formal 150-200 word abstract summarizing the entire report",
  "sections": [
    {
      "title": "Original section title",
      "content": "Rewritten academic content with [citations] preserved",
      "key_points": ["refined key point 1", "refined key point 2"]
    }
  ],
  "conclusion": "A formal 100-150 word conclusion summarizing findings and future directions"
}"""

    user_prompt = f"""Topic: {report.get('topic', 'Unknown')}

Executive Summary: {report.get('executive_summary', '')}

{sections_text}

Available Sources:
{sources_text}

Rewrite these sections to academic quality. Preserve all [citation] numbers. Output ONLY valid JSON."""

    with Progress(
        TextColumn("[bold cyan]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Enhancing content to academic standards via Groq...", total=None)

        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content.strip()
            enhanced = json.loads(raw)

            # Merge enhanced content back
            if "enhanced_abstract" in enhanced:
                report["enhanced_abstract"] = enhanced["enhanced_abstract"]

            if "sections" in enhanced:
                # Replace section content with enhanced versions
                for i, section in enumerate(enhanced["sections"]):
                    if i < len(report["sections"]):
                        report["sections"][i]["content"] = section.get("content", report["sections"][i]["content"])
                        if section.get("key_points"):
                            report["sections"][i]["key_points"] = section["key_points"]

            if "conclusion" in enhanced:
                report["conclusion"] = enhanced["conclusion"]

            console.print("[green]OK Content enhanced to academic quality[/]")

        except Exception as e:
            console.print(f"[yellow]! Enhancement warning (using original content): {e}[/]")

        progress.update(task, completed=True)

    return report


# ──────────────────────────────────────────────
# HEADER / FOOTER CALLBACK
# ──────────────────────────────────────────────

class HeaderFooter:
    """Draws header and footer on every page."""

    def __init__(self, title: str, font_family: str):
        self.title = title
        self.font_family = font_family

    def __call__(self, canvas, doc):
        canvas.saveState()

        # Header — project title on top of each page (except first)
        if doc.page > 1:
            canvas.setFont(self.font_family, 10)
            canvas.setFillColor(HexColor("#666666"))
            canvas.drawString(MARGIN, PAGE_HEIGHT - MARGIN + 20, self.title)
            # Header line
            canvas.setStrokeColor(HexColor("#cccccc"))
            canvas.setLineWidth(0.5)
            canvas.line(MARGIN, PAGE_HEIGHT - MARGIN + 14, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN + 14)

        # Footer — page number centered
        canvas.setFont(self.font_family, 10)
        canvas.setFillColor(HexColor("#666666"))
        canvas.drawCentredString(PAGE_WIDTH / 2, MARGIN - 24, str(doc.page))

        canvas.restoreState()


# ──────────────────────────────────────────────
# PDF BUILDER
# ──────────────────────────────────────────────

def _escape_xml(text: str) -> str:
    """Escape text for ReportLab XML-based Paragraph."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _format_citation_refs(text: str, font_family: str) -> str:
    """
    Turn [1], [2] style citations into superscript blue links.
    """
    bold_font = f"{font_family}-Bold" if font_family == "TimesNR" else "Times-Bold"
    # Match patterns like [1], [2], [1][3], [1], [2]
    def replace_ref(match):
        ref = match.group(0)
        return f'<font color="#0f4c75"><super>{_escape_xml(ref)}</super></font>'

    return re.sub(r'\[\d+\]', replace_ref, text)


def build_pdf_content(report: dict, styles: dict, font_family: str) -> list:
    """
    Build the list of flowable elements for the PDF.
    """
    story = []
    bold_font = f"{font_family}-Bold" if font_family == "TimesNR" else "Times-Bold"
    italic_font = f"{font_family}-Italic" if font_family == "TimesNR" else "Times-Italic"

    topic = report.get("topic", "Research Report")
    sources_used = report.get("sources_used", [])

    # ══════════════════════════════════════════
    # TITLE PAGE
    # ══════════════════════════════════════════

    story.append(Spacer(1, 120))

    # Title
    story.append(Paragraph(
        _escape_xml(topic),
        styles["title"],
    ))
    story.append(Spacer(1, 8))

    # Subtitle line
    story.append(HRFlowable(
        width="40%", thickness=1.5,
        color=ACCENT_COLOR, spaceAfter=12, spaceBefore=6,
        hAlign="CENTER",
    ))

    story.append(Paragraph(
        "Research Report",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 6))

    # Generation meta
    gen_date = report.get("generated_at", datetime.now(timezone.utc).isoformat())
    try:
        dt = datetime.fromisoformat(gen_date)
        date_str = dt.strftime("%B %d, %Y")
    except Exception:
        date_str = gen_date

    story.append(Paragraph(
        f"Generated: {_escape_xml(date_str)}",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 4))

    breakdown = report.get("source_breakdown", {})
    total = report.get("total_sources", 0)
    story.append(Paragraph(
        f"Sources: {total} ({breakdown.get('research_papers', 0)} papers, "
        f"{breakdown.get('wikipedia', 0)} Wikipedia, "
        f"{breakdown.get('articles_blogs', 0)} articles)",
        styles["subtitle"],
    ))

    story.append(Spacer(1, 60))

    # Abstract
    abstract = report.get("enhanced_abstract", report.get("executive_summary", ""))
    if abstract:
        story.append(Paragraph("Abstract", styles["abstract_label"]))
        story.append(HRFlowable(
            width="100%", thickness=0.5,
            color=HexColor("#cccccc"), spaceAfter=8,
        ))
        story.append(Paragraph(
            f"<i>{_escape_xml(abstract)}</i>",
            styles["abstract_body"],
        ))
        story.append(HRFlowable(
            width="100%", thickness=0.5,
            color=HexColor("#cccccc"), spaceBefore=4, spaceAfter=12,
        ))

    story.append(PageBreak())

    # ══════════════════════════════════════════
    # TABLE OF CONTENTS
    # ══════════════════════════════════════════

    story.append(Paragraph("Table of Contents", styles["toc_heading"]))
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=ACCENT_COLOR, spaceAfter=12,
    ))

    sections = report.get("sections", [])
    for i, section in enumerate(sections, 1):
        title = section.get("title", f"Section {i}")
        story.append(Paragraph(
            f"{i}. {_escape_xml(title)}",
            styles["toc_entry"],
        ))
        # Add sub-entries for key points
        key_points = section.get("key_points", [])
        for j, kp in enumerate(key_points, 1):
            story.append(Paragraph(
                f"{i}.{j} {_escape_xml(kp)}",
                styles["toc_sub_entry"],
            ))

    # Add references entry
    ref_num = len(sections) + 1
    story.append(Paragraph(
        f"{ref_num}. References",
        styles["toc_entry"],
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════
    # MAIN SECTIONS
    # ══════════════════════════════════════════

    for i, section in enumerate(sections, 1):
        title = section.get("title", f"Section {i}")
        content = section.get("content", "")
        key_points = section.get("key_points", [])

        # Section heading (numbered)
        story.append(Paragraph(
            f"{i}. {_escape_xml(title)}",
            styles["section_heading"],
        ))

        # Section content — split into paragraphs
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        if not paragraphs:
            paragraphs = [content]

        for para_text in paragraphs:
            formatted = _format_citation_refs(_escape_xml(para_text), font_family)
            story.append(Paragraph(formatted, styles["body"]))

        # Key points as sub-section
        if key_points:
            story.append(Spacer(1, 4))
            story.append(Paragraph(
                f"{i}.1 Key Findings",
                styles["sub_heading"],
            ))

            for kp in key_points:
                bullet_text = f"<bullet>&bull;</bullet> {_escape_xml(kp)}"
                story.append(Paragraph(bullet_text, styles["bullet"]))

            story.append(Spacer(1, 6))

    # ══════════════════════════════════════════
    # CONCLUSION (if enhanced by Groq)
    # ══════════════════════════════════════════

    conclusion = report.get("conclusion", "")
    if conclusion:
        conc_num = len(sections) + 1
        story.append(Paragraph(
            f"{conc_num}. Conclusion",
            styles["section_heading"],
        ))
        formatted = _format_citation_refs(_escape_xml(conclusion), font_family)
        story.append(Paragraph(formatted, styles["body"]))
        story.append(Spacer(1, 12))

    # ══════════════════════════════════════════
    # REFERENCES
    # ══════════════════════════════════════════

    ref_section_num = len(sections) + (2 if conclusion else 1)
    story.append(Paragraph(
        f"{ref_section_num}. References",
        styles["section_heading"],
    ))

    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=HexColor("#cccccc"), spaceAfter=10,
    ))

    if sources_used:
        for src in sources_used:
            ref_id = src.get("ref_id", "?")
            title = src.get("title", "Untitled")
            url = src.get("url", "")
            src_type = src.get("source_type", "unknown")

            # Format source type label
            type_label = {
                "research_paper": "Research Paper",
                "wikipedia": "Wikipedia",
                "article_blog": "Article/Blog",
            }.get(src_type, src_type.replace("_", " ").title())

            ref_text = (
                f'[{ref_id}] {_escape_xml(title)}. '
                f'<i>[{_escape_xml(type_label)}]</i>. '
                f'Available at: <font color="#0f4c75">'
                f'<link href="{_escape_xml(url)}">{_escape_xml(url)}</link>'
                f'</font>'
            )
            story.append(Paragraph(ref_text, styles["reference"]))
    else:
        story.append(Paragraph(
            "No references available.",
            styles["body"],
        ))

    # ══════════════════════════════════════════
    # SOURCE SUMMARY TABLE
    # ══════════════════════════════════════════

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Source Summary",
        styles["sub_heading"],
    ))

    # Build table
    table_data = [
        [
            Paragraph("Category", styles["table_header"]),
            Paragraph("Count", styles["table_header"]),
        ]
    ]

    breakdown = report.get("source_breakdown", {})
    table_data.append([
        Paragraph("Research Papers", styles["table_cell"]),
        Paragraph(str(breakdown.get("research_papers", 0)), styles["table_cell"]),
    ])
    table_data.append([
        Paragraph("Wikipedia", styles["table_cell"]),
        Paragraph(str(breakdown.get("wikipedia", 0)), styles["table_cell"]),
    ])
    table_data.append([
        Paragraph("Articles &amp; Blogs", styles["table_cell"]),
        Paragraph(str(breakdown.get("articles_blogs", 0)), styles["table_cell"]),
    ])
    table_data.append([
        Paragraph("<b>Total</b>", styles["table_cell"]),
        Paragraph(f"<b>{report.get('total_sources', 0)}</b>", styles["table_cell"]),
    ])

    col_widths = [3.5 * inch, 1.5 * inch]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        # Alternating rows
        ("BACKGROUND", (0, 1), (-1, 1), HexColor("#f5f5f5")),
        ("BACKGROUND", (0, 3), (-1, 3), HexColor("#f5f5f5")),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        # Bold last row
        ("BACKGROUND", (0, -1), (-1, -1), HexColor("#e8e8e8")),
    ]))

    story.append(table)

    return story


# ──────────────────────────────────────────────
# MAIN: generate_pdf
# ──────────────────────────────────────────────

def generate_pdf(report_input, output_path: str = None, enhance: bool = True) -> str:
    """
    Generate a professional academic PDF from a report dict or JSON file path.

    Args:
        report_input: dict or str (path to .json file)
        output_path:  custom output path (optional)
        enhance:      whether to use Groq to enhance to academic quality

    Returns:
        str: path to the generated PDF file
    """

    # Load report
    if isinstance(report_input, str):
        # It's a file path
        with open(report_input, "r", encoding="utf-8") as f:
            report = json.load(f)
        console.print(f"[green]OK Loaded report from: {report_input}[/]")
    elif isinstance(report_input, dict):
        report = report_input
    else:
        raise TypeError("report_input must be a dict or a path to a JSON file")

    topic = report.get("topic", "Research Report")

    console.print(Panel(
        f"[bold white]Generating PDF for:[/] [cyan]{topic}[/]",
        title="[bold green]PaperPilot PDF Generator[/]",
        border_style="bright_green",
        padding=(1, 2),
    ))

    # Step 1: Enhance content with Groq
    if enhance:
        console.print("\n[bold]Step 1/2 — Academic Enhancement[/]")
        report = enhance_content_academic(report)
    else:
        console.print("\n[dim]Skipping academic enhancement (enhance=False)[/]")

    # Step 2: Build PDF
    console.print("[bold]Step 2/2 — Generating PDF[/]")

    with Progress(
        TextColumn("[bold cyan]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Building PDF document...", total=None)

        # Register fonts
        font_family = register_fonts()

        # Build styles
        styles = build_styles(font_family)

        # Determine output path
        if output_path is None:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            safe_name = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')[:50]
            output_path = os.path.join(OUTPUT_DIR, f"{safe_name}_report.pdf")

        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN,
            bottomMargin=MARGIN,
            title=topic,
            author="PaperPilot Research System",
            subject=f"Research Report: {topic}",
        )

        # Build content
        story = build_pdf_content(report, styles, font_family)

        # Build with header/footer
        header_footer = HeaderFooter(topic, font_family)
        try:
            doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
        except Exception as e:
            logger.error(f"ReportLab build failed: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            raise

        progress.update(task, completed=True)

    console.print(f"\n[green]OK PDF generated:[/] [bold white]{output_path}[/]")
    return output_path


# ──────────────────────────────────────────────
# CLI ENTRY POINT
# ──────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        console.print(Panel(
            "[red]Missing JSON file path.[/]\n\n"
            '[white]Usage:[/] [cyan]python pdf_generator.py output/your_report.json[/]\n'
            '[white]Example:[/] [cyan]python pdf_generator.py output/artificial_intelligence_in_healthcare_report.json[/]\n\n'
            "[dim]Options:[/]\n"
            "  [cyan]--no-enhance[/]  Skip Groq academic enhancement\n",
            title="[bold red]Error[/]",
            border_style="red",
        ))
        sys.exit(1)

    json_path = sys.argv[1]
    enhance = "--no-enhance" not in sys.argv

    if not os.path.exists(json_path):
        console.print(f"[red]X File not found: {json_path}[/]")
        sys.exit(1)

    output_path = generate_pdf(json_path, enhance=enhance)

    console.print(Panel(
        f"[green]Done![/]\n"
        f"[white]PDF saved to:[/] [bold]{output_path}[/]\n\n"
        "[dim]Import in other files:[/]\n"
        "[cyan]from pdf_generator import generate_pdf\n"
        'pdf_path = generate_pdf(report_dict)[/]',
        title="[bold green]Complete[/]",
        border_style="bright_green",
    ))


if __name__ == "__main__":
    main()
