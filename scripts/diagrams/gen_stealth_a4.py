import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# A4 at 300 DPI = 8.27 x 11.69 inches (portrait)
fig, ax = plt.subplots(figsize=(8.27, 11.69), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 145)
ax.axis('off')
fig.patch.set_facecolor('#FFFFFF')

# ─── Color palette ───
C_BLUE    = '#2980B9'
C_GREEN   = '#27AE60'
C_RED     = '#E74C3C'
C_ORANGE  = '#E67E22'
C_PURPLE  = '#8E44AD'
C_PINK    = '#C0392B'
C_DARK    = '#2C3E50'
C_WHITE   = '#FFFFFF'
C_LBLUE   = '#EBF5FB'
C_BG      = '#F8F9FA'

def box(ax, x, y, w, h, text, facecolor, textcolor='white', fontsize=6.5,
        style='round,pad=0.1', bold=False):
    fancy = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle=style, linewidth=0.8,
                           edgecolor='white', facecolor=facecolor,
                           zorder=3)
    ax.add_patch(fancy)
    weight = 'bold' if bold else 'normal'
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            color=textcolor, fontweight=weight, zorder=4,
            multialignment='center', linespacing=1.4)

def diamond(ax, x, y, w, h, text, facecolor, textcolor='white', fontsize=6):
    dx, dy = w/2, h/2
    pts = [[x, y+dy], [x+dx, y], [x, y-dy], [x-dx, y]]
    poly = plt.Polygon(pts, closed=True, facecolor=facecolor,
                       edgecolor='white', linewidth=0.8, zorder=3)
    ax.add_patch(poly)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            color=textcolor, fontweight='bold', zorder=4,
            multialignment='center', linespacing=1.4)

def arrow(ax, x1, y1, x2, y2, label='', label_side='right', color='#555555'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=1.2, connectionstyle='arc3,rad=0.0'),
                zorder=2)
    if label:
        mx = (x1+x2)/2
        my = (y1+y2)/2
        offx = 2 if label_side == 'right' else -2
        ax.text(mx+offx, my, label, fontsize=5.5, color=color,
                fontweight='bold', ha='center', va='center', zorder=5,
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor='none', alpha=0.85))

def harrow(ax, x1, y1, x2, y2, label='', color='#555555'):
    """L-shaped horizontal then vertical arrow."""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.2,
                                connectionstyle=f'angle,angleA=0,angleB=90'),
                zorder=2)
    if label:
        ax.text((x1+x2)/2, y1+0.8, label, fontsize=5.5, color=color,
                fontweight='bold', ha='center', va='center', zorder=5,
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor='none', alpha=0.85))

# ─────────────────────────────────────────────
# BACKGROUND card
# ─────────────────────────────────────────────
bg = FancyBboxPatch((2, 1), 96, 143, boxstyle='round,pad=0.5',
                    facecolor=C_BG, edgecolor='#DDDDDD', linewidth=1, zorder=0)
ax.add_patch(bg)

# ─────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────
ax.text(50, 140, 'Stealth Extraction Decision Tree', ha='center', va='center',
        fontsize=12, fontweight='bold', color=C_DARK, zorder=5)
ax.text(50, 137.2, 'PaperPilot  ·  scraper_service.py  ·  StealthScraper.extract()',
        ha='center', va='center', fontsize=6, color='#777777', zorder=5)

# Title underline
ax.plot([10, 90], [135.8, 135.8], color='#CCCCCC', lw=0.8, zorder=2)

# ─────────────────────────────────────────────
# NODE DEFINITIONS  (x, y)
# ─────────────────────────────────────────────
# START
box(ax, 50, 132, 34, 4.5,
    'START\nStealthScraper.extract(url)',
    C_BLUE, fontsize=7, bold=True)

# D1 — stealth priority domain?
diamond(ax, 50, 122, 46, 9,
        'Is domain in\nSTEALTH_PRIORITY_DOMAINS?\n(8 domains: researchgate, ieee,\nspringer, sciencedirect,\nnature, wiley, tandfonline, sagepub)',
        C_ORANGE, fontsize=5.8)

# Standard extract box
box(ax, 22, 108, 30, 6,
    '_standard_extract(url)\nrequests.get()  timeout=15s\nUser-Agent: Chrome/131',
    C_BLUE, fontsize=6)

# Stealth extract box (first path)
box(ax, 78, 108, 30, 6,
    '_stealth_extract(url)\nScrapling StealthyFetcher\nBypasses Cloudflare / bot walls',
    C_PURPLE, fontsize=6)

# D2 — HTTP status
diamond(ax, 22, 95, 30, 7,
        'HTTP Status Code?\n403 / 429 / 503?',
        C_ORANGE, fontsize=6)

# D3 — bot detection string
diamond(ax, 22, 82, 34, 7.5,
        'Bot detection string\nin HTML response?\n(captcha / cf-turnstile /\nAccess Denied / recaptcha\nhCaptcha / challenge-platform)',
        C_ORANGE, fontsize=5.5)

# D4 — content length standard
diamond(ax, 22, 69, 28, 7,
        'Content length\n>= 200 chars?',
        C_ORANGE, fontsize=6)

# SUCCESS — standard
box(ax, 22, 58.5, 30, 5.5,
    'RETURN  success=True\nmethod_used = "standard"\nword_count = len(text.split())',
    C_GREEN, fontsize=6, bold=True)

# BLOCKED — intermediate
box(ax, 22, 45, 28, 5,
    'BLOCKED / FAILED\nFall through to stealth check',
    C_PINK, fontsize=6)

# D5 — scrapling available?
diamond(ax, 50, 35, 34, 7,
        'Is Scrapling library\navailable?\n(pip install scrapling)',
        C_ORANGE, fontsize=6)

# FAILED terminal
box(ax, 22, 22, 30, 5.5,
    'RETURN  success=False\nmethod_used = "failed"\ntext = ""',
    C_RED, fontsize=6, bold=True)

# D6 — stealth result valid?
diamond(ax, 78, 35, 30, 7,
        'Stealth result valid?\nHTTP 200 AND\nlength >= 200 chars',
        C_ORANGE, fontsize=5.8)

# SUCCESS — stealth
box(ax, 78, 22, 30, 5.5,
    'RETURN  success=True\nmethod_used = "stealth"\nword_count = len(text.split())',
    C_GREEN, fontsize=6, bold=True)

# ─────────────────────────────────────────────
# ARROWS
# ─────────────────────────────────────────────
# Start -> D1
arrow(ax, 50, 129.7, 50, 126.5)

# D1 -> Standard (NO)
ax.annotate('', xy=(22, 111), xytext=(27, 122),
            arrowprops=dict(arrowstyle='->', color='#555', lw=1.2,
                            connectionstyle='arc3,rad=0'), zorder=2)
ax.text(18, 118, 'NO', fontsize=6, color=C_GREEN, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))

# D1 -> Stealth direct (YES)
ax.annotate('', xy=(78, 111), xytext=(73, 122),
            arrowprops=dict(arrowstyle='->', color='#555', lw=1.2,
                            connectionstyle='arc3,rad=0'), zorder=2)
ax.text(82, 118, 'YES\n(skip standard)', fontsize=5.5, color=C_RED,
        fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))

# Standard -> D2
arrow(ax, 22, 105, 22, 98.5)

# D2 -> blocked (YES - 403/429/503)
ax.annotate('', xy=(22, 47.5), xytext=(22, 91.5),
            arrowprops=dict(arrowstyle='->', color='#555', lw=1.2), zorder=2)
ax.text(16, 86.5, 'YES\nBlocked', fontsize=5.5, color=C_RED,
        fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))

# D2 -> D3 (NO - 200 OK)
arrow(ax, 22, 91.5, 22, 85.7, label='NO  (200 OK)', label_side='right')

# D3 -> blocked (YES - bot detected)
# already connected via vertical line from D2->blocked
ax.annotate('', xy=(22, 47.5), xytext=(22, 78.2),
            arrowprops=dict(arrowstyle='->', color='#555', lw=1.2), zorder=2)
ax.text(16, 73, 'YES\nBot Found', fontsize=5.5, color=C_RED,
        fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))

# D3 -> D4 (NO - clean)
arrow(ax, 22, 78.2, 22, 72.5, label='NO  (Clean)', label_side='right')

# D4 -> SUCCESS standard (YES)
arrow(ax, 22, 65.5, 22, 61.2, label='YES', label_side='right')

# D4 -> blocked (NO - too short)
ax.annotate('', xy=(36, 45), xytext=(36, 69),
            arrowprops=dict(arrowstyle='->', color='#555', lw=1.2), zorder=2)
ax.text(40, 62, 'NO\n< 200 chars', fontsize=5.5, color=C_RED,
        fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))

# BLOCKED -> D5
arrow(ax, 22, 42.5, 33, 35)

# Stealth (direct) -> D6
arrow(ax, 78, 105, 78, 38.5)

# D5 -> FAILED (NO)
arrow(ax, 33, 35, 22, 24.7, label='NO', label_side='left')

# D5 -> Stealth (YES)
ax.annotate('', xy=(63, 35), xytext=(67, 35),
            arrowprops=dict(arrowstyle='->', color='#555', lw=1.2), zorder=2)
ax.text(62, 37.5, 'YES', fontsize=6, color=C_GREEN, fontweight='bold',
        ha='center',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))

# D6 -> SUCCESS stealth (YES)
arrow(ax, 78, 31.5, 78, 24.7, label='YES', label_side='right')

# D6 -> FAILED (NO)
ax.annotate('', xy=(37, 22), xytext=(63, 35),
            arrowprops=dict(arrowstyle='->', color='#555', lw=1.2,
                            connectionstyle='arc3,rad=-0.2'), zorder=2)
ax.text(46, 25, 'NO', fontsize=6, color=C_RED, fontweight='bold',
        ha='center',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none'))

# ─────────────────────────────────────────────
# LEGEND
# ─────────────────────────────────────────────
legend_items = [
    (C_BLUE,   'Standard HTTP Request'),
    (C_PURPLE, 'Scrapling Stealth Browser'),
    (C_ORANGE, 'Decision / Condition'),
    (C_GREEN,  'Success Result'),
    (C_RED,    'Failure Result'),
    (C_PINK,   'Blocked / Fallthrough'),
]
lx, ly = 6, 14
ax.text(lx, ly+2, 'Legend', fontsize=6.5, fontweight='bold', color=C_DARK)
for i, (col, label) in enumerate(legend_items):
    row = i % 3
    col_off = (i // 3) * 42
    rect = FancyBboxPatch((lx + col_off, ly - row*3.2 - 0.8), 3.5, 2.2,
                          boxstyle='round,pad=0.1', facecolor=col,
                          edgecolor='white', lw=0.5, zorder=3)
    ax.add_patch(rect)
    ax.text(lx + col_off + 4.5, ly - row*3.2 + 0.3, label,
            fontsize=5.8, color=C_DARK, va='center', zorder=4)

# Footer
ax.text(50, 2.5, 'PaperPilot  ·  scraper_service.py  ·  StealthScraper.extract()  ·  Lines 221–268',
        ha='center', va='center', fontsize=5, color='#AAAAAA')

os.makedirs('output', exist_ok=True)
plt.tight_layout(pad=0)
plt.savefig('output/StealthExtraction_A4.png', dpi=300, bbox_inches='tight',
            facecolor='white', format='png')
plt.close()
print('Saved: output/StealthExtraction_A4.png')
