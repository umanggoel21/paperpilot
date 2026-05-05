/**
 * PaperPilot — Professional Frontend
 * ====================================
 * Features:
 * - Backend API integration
 * - Skeleton loading states
 * - Real progress tracking
 * - Collapsible result sections
 * - Toast notifications
 * - Keyboard shortcuts
 * - localStorage search history
 * - Markdown export
 * - Source quality indicators
 * - Editable report sections
 * - Copy to clipboard
 */

// ══════════════════════════════════════════════
// CONFIG
// ══════════════════════════════════════════════

const API_BASE = window.location.origin;
const HISTORY_KEY = 'paperpilot_history';
const MAX_HISTORY = 8;

// Source quality scoring
const SOURCE_QUALITY = {
    'research_paper': { score: 95, label: 'High', color: 'quality-high' },
    'wikipedia':      { score: 70, label: 'Medium', color: 'quality-medium' },
    'article_blog':   { score: 50, label: 'Low', color: 'quality-low' },
};


// ══════════════════════════════════════════════
// 1. NAVIGATION — Scroll effect
// ══════════════════════════════════════════════

function initNavScroll() {
    const nav = document.getElementById('main-nav');
    if (!nav) return;

    window.addEventListener('scroll', () => {
        nav.classList.toggle('scrolled', window.scrollY > 20);
    }, { passive: true });
}


// ══════════════════════════════════════════════
// 2. SEARCH — Init & handlers
// ══════════════════════════════════════════════

function initSearch() {
    const input = document.getElementById('search-input');
    const btn = document.getElementById('search-btn');
    const chips = document.querySelectorAll('.search-chip');

    if (!input || !btn) return;

    // Suggestion chips
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            input.value = chip.dataset.topic;
            input.focus();
            runResearch(chip.dataset.topic);
        });
    });

    // Button click
    btn.addEventListener('click', () => {
        const topic = input.value.trim();
        if (topic) runResearch(topic);
    });

    // Enter key
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const topic = input.value.trim();
            if (topic) runResearch(topic);
        }
    });

    // Keyboard shortcut: / to focus search
    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== input && document.activeElement.tagName !== 'INPUT' && !document.activeElement.isContentEditable) {
            e.preventDefault();
            input.focus();
        }
        if (e.key === 'Escape' && document.activeElement === input) {
            input.blur();
        }
    });
}


// ══════════════════════════════════════════════
// 3. SEARCH HISTORY (localStorage)
// ══════════════════════════════════════════════

function loadHistory() {
    try {
        // One-time migration: clear corrupted data from v1
        const migrated = localStorage.getItem('paperpilot_history_v2');
        if (!migrated) {
            localStorage.removeItem(HISTORY_KEY);
            localStorage.setItem('paperpilot_history_v2', '1');
            return [];
        }

        const raw = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        // Sanitize any corrupted entries
        const clean = raw
            .filter(h => h && typeof h.topic === 'string')
            .map(h => ({
                ...h,
                topic: h.topic.replace(/[^\x20-\x7E]/g, '').trim().substring(0, 50),
            }))
            .filter(h => h.topic.length > 0 && h.topic.length < 50);
        // Persist cleaned data
        if (clean.length !== raw.length) {
            localStorage.setItem(HISTORY_KEY, JSON.stringify(clean));
        }
        return clean;
    } catch {
        localStorage.removeItem(HISTORY_KEY);
        return [];
    }
}

function saveToHistory(topic, totalSources) {
    // Sanitize topic: strip non-printable chars, truncate to 50 chars
    const cleanTopic = (topic || '').replace(/[^\x20-\x7E]/g, '').trim().substring(0, 50);
    if (!cleanTopic) return;

    const history = loadHistory();

    // Remove duplicate if exists
    const idx = history.findIndex(h => h.topic.toLowerCase() === cleanTopic.toLowerCase());
    if (idx !== -1) history.splice(idx, 1);

    // Add to front
    history.unshift({
        topic: cleanTopic,
        totalSources,
        timestamp: new Date().toISOString(),
    });

    // Cap size
    if (history.length > MAX_HISTORY) history.length = MAX_HISTORY;

    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    renderHistory();
}

function renderHistory() {
    const container = document.getElementById('recent-searches');
    const list = document.getElementById('recent-list');
    if (!container || !list) return;

    const history = loadHistory();

    if (history.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'flex';

    list.innerHTML = history.map(h => {
        const timeAgo = getTimeAgo(new Date(h.timestamp));
        return `<button class="recent-chip" data-topic="${escapeAttr(h.topic)}" title="${h.totalSources || 0} sources · ${timeAgo}">${escapeHtml(h.topic)}</button>`;
    }).join('');

    // Click handlers
    list.querySelectorAll('.recent-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const input = document.getElementById('search-input');
            if (input) input.value = chip.dataset.topic;
            runResearch(chip.dataset.topic);
        });
    });
}

function getTimeAgo(date) {
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}


// ══════════════════════════════════════════════
// 4. PROGRESS TRACKER
// ══════════════════════════════════════════════

function showProgress() {
    const tracker = document.getElementById('progress-tracker');
    if (!tracker) return;
    tracker.classList.add('visible');
    tracker.querySelectorAll('.progress-step').forEach(s => {
        s.classList.remove('active', 'done');
    });
}

function setProgressStep(stepId) {
    const steps = ['step-search', 'step-extract', 'step-synthesize', 'step-done'];
    const idx = steps.indexOf(stepId);

    steps.forEach((id, i) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.remove('active', 'done');
        if (i < idx) el.classList.add('done');
        if (i === idx) el.classList.add('active');
    });
}

function hideProgress() {
    const tracker = document.getElementById('progress-tracker');
    if (tracker) tracker.classList.remove('visible');
}


// ══════════════════════════════════════════════
// 5. SKELETON LOADING
// ══════════════════════════════════════════════

function showSkeleton() {
    const skeleton = document.getElementById('skeleton-section');
    const results = document.getElementById('results');
    // skeleton-section is optional; always hide results while loading
    if (skeleton) skeleton.style.display = 'block';
    if (results) results.style.display = 'none';
}

function hideSkeleton() {
    const skeleton = document.getElementById('skeleton-section');
    if (skeleton) skeleton.style.display = 'none';
    // ensure results area is visible after hiding skeleton
    const results = document.getElementById('results');
    if (results && results.dataset.hasReport) results.style.display = 'flex';
}


// ══════════════════════════════════════════════
// 6. RESEARCH — Main pipeline (mode-aware)
// ══════════════════════════════════════════════

// Current mode: 'lite', 'pro', or 'deep'
let currentMode = 'pro';

async function runResearch(topic) {
    // Reset compact mode if a previous search was shown
    const hero = document.getElementById('hero');
    if (hero) hero.classList.remove('compact-mode');
    document.getElementById('results')?.style && (document.getElementById('results').style.display = 'none');

    if (currentMode === 'pro') {
        // Pro mode opens the intake modal instead of running directly
        openProModal(topic);
        return;
    }
    if (currentMode === 'deep') {
        // Deep mode opens the deep research modal
        openDeepModal(topic);
        return;
    }
    // Lite mode: Standard research pipeline
    return runStandardResearch(topic);
}

async function runStandardResearch(topic) {
    const btn = document.getElementById('search-btn');

    btn.classList.add('loading');
    btn.disabled = true;

    showProgress();
    setProgressStep('step-search');

    showSkeleton();

    try {
        const response = await fetch(`${API_BASE}/api/research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic })
        });

        // Real event: server responded — sources found & extracted
        setProgressStep('step-extract');

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || `Server error (${response.status})`);
        }

        // Real event: parsing synthesis result
        setProgressStep('step-synthesize');
        const report = await response.json();

        if (report.error) {
            throw new Error(report.error);
        }

        setProgressStep('step-done');
        setTimeout(() => hideProgress(), 1500);

        hideSkeleton();
        displayResults(report);

        window.__lastReport = report;

        // Save to localStorage history
        saveToHistory(topic, report.total_sources || 0);

        const cacheNote = report.from_cache ? ' (cached)' : '';
        showToast(`Research complete${cacheNote} — report ready`, 'success');

    } catch (err) {
        console.error('Research error:', err);
        hideSkeleton();
        hideProgress();
        showError(err.message, topic);
        showToast(err.message, 'error');
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}


// ══════════════════════════════════════════════
// 7. DISPLAY RESULTS
// ══════════════════════════════════════════════

function displayResults(report) {
    const results = document.getElementById('results');
    const topicEl = document.getElementById('sidebar-topic');
    const metricsEl = document.getElementById('sidebar-metrics');
    const tocEl = document.getElementById('sidebar-toc');
    const breakdownEl = document.getElementById('sidebar-source-breakdown');
    
    const bodyEl = document.getElementById('report-content');
    const refsEl = document.getElementById('document-references');
    const metricsLeftEl = document.getElementById('metrics-left');

    topicEl.textContent = report.topic || 'Research Report';

    // Metrics
    const bd = report.source_breakdown || {};
    const elapsed = report.elapsed_seconds || '—';

    // Calculate overall source quality
    const paperCount = bd.research_papers || 0;
    const wikiCount = bd.wikipedia || 0;
    const blogCount = bd.articles_blogs || 0;
    const totalSources = report.total_sources || 0;
    const qualityScore = totalSources > 0
        ? Math.round((paperCount * 95 + wikiCount * 70 + blogCount * 50) / totalSources)
        : 0;
    const qualityLabel = qualityScore >= 80 ? 'High' : qualityScore >= 60 ? 'Medium' : 'Low';
    const qualityClass = qualityScore >= 80 ? 'quality-high' : qualityScore >= 60 ? 'quality-medium' : 'quality-low';

    metricsEl.innerHTML = `
        <div class="metric-row">
            <span class="metric-label">Sources</span>
            <span class="metric-val">${totalSources}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Quality</span>
            <span class="metric-val ${qualityClass}">${qualityScore}/100</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Time Elapsed</span>
            <span class="metric-val">${elapsed}s</span>
        </div>
    `;
    
    breakdownEl.innerHTML = `
        <div style="font-size: 0.75rem; color: var(--text-tertiary); text-align: center;">
            Papers: ${paperCount} &nbsp;|&nbsp; Wiki: ${wikiCount} &nbsp;|&nbsp; Articles: ${blogCount}
        </div>
    `;

    metricsLeftEl.innerHTML = `
        <span class="${qualityClass}" style="margin-right: 12px; font-weight: 700;">● ${qualityLabel} Confidence</span>
        <span>${totalSources} sources cited</span>
    `;

    // Build body and TOC
    let bodyHTML = '';
    let tocHTML = '';
    let sectionCount = 0;

    // Executive Summary
    const summary = report.enhanced_abstract || report.executive_summary || '';
    if (summary) {
        sectionCount++;
        const id = `sec-${sectionCount}`;
        tocHTML += `<a class="toc-item" onclick="document.getElementById('${id}').scrollIntoView({behavior:'smooth'})">Executive Summary</a>`;
        bodyHTML += buildSection('Executive Summary', `<p class="editable-content" contenteditable="true" data-field="executive_summary">${escapeHtml(summary)}</p>`, null, id);
    }

    // Sections
    const sections = report.sections || [];
    sections.forEach((section, i) => {
        sectionCount++;
        const id = `sec-${sectionCount}`;
        const title = section.title || `Section ${i + 1}`;
        tocHTML += `<a class="toc-item" onclick="document.getElementById('${id}').scrollIntoView({behavior:'smooth'})">${escapeHtml(title)}</a>`;
        
        const sectionContent = section.content || '';
        const keyPointsHTML = section.key_points && section.key_points.length
            ? `<ul class="key-points">${section.key_points.map(kp => `<li>${escapeHtml(kp)}</li>`).join('')}</ul>`
            : '';
            
        bodyHTML += buildSection(
            title,
            `<p class="editable-content" contenteditable="true" data-field="section-${i}">${escapeHtml(sectionContent)}</p>${keyPointsHTML}`,
            `§${i + 1}`,
            id
        );
    });

    // Key Takeaways
    const takeaways = report.key_takeaways || [];
    if (takeaways.length) {
        sectionCount++;
        const id = `sec-${sectionCount}`;
        tocHTML += `<a class="toc-item" onclick="document.getElementById('${id}').scrollIntoView({behavior:'smooth'})">Key Takeaways</a>`;
        const content = `<ul class="key-points">${takeaways.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul>`;
        bodyHTML += buildSection('Key Takeaways', content, null, id);
    }

    // Conclusion
    if (report.conclusion) {
        sectionCount++;
        const id = `sec-${sectionCount}`;
        tocHTML += `<a class="toc-item" onclick="document.getElementById('${id}').scrollIntoView({behavior:'smooth'})">Conclusion</a>`;
        bodyHTML += buildSection('Conclusion', `<p class="editable-content" contenteditable="true" data-field="conclusion">${escapeHtml(report.conclusion)}</p>`, null, id);
    }
    
    // Set HTML
    tocEl.innerHTML = tocHTML;
    bodyEl.innerHTML = bodyHTML;

    // References
    const sources = report.sources_used || [];
    if (sources.length) {
        tocEl.innerHTML += `<a class="toc-item" onclick="document.getElementById('document-references').scrollIntoView({behavior:'smooth'})" style="margin-top: 12px; font-weight: 600;">References</a>`;
        
        const refsContent = sources.map(src => {
            const typeClass = {
                'research_paper': 'ref-type-paper',
                'wikipedia': 'ref-type-wiki',
                'article_blog': 'ref-type-blog'
            }[src.source_type] || 'ref-type-paper';

            const typeLabel = {
                'research_paper': 'Paper',
                'wikipedia': 'Wiki',
                'article_blog': 'Article'
            }[src.source_type] || src.source_type;

            return `
                <div class="ref-item">
                    <span class="ref-id">[${src.ref_id}]</span>
                    <span class="ref-type ${typeClass}">${typeLabel}</span>
                    <a href="${escapeAttr(src.url || '#')}" target="_blank" rel="noopener" class="ref-link">${escapeHtml(src.title || 'Untitled')}</a>
                </div>
            `;
        }).join('');

        refsEl.innerHTML = `<h3>References</h3>${refsContent}`;
        refsEl.style.display = 'block';
    } else {
        refsEl.style.display = 'none';
    }

    results.style.display = 'flex';
    results.dataset.hasReport = '1';

    // Compact hero to mini bar
    const hero = document.getElementById('hero');
    if (hero) hero.classList.add('compact-mode');

    initEditableSync();
    
    // Automatically enable sentence clicking for verification if session exists
    if (window.__sessionId) {
        makeContentClickable();
    }

    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


function buildSection(title, content, label, id) {
    const labelHTML = label ? `<span class="doc-section-label">${label}</span> ` : '';
    return `
        <div class="doc-section" id="${id}">
            <h3>${labelHTML}${escapeHtml(title)}</h3>
            ${content}
        </div>
    `;
}


// ══════════════════════════════════════════════
// 8. EDITABLE SECTIONS — Sync edits to report
// ══════════════════════════════════════════════

function initEditableSync() {
    document.querySelectorAll('.editable-content').forEach(el => {
        el.addEventListener('blur', () => {
            syncEditToReport(el);
        });

        // Visual feedback on focus
        el.addEventListener('focus', () => {
            el.classList.add('editing');
        });
        el.addEventListener('blur', () => {
            el.classList.remove('editing');
        });
    });
}

function syncEditToReport(el) {
    const report = window.__lastReport;
    if (!report) return;

    const field = el.dataset.field;
    const newText = el.textContent.trim();

    if (field === 'executive_summary') {
        report.enhanced_abstract = newText;
        report.executive_summary = newText;
    } else if (field === 'conclusion') {
        report.conclusion = newText;
    } else if (field.startsWith('section-')) {
        const idx = parseInt(field.split('-')[1]);
        if (report.sections && report.sections[idx]) {
            report.sections[idx].content = newText;
        }
    }
}


// ══════════════════════════════════════════════
// 9. ERROR DISPLAY
// ══════════════════════════════════════════════

function showError(message, topic) {
    const results = document.getElementById('results');
    const topicEl = document.getElementById('results-topic');
    const metricsEl = document.getElementById('results-metrics');
    const bodyEl = document.getElementById('results-body');

    topicEl.textContent = `Error researching "${topic}"`;
    metricsEl.innerHTML = '';

    bodyEl.innerHTML = `
        <div class="error-section">
            <h4>Something went wrong</h4>
            <p>${escapeHtml(message)}</p>
            <div class="error-tips">
                <strong>Troubleshooting:</strong><br>
                • Make sure the Flask API server is running (<code>python api_server.py</code>)<br>
                • Check that GROQ_API_KEY and TAVILY_API_KEY are set in .env<br>
                • Try a different research topic
            </div>
        </div>
    `;

    results.style.display = 'block';
}


// ══════════════════════════════════════════════
// 10. PDF GENERATION
// ══════════════════════════════════════════════

async function generatePDF() {
    const report = window.__lastReport;
    if (!report) {
        showToast('No research report available. Run a search first.', 'error');
        return;
    }

    const btn = document.getElementById('btn-download-pdf');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Generating...';
    btn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ report, enhance: true })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || `PDF generation failed (${response.status})`);
        }

        const data = await response.json();

        if (data.pdf_base64) {
            const link = document.createElement('a');
            link.href = `data:application/pdf;base64,${data.pdf_base64}`;
            link.download = data.filename || 'research_report.pdf';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showToast('PDF downloaded successfully', 'success');
        } else if (data.pdf_url) {
            window.open(data.pdf_url, '_blank');
            showToast('PDF ready', 'success');
        }

    } catch (err) {
        console.error('PDF error:', err);
        showToast(`PDF failed: ${err.message}`, 'error');
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}


// ══════════════════════════════════════════════
// 11. JSON DOWNLOAD
// ══════════════════════════════════════════════

function downloadJSON() {
    const report = window.__lastReport;
    if (!report) {
        showToast('No report available. Run a search first.', 'error');
        return;
    }

    const json = JSON.stringify(report, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `${(report.topic || 'report').replace(/\s+/g, '_')}_report.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showToast('JSON exported', 'success');
}


// ══════════════════════════════════════════════
// 12. MARKDOWN EXPORT
// ══════════════════════════════════════════════

function downloadMarkdown() {
    const report = window.__lastReport;
    if (!report) {
        showToast('No report available. Run a search first.', 'error');
        return;
    }

    let md = `# ${report.topic || 'Research Report'}\n\n`;
    md += `*Generated: ${report.generated_at || new Date().toISOString()}*\n`;
    md += `*Sources: ${report.total_sources || 0}*\n\n---\n\n`;

    // Abstract
    const summary = report.enhanced_abstract || report.executive_summary || '';
    if (summary) {
        md += `## Abstract\n\n${summary}\n\n`;
    }

    // Sections
    const sections = report.sections || [];
    sections.forEach((section, i) => {
        md += `## ${i + 1}. ${section.title || 'Section'}\n\n`;
        md += `${section.content || ''}\n\n`;

        if (section.key_points && section.key_points.length) {
            md += `**Key Findings:**\n\n`;
            section.key_points.forEach(kp => {
                md += `- ${kp}\n`;
            });
            md += '\n';
        }
    });

    // Key Takeaways
    const takeaways = report.key_takeaways || [];
    if (takeaways.length) {
        md += `## Key Takeaways\n\n`;
        takeaways.forEach((t, i) => {
            md += `${i + 1}. ${t}\n`;
        });
        md += '\n';
    }

    // Conclusion
    if (report.conclusion) {
        md += `## Conclusion\n\n${report.conclusion}\n\n`;
    }

    // References
    const sources = report.sources_used || [];
    if (sources.length) {
        md += `## References\n\n`;
        sources.forEach(src => {
            const typeLabel = {
                'research_paper': 'Paper',
                'wikipedia': 'Wiki',
                'article_blog': 'Article'
            }[src.source_type] || src.source_type;

            md += `[${src.ref_id}] ${src.title || 'Untitled'} *(${typeLabel})* — ${src.url || ''}\n\n`;
        });
    }

    // Download
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${(report.topic || 'report').replace(/\s+/g, '_')}_report.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showToast('Markdown exported', 'success');
}


// ══════════════════════════════════════════════
// 13. COPY TO CLIPBOARD
// ══════════════════════════════════════════════

function copyToClipboard() {
    const report = window.__lastReport;
    if (!report) {
        showToast('No report available. Run a search first.', 'error');
        return;
    }

    const summary = report.enhanced_abstract || report.executive_summary || '';
    if (!summary) {
        showToast('No summary available to copy', 'error');
        return;
    }

    navigator.clipboard.writeText(summary).then(() => {
        showToast('Summary copied to clipboard', 'success');
    }).catch(() => {
        const textarea = document.createElement('textarea');
        textarea.value = summary;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Summary copied to clipboard', 'success');
    });
}


// ══════════════════════════════════════════════
// 14. TOAST NOTIFICATIONS
// ══════════════════════════════════════════════

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    toast.innerHTML = `<span>${icons[type] || ''}</span> ${escapeHtml(message)}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}


// ══════════════════════════════════════════════
// 15. SMOOTH SCROLL
// ══════════════════════════════════════════════

function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}


// ══════════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════════

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    if (!text) return '';
    return text.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}


// ══════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    initNavScroll();
    initSearch();
    initSmoothScroll();
    renderHistory();
    initDeepResearch();
    initModeToggle();
    initProSearch();

    // Health check
    fetch(`${API_BASE}/api/health`)
        .then(r => r.json())
        .then(data => {
            console.log('PaperPilot API:', data.status);
            if (data.cache) {
                console.log('Cache:', data.cache);
            }
            if (!data.keys_configured?.groq || !data.keys_configured?.tavily) {
                console.warn('API keys not fully configured.');
            }
        })
        .catch(() => {
            console.warn('PaperPilot API not reachable.');
        });
});


// ══════════════════════════════════════════════
// 14. DEEP RESEARCH — Modal Controller
// ══════════════════════════════════════════════

// Expose deepState so openDeepModal can update it
let _deepStateRef = null;

function initDeepResearch() {
    const modal = document.getElementById('deep-modal');
    const closeBtn = document.getElementById('modal-close');
    if (!modal) return;

    // State
    let deepState = {
        step: 1,
        topic: '',
        config: { sources: 5, length: 'medium', tone: 'professional', focus: 'overview' },
        questions: [],
        answers: [],
        plan: [],
        planFocus: '',
    };
    // Share reference so openDeepModal can set topic
    _deepStateRef = deepState;

    // ── Close modal ──
    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }

    // expose for openDeepModal
    deepState._open = function(topic) {
        deepState.topic = topic;
        deepState.step = 1;
        resetModal();
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    };

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') closeModal();
    });

    // ── Config chip selection (scoped to deep modal only) ──
    const deepCfgGroups = ['cfg-sources', 'cfg-length', 'cfg-tone', 'cfg-focus'];
    deepCfgGroups.forEach(groupId => {
        const group = document.getElementById(groupId);
        if (!group) return;
        group.addEventListener('click', (e) => {
            const chip = e.target.closest('.config-chip');
            if (!chip) return;
            group.querySelectorAll('.config-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');

            // Update config
            const val = chip.dataset.value;
            if (groupId === 'cfg-sources') deepState.config.sources = parseInt(val);
            if (groupId === 'cfg-length') deepState.config.length = val;
            if (groupId === 'cfg-tone') deepState.config.tone = val;
            if (groupId === 'cfg-focus') deepState.config.focus = val;
        });
    });

    // ── Step navigation ──
    function setStep(step) {
        deepState.step = step;
        document.querySelectorAll('.modal-panel').forEach(p => p.classList.remove('active'));
        document.getElementById(`deep-step-${step}`)?.classList.add('active');

        // Update step dots
        document.querySelectorAll('.modal-step-dot').forEach(dot => {
            const s = parseInt(dot.dataset.step);
            dot.classList.remove('active', 'done');
            if (s === step) dot.classList.add('active');
            else if (s < step) dot.classList.add('done');
        });
    }

    function resetModal() {
        setStep(1);
        // Reset config UI to stored values
        document.querySelectorAll('.config-options').forEach(group => {
            group.querySelectorAll('.config-chip').forEach(c => c.classList.remove('active'));
        });
        // Set defaults
        selectChip('cfg-sources', '5');
        selectChip('cfg-length', 'medium');
        selectChip('cfg-tone', 'professional');
        selectChip('cfg-focus', 'overview');
        // Reset state
        deepState.config = { sources: 5, length: 'medium', tone: 'professional', focus: 'overview' };
        deepState.questions = [];
        deepState.answers = [];
        deepState.plan = [];
    }

    function selectChip(groupId, value) {
        const group = document.getElementById(groupId);
        if (!group) return;
        group.querySelectorAll('.config-chip').forEach(c => {
            c.classList.toggle('active', c.dataset.value === String(value));
        });
    }

    // ── Step 1 → Step 2: Fetch AI questions ──
    document.getElementById('deep-next-1')?.addEventListener('click', async () => {
        setStep(2);
        const container = document.getElementById('deep-questions-container');
        container.innerHTML = '<div class="modal-loading"><span class="spinner"></span><span>Generating personalized questions...</span></div>';
        document.getElementById('deep-next-2').disabled = true;

        try {
            const res = await fetch(`${API_BASE}/api/deep/questions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: deepState.topic, config: deepState.config }),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error || 'Failed to generate questions');
            }

            const data = await res.json();
            deepState.questions = data.questions || [];

            // Show remaining uses
            const usesEl = document.getElementById('modal-uses');
            if (usesEl && data.remaining_uses !== undefined) {
                usesEl.textContent = `${data.remaining_uses} deep research uses remaining this month`;
            }

            // Render questions
            container.innerHTML = deepState.questions.map((q, i) => `
                <div class="question-item">
                    <div class="question-label">
                        <span class="question-number">${i + 1}</span>
                        <span>${escapeHtml(q.question)}</span>
                    </div>
                    <input type="text" class="question-input" id="q-answer-${i}" 
                           placeholder="${escapeAttr(q.placeholder || 'Your answer...')}"
                           data-qid="${i}">
                </div>
            `).join('');

            // Enable next button when at least one answer is given
            container.querySelectorAll('.question-input').forEach(input => {
                input.addEventListener('input', () => {
                    const answered = Array.from(container.querySelectorAll('.question-input'))
                        .some(inp => inp.value.trim().length > 0);
                    document.getElementById('deep-next-2').disabled = !answered;
                });
            });

        } catch (e) {
            container.innerHTML = `<div style="color:var(--error);text-align:center;padding:20px;">${escapeHtml(e.message)}</div>`;
            showToast(e.message, 'error');
        }
    });

    // ── Step 2 → Step 3: Fetch plan ──
    document.getElementById('deep-next-2')?.addEventListener('click', async () => {
        // Collect answers
        deepState.answers = deepState.questions.map((q, i) => ({
            question: q.question,
            answer: document.getElementById(`q-answer-${i}`)?.value?.trim() || '',
        }));

        setStep(3);
        const container = document.getElementById('deep-plan-container');
        container.innerHTML = '<div class="modal-loading"><span class="spinner"></span><span>Planning your research...</span></div>';

        try {
            const res = await fetch(`${API_BASE}/api/deep/plan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: deepState.topic,
                    config: deepState.config,
                    answers: deepState.answers,
                }),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error || 'Failed to generate plan');
            }

            const data = await res.json();
            deepState.plan = data.plan || [];
            deepState.planFocus = data.research_focus || '';

            // Render plan
            let html = '';
            if (deepState.planFocus) {
                html += `<div class="plan-focus">${escapeHtml(deepState.planFocus)}</div>`;
            }
            html += deepState.plan.map((p, i) => `
                <div class="plan-item">
                    <div class="plan-number">${i + 1}</div>
                    <div class="plan-info">
                        <h4>${escapeHtml(p.title)}</h4>
                        <p>${escapeHtml(p.description)}</p>
                    </div>
                </div>
            `).join('');

            if (data.estimated_time) {
                html += `<div style="text-align:center;font-size:0.75rem;color:var(--text-tertiary);padding-top:12px;">Estimated time: ${escapeHtml(data.estimated_time)}</div>`;
            }

            container.innerHTML = html;

        } catch (e) {
            container.innerHTML = `<div style="color:var(--error);text-align:center;padding:20px;">${escapeHtml(e.message)}</div>`;
            showToast(e.message, 'error');
        }
    });

    // ── Back buttons ──
    document.getElementById('deep-back-2')?.addEventListener('click', () => setStep(1));
    document.getElementById('deep-back-3')?.addEventListener('click', () => setStep(2));

    // ── Execute deep research ──
    document.getElementById('deep-execute')?.addEventListener('click', async () => {
        closeModal();
        showToast('Deep research started — this may take a minute', 'info');

        // Disable search button while running
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) { searchBtn.disabled = true; searchBtn.classList.add('loading'); }

        showProgress();
        setProgressStep('step-search');
        showSkeleton();

        try {
            setProgressStep('step-extract');

            const res = await fetch(`${API_BASE}/api/deep/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: deepState.topic,
                    config: deepState.config,
                    answers: deepState.answers,
                    plan: deepState.plan,
                }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `Server error (${res.status})`);
            }

            const report = await res.json();

            setProgressStep('step-synthesize');

            if (report.error) throw new Error(report.error);

            setProgressStep('step-done');
            setTimeout(() => hideProgress(), 1500);

            // Store for export
            window.__lastReport = report;

            // Add to history
            saveToHistory(deepState.topic, report.total_sources || 0);

            // Render using existing pipeline
            hideSkeleton();
            displayResults(report);

            showToast(`Deep research complete — ${report.total_sources} sources, ${report.sections?.length || 0} sections`, 'success');

        } catch (e) {
            console.error('Deep research error:', e);
            hideSkeleton();
            hideProgress();
            showError(e.message, deepState.topic);
            showToast(e.message, 'error');
        } finally {
            if (searchBtn) { searchBtn.disabled = false; searchBtn.classList.remove('loading'); }
        }
    });
}


// ══════════════════════════════════════════════
// 15. ENHANCED RESEARCH — RAG + Stealth Pipeline
// ══════════════════════════════════════════════

/**
 * Run enhanced research with stealth extraction + RAG indexing.
 * This replaces the standard runResearch() when the user wants evidence tracking.
 */
async function runEnhancedResearch(topic) {
    const btn = document.getElementById('search-btn');

    btn.classList.add('loading');
    btn.disabled = true;

    showProgress();
    setProgressStep('step-search');

    showSkeleton();

    try {
        const response = await fetch(`${API_BASE}/api/research/enhanced`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic })
        });

        // Real event: server responded — sources found & extracted
        setProgressStep('step-extract');

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || `Server error (${response.status})`);
        }

        // Real event: parsing synthesis result
        setProgressStep('step-synthesize');
        const report = await response.json();

        if (report.error) {
            throw new Error(report.error);
        }

        setProgressStep('step-done');
        setTimeout(() => hideProgress(), 1500);

        hideSkeleton();
        displayResults(report);

        // Show Evidence Panel if enhanced data is available
        if (report.enhanced && report.extraction_log) {
            displayEvidencePanel(report.extraction_log, report.rag_stats, report.session_id);
        }

        window.__lastReport = report;

        // Save to localStorage history
        saveToHistory(topic, report.total_sources || 0);

        const stealthCount = (report.extraction_log || []).filter(e => e.method === 'stealth').length;
        const cacheNote = report.from_cache ? ' (cached)' : '';
        showToast(
            `Enhanced research complete${cacheNote} — ${report.total_sources || 0} sources, ${stealthCount} stealth bypasses`,
            'success'
        );

    } catch (err) {
        console.error('Enhanced research error:', err);
        hideSkeleton();
        hideProgress();
        showError(err.message, topic);
        showToast(err.message, 'error');
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}


// ══════════════════════════════════════════════
// 16. EVIDENCE PANEL — Display & Interaction
// ══════════════════════════════════════════════

/**
 * Display the Evidence Panel with extraction log and RAG stats.
 */
function displayEvidencePanel(extractionLog, ragStats, sessionId) {
    const panel = document.getElementById('evidence-panel');
    const statsEl = document.getElementById('evidence-stats');
    const logEl = document.getElementById('evidence-log');

    if (!panel) return;

    // Store session ID globally for evidence queries
    window.__sessionId = sessionId;

    // Stats
    const standardCount = extractionLog.filter(e => e.method === 'standard').length;
    const stealthCount = extractionLog.filter(e => e.method === 'stealth').length;
    const failedCount = extractionLog.filter(e => e.method === 'failed').length;
    const totalWords = extractionLog.reduce((sum, e) => sum + (e.words || 0), 0);

    statsEl.innerHTML = `
        <div class="evidence-stat">
            <div class="evidence-stat-value">${ragStats?.total_chunks || 0}</div>
            <div class="evidence-stat-label">Chunks</div>
        </div>
        <div class="evidence-stat">
            <div class="evidence-stat-value">${totalWords.toLocaleString()}</div>
            <div class="evidence-stat-label">Words</div>
        </div>
        <div class="evidence-stat">
            <div class="evidence-stat-value">${stealthCount}</div>
            <div class="evidence-stat-label">Bypassed</div>
        </div>
    `;

    // Extraction log
    const logItems = extractionLog.map(entry => {
        const methodLabels = {
            'standard': '✓ Standard',
            'stealth': '⚡ Stealth',
            'failed': '✗ Failed'
        };
        const shortUrl = entry.url ? new URL(entry.url).hostname : 'unknown';

        return `
            <div class="evidence-log-item">
                <span class="evidence-log-dot ${entry.method}"></span>
                <span class="evidence-log-method ${entry.method}">${methodLabels[entry.method] || entry.method}</span>
                <span class="evidence-log-url" title="${escapeAttr(entry.url)}">${escapeHtml(entry.title || shortUrl)}</span>
                <span class="evidence-log-words">${entry.words?.toLocaleString() || 0} words</span>
            </div>
        `;
    }).join('');

    logEl.innerHTML = `
        <div class="evidence-log-title">Source Extraction Log</div>
        ${logItems}
    `;

    panel.style.display = 'block';

    // Make report sentences clickable for verification
    makeContentClickable();
}


/**
 * Make sentences in the report body clickable for evidence verification.
 */
function makeContentClickable() {
    const editables = document.querySelectorAll('.editable-content');

    editables.forEach(el => {
        const text = el.textContent;
        if (!text) return;

        // Split into sentences and wrap each in a clickable span
        const sentences = text.split(/(?<=[.!?])\s+/);
        el.innerHTML = sentences.map((s, i) =>
            `<span class="verifiable-sentence" data-idx="${i}" title="Click to verify this claim">${escapeHtml(s)}</span> `
        ).join('');

        // Add click handlers
        el.querySelectorAll('.verifiable-sentence').forEach(span => {
            span.addEventListener('click', (e) => {
                e.stopPropagation();
                const sentence = span.textContent.trim();
                if (sentence.length > 10 && window.__sessionId) {
                    verifyEvidence(sentence, window.__sessionId, span);
                }
            });
        });
    });
}


/**
 * Query the backend for evidence matching a clicked sentence.
 */
async function verifyEvidence(sentence, sessionId, spanEl) {
    const drawer = document.getElementById('evidence-drawer');
    const verifyResults = document.getElementById('evidence-verify-results');

    if (!drawer || !verifyResults) return;

    // Visual feedback on the clicked sentence
    document.querySelectorAll('.verifiable-sentence.verifying').forEach(el => el.classList.remove('verifying'));
    spanEl.classList.add('verifying');

    // Open drawer automatically
    drawer.classList.add('open');
    
    verifyResults.innerHTML = `
        <div style="text-align: center; padding: 40px 20px;">
            <span class="spinner" style="border-color: var(--border); border-top-color: var(--accent); width: 24px; height: 24px; margin-bottom: 16px;"></span>
            <div style="color: var(--text-secondary); font-size: 0.9375rem;">Searching indexed chunks...</div>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/api/evidence`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sentence, session_id: sessionId })
        });

        if (!response.ok) {
            throw new Error('Evidence query failed');
        }

        const data = await response.json();
        const evidence = data.evidence || [];

        spanEl.classList.remove('verifying');

        if (evidence.length === 0) {
            verifyResults.innerHTML = `
                <div class="match-card">
                    <div style="color: var(--text-secondary);">No matching source found for this claim. This may indicate the AI synthesized this from multiple partial sources.</div>
                </div>
            `;
            return;
        }

        verifyResults.innerHTML = evidence.map((ev, i) => `
            <div class="match-card">
                <div style="font-size: 0.75rem; font-weight: 700; color: var(--text-tertiary); margin-bottom: 8px;">
                    MATCH #${i + 1} — ${ev.similarity_score}% SIMILARITY
                </div>
                <div class="match-text">"${escapeHtml(ev.text)}"</div>
                <div style="margin-top: 12px; font-size: 0.8125rem;">
                    <a href="${escapeAttr(ev.source_url)}" class="match-source" target="_blank" rel="noopener">${escapeHtml(ev.source_title)}</a>
                    <span class="ref-type ref-type-${ev.source_type === 'research_paper' ? 'paper' : ev.source_type === 'wikipedia' ? 'wiki' : 'blog'}">${ev.source_type}</span>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error('Evidence verification error:', err);
        spanEl.classList.remove('verifying');
        verifyResults.innerHTML = `
            <div class="match-card">
                <div style="color: var(--error);">Evidence verification unavailable. The RAG engine may not be loaded yet.</div>
            </div>
        `;
    }
}

function toggleEvidenceDrawer() {
    const drawer = document.getElementById('evidence-drawer');
    if (drawer) {
        drawer.classList.toggle('open');
    }
}

function closeEvidenceDrawer() {
    const drawer = document.getElementById('evidence-drawer');
    if (drawer) {
        drawer.classList.remove('open');
    }
}


// ══════════════════════════════════════════════
// 17. MODE TOGGLE — Lite / Pro Switch
// ══════════════════════════════════════════════

function initModeToggle() {
    const selector = document.getElementById('mode-selector');
    if (!selector) return;

    const cards = selector.querySelectorAll('.mode-card');

    // Sync initial state
    const activeCard = selector.querySelector('.mode-card.active');
    if (activeCard) {
        currentMode = activeCard.dataset.mode;
    }

    cards.forEach(card => {
        card.addEventListener('click', () => {
            const mode = card.dataset.mode;
            currentMode = mode;

            cards.forEach(p => p.classList.remove('active'));
            card.classList.add('active');

            // Update search button text with opacity fade
            const searchBtnText = document.querySelector('.search-btn-text');
            if (searchBtnText) {
                searchBtnText.style.opacity = '0';
                setTimeout(() => {
                    searchBtnText.textContent = 'Research →';
                    searchBtnText.style.opacity = '1';
                }, 150);
            }
        });
    });
}

/**
 * Open the Deep Research modal (used by mode selector).
 */
function openDeepModal(topic) {
    const modal = document.getElementById('deep-modal');
    if (!modal) {
        showToast('Deep research modal not found', 'error');
        return;
    }
    const input = document.getElementById('search-input');
    if (!topic && input) topic = input.value.trim();
    if (!topic) {
        showToast('Enter a research topic first', 'error');
        input?.focus();
        return;
    }
    // Delegate to initDeepResearch state manager if available
    if (_deepStateRef && typeof _deepStateRef._open === 'function') {
        _deepStateRef._open(topic);
    } else {
        // Fallback: just open the modal
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}


// ══════════════════════════════════════════════
// 18. PRO SEARCH MODAL — Full Pipeline
// ══════════════════════════════════════════════

// Pro Search state
let proState = {
    topic: '',
    step: 1,
    chips: [],
    selectedSubTopics: [],
    plan: null,
    context: null,
};

function openProModal(topic) {
    const modal = document.getElementById('pro-modal');
    if (!modal) return;

    proState.topic = topic;
    proState.step = 1;
    proState.selectedSubTopics = [];
    proState.plan = null;
    proState.context = null;

    // Reset steps
    setProStep(1);

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // Load dynamic chips for Q5
    loadIntakeChips(topic);
}

function closeProModal() {
    const modal = document.getElementById('pro-modal');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = '';
}

function setProStep(step) {
    proState.step = step;
    document.querySelectorAll('#pro-modal .modal-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(`pro-step-${step}`)?.classList.add('active');

    // Update step dots
    document.querySelectorAll('#pro-modal .modal-step-dot').forEach(dot => {
        const s = parseInt(dot.dataset.step);
        dot.classList.remove('active', 'done');
        if (s === step) dot.classList.add('active');
        else if (s < step) dot.classList.add('done');
    });
}

async function loadIntakeChips(topic) {
    const container = document.getElementById('pro-subtopics');
    if (!container) return;

    container.innerHTML = `<div class="modal-loading" id="pro-chips-loading">
        <span class="spinner"></span>
        <span>Loading topic-specific options...</span>
    </div>`;

    try {
        const res = await fetch(`${API_BASE}/api/pro/intake-chips`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic }),
        });

        if (!res.ok) throw new Error('Failed to load chips');

        const data = await res.json();
        proState.chips = data.chips || [];

        container.innerHTML = proState.chips.map(chip =>
            `<button class="config-chip" data-value="${escapeAttr(chip)}" tabindex="0">${escapeHtml(chip)}</button>`
        ).join('');

        // Pre-select first 2 sub-topics
        const chipBtns = container.querySelectorAll('.config-chip');
        chipBtns.forEach((btn, i) => {
            if (i < 2) btn.classList.add('selected');

            btn.addEventListener('click', () => {
                btn.classList.toggle('selected');
                proState.selectedSubTopics = Array.from(container.querySelectorAll('.config-chip.selected'))
                    .map(el => el.dataset.value);
            });

            // Keyboard: Enter/Space to toggle
            btn.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    btn.click();
                }
            });
        });

        proState.selectedSubTopics = Array.from(container.querySelectorAll('.config-chip.selected'))
            .map(el => el.dataset.value);

    } catch (e) {
        container.innerHTML = `<div style="font-size:0.8rem;color:var(--text-tertiary);">Could not load subtopics — you can skip this.</div>`;
    }
}

function getChipValue(groupId) {
    const group = document.getElementById(groupId);
    if (!group) return '';
    const active = group.querySelector('.config-chip.active');
    return active ? active.dataset.value : '';
}

function initProSearch() {
    const modal = document.getElementById('pro-modal');
    if (!modal) return;

    // Close handlers
    document.getElementById('pro-modal-close')?.addEventListener('click', closeProModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeProModal();
    });

    // Config chip selection (single-select within Q1-Q4 groups)
    ['pro-purpose', 'pro-audience', 'pro-depth', 'pro-length', 'pro-tone'].forEach(groupId => {
        const group = document.getElementById(groupId);
        if (!group) return;
        group.addEventListener('click', (e) => {
            const chip = e.target.closest('.config-chip');
            if (!chip) return;
            group.querySelectorAll('.config-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
        });
        // Keyboard: Enter/Space
        group.querySelectorAll('.config-chip').forEach(chip => {
            chip.setAttribute('tabindex', '0');
            chip.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    chip.click();
                }
            });
        });
    });

    // Clickable breadcrumb step dots
    document.querySelectorAll('#pro-modal .modal-step-dot.clickable').forEach(dot => {
        const targetStep = parseInt(dot.dataset.step);
        dot.addEventListener('click', () => {
            // Only allow going back to completed steps, not forward
            if (targetStep < proState.step) {
                setProStep(targetStep);
            }
        });
        dot.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                if (targetStep < proState.step) {
                    setProStep(targetStep);
                }
            }
        });
    });

    // Step 1 → Step 2: Generate Plan
    document.getElementById('pro-next-1')?.addEventListener('click', async () => {
        const formData = {
            topic: proState.topic,
            purpose: getChipValue('pro-purpose'),
            audience: getChipValue('pro-audience'),
            depth: getChipValue('pro-depth'),
            length: getChipValue('pro-length'),
            tone: getChipValue('pro-tone'),
            sub_topics: proState.selectedSubTopics,
            custom_focus: document.getElementById('pro-custom-focus')?.value?.trim() || '',
        };

        setProStep(2);
        const container = document.getElementById('pro-plan-container');
        container.innerHTML = '<div class="modal-loading"><span class="spinner"></span><span>Generating your research plan...</span></div>';

        try {
            const res = await fetch(`${API_BASE}/api/pro/plan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error || 'Plan generation failed');
            }

            const data = await res.json();
            proState.plan = data;
            proState.context = data.context;

            // Render plan
            let html = '';
            if (data.research_focus) {
                html += `<div class="plan-focus">${escapeHtml(data.research_focus)}</div>`;
            }
            html += (data.plan || []).map((p, i) => `
                <div class="plan-item">
                    <div class="plan-number">${i + 1}</div>
                    <div class="plan-info">
                        <h4>${escapeHtml(p.title)}</h4>
                        <p>${escapeHtml(p.description)}</p>
                    </div>
                </div>
            `).join('');
            if (data.estimated_time) {
                html += `<div style="text-align:center;font-size:0.75rem;color:var(--text-tertiary);padding-top:12px;">Estimated time: ${escapeHtml(data.estimated_time)}</div>`;
            }
            container.innerHTML = html;

        } catch (e) {
            container.innerHTML = `<div style="color:var(--error);text-align:center;padding:20px;">${escapeHtml(e.message)}</div>`;
            showToast(e.message, 'error');
        }
    });

    // Back from Step 2 to Step 1
    document.getElementById('pro-back-2')?.addEventListener('click', () => setProStep(1));

    // Execute Pro Research — starts live browser agent + synthesis
    document.getElementById('pro-execute')?.addEventListener('click', async () => {
        if (!proState.plan || !proState.context) {
            showToast('No plan available. Go back and regenerate.', 'error');
            return;
        }

        setProStep(3);
        resetAgentTerminal();

        const topic = proState.topic;
        const searchQueries = proState.plan.search_queries || [`${topic} research`];

        // ── PHASE 1: Start browser agent ──
        setAgentPhase('agent');
        addAgentLog('system', 'Starting browser agent...');

        try {
            const startRes = await fetch(`${API_BASE}/api/agent/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, search_queries: searchQueries }),
            });

            if (!startRes.ok) {
                const err = await startRes.json();
                throw new Error(err.error || 'Failed to start agent');
            }

            const startData = await startRes.json();
            const agentSessionId = startData.session_id;

            addAgentLog('status', `Agent session: ${agentSessionId}`);
            updateAgentBadge('● Running', '');

            // ── Stream live events via SSE ──
            const agentResult = await streamAgentEvents(agentSessionId);

            // ── PHASE 2: Deep search + extraction ──
            setAgentPhase('search');
            addAgentLog('status', 'Running deep source search & extraction...');

            // ── PHASE 3: AI Synthesis ──
            setAgentPhase('synthesis');
            addAgentLog('status', '<span class="synthesizing-dot"></span>Synthesizing report with AI...');

            const execRes = await fetch(`${API_BASE}/api/pro/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    context: proState.context,
                    plan: proState.plan,
                    agent_findings: agentResult,
                }),
            });

            if (!execRes.ok) {
                const err = await execRes.json();
                throw new Error(err.error || 'Pro research failed');
            }

            const report = await execRes.json();

            if (report.error) throw new Error(report.error);

            addAgentLog('complete', `✓ Report ready — ${report.total_sources || 0} sources, ${report.sections?.length || 0} sections`);
            updateAgentBadge('● Complete', 'done');
            setAgentPhase('done');

            // Close modal after brief delay
            setTimeout(() => {
                closeProModal();
                window.__lastReport = report;
                saveToHistory(proState.topic, report.total_sources || 0);
                hideSkeleton();
                displayResults(report);
                showToast(`Pro research complete — ${report.total_sources} sources, ${report.sections?.length || 0} sections`, 'success');
            }, 1500);

        } catch (e) {
            addAgentLog('error', 'Agent encountered an issue -- falling back to standard search.');
            updateAgentBadge('● Fallback', 'error');

            // ── ACTUAL FALLBACK: Execute Pro Research WITHOUT browser agent ──
            try {
                setAgentPhase('search');
                addAgentLog('status', 'Running deep source search & extraction (no agent)...');
                setAgentPhase('synthesis');
                addAgentLog('status', '<span class="synthesizing-dot"></span>Synthesizing report with AI...');

                const fallbackRes = await fetch(`${API_BASE}/api/pro/execute`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        context: proState.context,
                        plan: proState.plan,
                        agent_findings: null,  // No agent data
                    }),
                });

                if (!fallbackRes.ok) {
                    const err = await fallbackRes.json();
                    throw new Error(err.error || 'Fallback research failed');
                }

                const report = await fallbackRes.json();
                if (report.error) throw new Error(report.error);

                addAgentLog('complete', `Report ready (fallback) -- ${report.total_sources || 0} sources, ${report.sections?.length || 0} sections`);
                updateAgentBadge('● Complete', 'done');
                setAgentPhase('done');

                setTimeout(() => {
                    closeProModal();
                    window.__lastReport = report;
                    saveToHistory(proState.topic, report.total_sources || 0);
                    hideSkeleton();
                    displayResults(report);
                    showToast(`Pro research complete -- ${report.total_sources} sources`, 'success');
                }, 1500);

            } catch (fallbackErr) {
                addAgentLog('error', `Fallback also failed: ${fallbackErr.message}`);
                updateAgentBadge('● Failed', 'error');
                showToast('Research failed. Please try again later.', 'error');
            }
        }
    });

    // Cancel button
    document.getElementById('agent-cancel-btn')?.addEventListener('click', () => {
        closeProModal();
        showToast('Agent cancelled', 'info');
    });
}


// ══════════════════════════════════════════════
// 19. LIVE AGENT TERMINAL HELPERS
// ══════════════════════════════════════════════

let agentStepCount = 0;
let agentPageCount = 0;
let agentFindingsCount = 0;
let screenshotPollTimer = null;

function resetAgentTerminal() {
    const log = document.getElementById('agent-log');
    if (log) log.innerHTML = '';
    agentStepCount = 0;
    agentPageCount = 0;
    agentFindingsCount = 0;
    updateAgentStats();
    updateAgentBadge('● Initializing', '');

    // Reset phases
    document.querySelectorAll('.agent-phase').forEach(p => {
        p.classList.remove('active', 'done');
    });

    // Reset virtual browser
    const screenshot = document.getElementById('vb-screenshot');
    const placeholder = document.getElementById('vb-placeholder');
    const urlText = document.getElementById('vb-url-text');
    const statusDot = document.getElementById('vb-status-dot');
    if (screenshot) { screenshot.style.display = 'none'; screenshot.src = ''; }
    if (placeholder) placeholder.style.display = 'flex';
    if (urlText) urlText.textContent = 'about:blank';
    if (statusDot) statusDot.className = 'vb-status-dot';
}

/**
 * Start polling the screenshot endpoint for the virtual browser tab.
 * Polls every 1.5s and updates the img + URL bar.
 */
function startScreenshotPolling(sessionId) {
    stopScreenshotPolling(); // Clear any existing timer

    screenshotPollTimer = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/agent/screenshot/${sessionId}`);
            if (!res.ok) return;

            const data = await res.json();
            if (!data.image) return; // No screenshot yet

            const screenshot = document.getElementById('vb-screenshot');
            const placeholder = document.getElementById('vb-placeholder');
            const urlText = document.getElementById('vb-url-text');

            if (screenshot && data.image) {
                screenshot.src = `data:image/jpeg;base64,${data.image}`;
                screenshot.style.display = 'block';
                screenshot.classList.remove('fresh');
                // Trigger reflow to restart animation
                void screenshot.offsetWidth;
                screenshot.classList.add('fresh');
                if (placeholder) placeholder.style.display = 'none';
            }

            if (urlText && data.url) {
                // Display a clean URL (strip protocol for space)
                try {
                    const u = new URL(data.url);
                    urlText.textContent = u.host + u.pathname + u.search;
                } catch {
                    urlText.textContent = data.url;
                }
            }
        } catch (e) {
            // Silently ignore polling errors
        }
    }, 1500);
}

function stopScreenshotPolling() {
    if (screenshotPollTimer) {
        clearInterval(screenshotPollTimer);
        screenshotPollTimer = null;
    }
    // Mark status dot as idle
    const statusDot = document.getElementById('vb-status-dot');
    if (statusDot) statusDot.classList.add('idle');
}

function addAgentLog(type, message) {
    const log = document.getElementById('agent-log');
    if (!log) return;

    const now = new Date();
    const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    const prefixMap = {
        system: '⚙',
        status: '→',
        step: '▸',
        error: '✕',
        complete: '✓',
    };

    const entry = document.createElement('div');
    entry.className = `agent-log-entry ${type}`;
    entry.innerHTML = `<span class="log-time">${time}</span><span class="log-prefix">${prefixMap[type] || '·'}</span><span class="log-msg">${escapeHtml(message)}</span>`;
    log.appendChild(entry);

    // Auto-scroll to bottom
    log.scrollTop = log.scrollHeight;

    // Update step counter
    if (type === 'step') {
        agentStepCount++;

        // Detect page visits from message content
        const msgLower = message.toLowerCase();
        if (msgLower.includes('navigate') || msgLower.includes('open') || msgLower.includes('click') || msgLower.includes('go to')) {
            agentPageCount++;
        }

        updateAgentStats();
    }
}

function updateAgentBadge(text, className) {
    const badge = document.getElementById('agent-status-badge');
    if (!badge) return;
    badge.textContent = text;
    badge.className = `terminal-status ${className || ''}`;
}

function updateAgentStats() {
    const steps = document.getElementById('agent-steps-count');
    const pages = document.getElementById('agent-pages-count');
    const findings = document.getElementById('agent-findings-count');
    if (steps) steps.textContent = agentStepCount;
    if (pages) pages.textContent = agentPageCount;
    if (findings) findings.textContent = agentFindingsCount;
}

function setAgentPhase(phase) {
    const phases = document.querySelectorAll('.agent-phase');
    const order = ['agent', 'search', 'synthesis'];

    if (phase === 'done') {
        phases.forEach(p => { p.classList.remove('active'); p.classList.add('done'); });
        return;
    }

    const targetIdx = order.indexOf(phase);
    phases.forEach(p => {
        const pPhase = p.dataset.phase;
        const idx = order.indexOf(pPhase);
        p.classList.remove('active', 'done');
        if (idx < targetIdx) p.classList.add('done');
        else if (idx === targetIdx) p.classList.add('active');
    });
}


// ══════════════════════════════════════════════
// 20. SSE AGENT EVENT STREAM
// ══════════════════════════════════════════════

function streamAgentEvents(sessionId) {
    return new Promise((resolve, reject) => {
        const eventSource = new EventSource(`${API_BASE}/api/agent/stream/${sessionId}`);

        let agentResult = null;
        let resolved = false;

        // Connection opened
        eventSource.onopen = () => {
            addAgentLog('status', 'Connected to agent stream');
        };

        // Status events
        eventSource.addEventListener('status', (e) => {
            try {
                const data = JSON.parse(e.data);
                addAgentLog('status', data.data?.message || 'Status update');
                updateAgentBadge(`● ${data.data?.phase || 'Running'}`, '');
            } catch {}
        });

        // Step events
        eventSource.addEventListener('step', (e) => {
            try {
                const data = JSON.parse(e.data);
                const msg = data.data?.message || `Step ${data.data?.step || '?'}`;
                addAgentLog('step', msg);
            } catch {}
        });

        // Complete event (agent finished)
        eventSource.addEventListener('complete', (e) => {
            try {
                const data = JSON.parse(e.data);
                agentResult = data.data?.result || {};
                agentFindingsCount = agentResult.findings?.length || 0;
                updateAgentStats();
                addAgentLog('complete', data.data?.message || 'Agent complete');
                updateAgentBadge('● Agent Done', 'done');
            } catch {}
        });

        // Error event
        eventSource.addEventListener('error', (e) => {
            try {
                const data = JSON.parse(e.data);
                addAgentLog('error', data.data?.message || 'Agent error');
            } catch {
                // SSE connection error (not a JSON event)
                if (eventSource.readyState === EventSource.CLOSED && !resolved) {
                    resolved = true;
                    eventSource.close();
                    resolve(agentResult || { findings: [], overall_summary: 'Agent stream ended' });
                }
            }
        });

        // Done event (stream finished)
        eventSource.addEventListener('done', () => {
            if (!resolved) {
                resolved = true;
                eventSource.close();
                resolve(agentResult || { findings: [], overall_summary: 'Agent completed' });
            }
        });

        // Standard error handler (connection lost)
        eventSource.onerror = () => {
            if (!resolved) {
                resolved = true;
                eventSource.close();
                // Don't reject — resolve with whatever we have
                resolve(agentResult || { findings: [], overall_summary: 'Agent stream connection ended' });
            }
        };

        // Safety timeout (2 minutes)
        setTimeout(() => {
            if (!resolved) {
                resolved = true;
                eventSource.close();
                addAgentLog('system', 'Agent timed out after 2 minutes');
                resolve(agentResult || { findings: [], overall_summary: 'Agent timed out' });
            }
        }, 120000);
    });
}


// ══════════════════════════════════════════════
// 21. OPEN IN EDITOR
// ══════════════════════════════════════════════

function openInEditor() {
    const report = window.__lastReport;
    if (!report) {
        showToast('No report available. Run research first.', 'error');
        return;
    }

    // Store report in sessionStorage for the editor page to pick up
    try {
        sessionStorage.setItem('paperpilot_editor_report', JSON.stringify(report));
    } catch (e) {
        showToast('Report too large for editor transfer.', 'error');
        return;
    }

    window.open('/editor', '_blank');
}


// ══════════════════════════════════════════════
// 22. INIT EVERYTHING
// ══════════════════════════════════════════════

// Add the extra initializations
document.addEventListener('DOMContentLoaded', () => {
    initModeToggle();
    initProSearch();
});

