/**
 * PaperPilot — Document Editor
 * ================================
 * Split-pane editor with live Markdown preview,
 * template system, and export to PDF/Markdown.
 */

const API_BASE = window.location.origin;

// ══════════════════════════════════════════════
// 1. INIT
// ══════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    initEditor();
    initDividerDrag();
    initTemplates();
    initExports();
    loadReportIntoEditor();
});


// ══════════════════════════════════════════════
// 2. EDITOR — Live Preview
// ══════════════════════════════════════════════

function initEditor() {
    const textarea = document.getElementById('editor-textarea');
    const preview = document.getElementById('editor-preview');
    const wordCount = document.getElementById('word-count');
    const saveStatus = document.getElementById('save-status');

    if (!textarea || !preview) return;

    // Restore draft from localStorage if no session report is loaded
    const savedDraft = localStorage.getItem('paperpilot_editor_draft');
    if (savedDraft && !sessionStorage.getItem('paperpilot_editor_report')) {
        textarea.value = savedDraft;
    }

    let hasUnsavedChanges = false;

    // Debounced render on input
    let renderTimeout;
    textarea.addEventListener('input', () => {
        hasUnsavedChanges = true;
        if (saveStatus) {
            saveStatus.textContent = 'Unsaved changes';
            saveStatus.className = 'save-status unsaved';
        }
        clearTimeout(renderTimeout);
        renderTimeout = setTimeout(() => {
            renderPreview(textarea.value, preview);
            updateWordCount(textarea.value, wordCount);
        }, 150);
    });

    // Tab key support
    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            textarea.value = textarea.value.substring(0, start) + '    ' + textarea.value.substring(end);
            textarea.selectionStart = textarea.selectionEnd = start + 4;
            textarea.dispatchEvent(new Event('input'));
        }
    });

    // Initial render — fires for template text AND draft content
    if (textarea.value.trim()) {
        renderPreview(textarea.value, preview);
        updateWordCount(textarea.value, wordCount);
    }

    // Auto-save to localStorage every 30 seconds
    setInterval(() => {
        if (hasUnsavedChanges && textarea.value.trim()) {
            localStorage.setItem('paperpilot_editor_draft', textarea.value);
            hasUnsavedChanges = false;
            if (saveStatus) {
                saveStatus.textContent = 'Saved';
                saveStatus.className = 'save-status saved';
            }
        }
    }, 30000);

    // Save on unload
    window.addEventListener('beforeunload', (e) => {
        if (hasUnsavedChanges && textarea.value.trim()) {
            localStorage.setItem('paperpilot_editor_draft', textarea.value);
        }
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
}


function updateWordCount(text, el) {
    if (!el) return;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    el.textContent = `${words.toLocaleString()} words`;
}


// ══════════════════════════════════════════════
// 3. MARKDOWN RENDERER (lightweight, no deps)
// ══════════════════════════════════════════════

function renderPreview(markdown, container) {
    if (!markdown.trim()) {
        container.innerHTML = '<div class="preview-empty"><p>Start typing in the editor to see a live preview here.</p></div>';
        return;
    }

    let html = escapeHtml(markdown);

    // Code blocks (``` ... ```)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="lang-${lang}">${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Headers
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // Bold & Italic
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Blockquotes
    html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

    // Horizontal rules
    html = html.replace(/^---+$/gm, '<hr>');

    // Unordered lists
    html = html.replace(/^[*\-] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

    // Ordered lists
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Paragraphs — wrap remaining text
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    // Clean up empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>(<h[1-3]>)/g, '$1');
    html = html.replace(/(<\/h[1-3]>)<\/p>/g, '$1');
    html = html.replace(/<p>(<pre>)/g, '$1');
    html = html.replace(/(<\/pre>)<\/p>/g, '$1');
    html = html.replace(/<p>(<ul>)/g, '$1');
    html = html.replace(/(<\/ul>)<\/p>/g, '$1');
    html = html.replace(/<p>(<blockquote>)/g, '$1');
    html = html.replace(/(<\/blockquote>)<\/p>/g, '$1');
    html = html.replace(/<p>(<hr>)/g, '$1');
    html = html.replace(/(<hr>)<\/p>/g, '$1');

    container.innerHTML = html;
}


function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}


// ══════════════════════════════════════════════
// 4. DIVIDER DRAG (Resize Panes)
// ══════════════════════════════════════════════

function initDividerDrag() {
    const divider = document.getElementById('editor-divider');
    const leftPane = document.getElementById('editor-pane-left');
    const rightPane = document.getElementById('editor-pane-right');
    const main = document.getElementById('editor-main');

    if (!divider || !leftPane || !rightPane || !main) return;

    let isDragging = false;

    divider.addEventListener('mousedown', (e) => {
        isDragging = true;
        divider.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const mainRect = main.getBoundingClientRect();
        const offset = e.clientX - mainRect.left;
        const totalWidth = mainRect.width;
        const ratio = Math.max(0.2, Math.min(0.8, offset / totalWidth));

        leftPane.style.flex = `0 0 ${ratio * 100}%`;
        rightPane.style.flex = `0 0 ${(1 - ratio) * 100 - 1}%`;
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            divider.classList.remove('dragging');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}


// ══════════════════════════════════════════════
// 5. TEMPLATES
// ══════════════════════════════════════════════

const TEMPLATES = {
    ieee: `# Title of Your Paper

## Abstract
A concise summary of your paper (150-250 words). State the problem, approach, key results, and conclusions.

## I. Introduction
Provide context and motivation for your research. State the problem clearly and outline the paper structure.

## II. Related Work
Survey relevant prior work and position your contribution.

## III. Methodology
Describe your approach, experimental setup, and evaluation metrics.

## IV. Results
Present your findings with supporting data and analysis.

## V. Discussion
Interpret results, discuss limitations, and compare with prior work.

## VI. Conclusion
Summarize contributions and suggest future directions.

## References
[1] Author, "Title," *Journal*, vol. X, pp. Y-Z, 2026.
`,

    apa: `# Research Title

**Authors:** Your Name

**Abstract**

Provide a brief summary of the research (150-250 words).

**Keywords:** keyword1, keyword2, keyword3

## Introduction

Introduce the topic, provide background, and state the research questions.

## Literature Review

Survey and synthesize relevant existing research.

## Method

### Participants
### Materials
### Procedure

## Results

Present findings with statistical analyses.

## Discussion

Interpret results in context of existing literature.

## References

Author, A. A. (2026). Title of work. *Journal Name*, *Volume*(Issue), Pages.
`,

    litreview: `# Literature Review: [Your Topic]

## 1. Introduction

Provide context for why this literature review matters. State the scope and objectives.

## 2. Background

Define key concepts and provide foundational knowledge.

## 3. Thematic Analysis

### 3.1 Theme One
Synthesize findings across multiple sources.

### 3.2 Theme Two
Compare and contrast different perspectives.

### 3.3 Theme Three
Identify patterns, gaps, and contradictions.

## 4. Critical Evaluation

Assess methodology quality, potential biases, and limitations across the literature.

## 5. Conclusion and Future Directions

Summarize key findings and identify areas for further research.

## References

[1] Author, "Title," Journal, Year.
`,

    executive: `# Executive Brief: [Topic]

**Prepared for:** [Audience]
**Date:** ${new Date().toLocaleDateString()}

---

## Executive Summary

A 2-3 paragraph overview of key findings and recommendations.

## Key Findings

- **Finding 1:** Description
- **Finding 2:** Description
- **Finding 3:** Description

## Analysis

Detailed analysis supporting the findings above.

## Recommendations

1. **Action Item 1** — Description
2. **Action Item 2** — Description
3. **Action Item 3** — Description

## Appendix

Supporting data and additional context.
`,
};


function initTemplates() {
    const select = document.getElementById('template-select');
    const textarea = document.getElementById('editor-textarea');

    if (!select || !textarea) return;

    select.addEventListener('change', () => {
        const template = TEMPLATES[select.value];
        if (template && (!textarea.value.trim() || confirm('Replace current content with template?'))) {
            textarea.value = template;
            textarea.dispatchEvent(new Event('input'));
        }
    });
}


// ══════════════════════════════════════════════
// 6. EXPORTS
// ══════════════════════════════════════════════

function initExports() {
    const btnMd = document.getElementById('btn-export-md');
    const btnPdf = document.getElementById('btn-export-pdf');

    if (btnMd) {
        btnMd.addEventListener('click', () => {
            const textarea = document.getElementById('editor-textarea');
            if (!textarea || !textarea.value.trim()) {
                showToast('Nothing to export — write something first.', 'error');
                return;
            }

            const blob = new Blob([textarea.value], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'paperpilot_document.md';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            showToast('Markdown exported', 'success');
        });
    }

    if (btnPdf) {
        btnPdf.addEventListener('click', async () => {
            const textarea = document.getElementById('editor-textarea');
            if (!textarea || !textarea.value.trim()) {
                showToast('Nothing to export — write something first.', 'error');
                return;
            }

            btnPdf.disabled = true;
            const originalHTML = btnPdf.innerHTML;
            btnPdf.innerHTML = '<span class="spinner"></span> Generating...';

            try {
                // Build a minimal report structure from the markdown
                const lines = textarea.value.split('\n');
                const title = lines.find(l => l.startsWith('# '))?.replace('# ', '') || 'Document';
                const content = textarea.value;

                const report = {
                    topic: title,
                    executive_summary: content.substring(0, 500),
                    sections: [{title: title, content: content, key_points: []}],
                    key_takeaways: [],
                    conclusion: '',
                    sources_used: [],
                    generated_at: new Date().toISOString(),
                };

                const response = await fetch(`${API_BASE}/api/pdf`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ report, enhance: false }),
                });

                if (!response.ok) throw new Error('PDF generation failed');

                const data = await response.json();
                if (data.pdf_base64) {
                    const link = document.createElement('a');
                    link.href = `data:application/pdf;base64,${data.pdf_base64}`;
                    link.download = data.filename || 'paperpilot_document.pdf';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    showToast('PDF exported', 'success');
                }
            } catch (err) {
                console.error('PDF export error:', err);
                showToast(`PDF failed: ${err.message}`, 'error');
            } finally {
                btnPdf.disabled = false;
                btnPdf.innerHTML = originalHTML;
            }
        });
    }
}


// ══════════════════════════════════════════════
// 7. LOAD REPORT INTO EDITOR
// ══════════════════════════════════════════════

function loadReportIntoEditor() {
    const textarea = document.getElementById('editor-textarea');
    if (!textarea) return;

    // Check if there's a report in sessionStorage (passed from main page)
    const stored = sessionStorage.getItem('paperpilot_editor_report');
    if (!stored) return;

    try {
        const report = JSON.parse(stored);
        const md = reportToMarkdown(report);
        textarea.value = md;
        textarea.dispatchEvent(new Event('input'));
        showToast('Report loaded into editor', 'success');
    } catch (e) {
        console.error('Failed to load report:', e);
    }
}


function reportToMarkdown(report) {
    let md = `# ${report.topic || 'Research Report'}\n\n`;
    md += `*Generated: ${report.generated_at || new Date().toISOString()}*\n`;
    md += `*Sources: ${report.total_sources || 0}*\n\n---\n\n`;

    const summary = report.enhanced_abstract || report.executive_summary || '';
    if (summary) {
        md += `## Abstract\n\n${summary}\n\n`;
    }

    const sections = report.sections || [];
    sections.forEach((section, i) => {
        md += `## ${i + 1}. ${section.title || 'Section'}\n\n`;
        md += `${section.content || ''}\n\n`;

        if (section.key_points && section.key_points.length) {
            md += `**Key Findings:**\n\n`;
            section.key_points.forEach(kp => { md += `- ${kp}\n`; });
            md += '\n';
        }
    });

    const takeaways = report.key_takeaways || [];
    if (takeaways.length) {
        md += `## Key Takeaways\n\n`;
        takeaways.forEach((t, i) => { md += `${i + 1}. ${t}\n`; });
        md += '\n';
    }

    if (report.conclusion) {
        md += `## Conclusion\n\n${report.conclusion}\n\n`;
    }

    const sources = report.sources_used || [];
    if (sources.length) {
        md += `## References\n\n`;
        sources.forEach(src => {
            md += `[${src.ref_id}] ${src.title || 'Untitled'} — ${src.url || ''}\n\n`;
        });
    }

    return md;
}


// ══════════════════════════════════════════════
// TOAST NOTIFICATIONS (same as main)
// ══════════════════════════════════════════════

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    toast.innerHTML = `<span>${icons[type] || ''}</span> ${message}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
