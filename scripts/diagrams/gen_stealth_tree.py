import urllib.request, zlib, base64, os

def encode(text):
    return base64.urlsafe_b64encode(zlib.compress(text.encode('utf-8'))).decode('ascii')

def save_png(diagram_type, source, filename):
    url = f'https://kroki.io/{diagram_type}/png/{encode(source)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        with open(filename, 'wb') as f:
            f.write(r.read())
    print(f'Saved: {filename}')

# Stealth Extraction Decision Tree — from scraper_service.py
diagram = r"""
graph TD
    A([Start: extract url]) --> B{Is domain in\nSTEALTH_PRIORITY_DOMAINS?\nresearchgate, ieee, springer,\nsciencedirect, nature,\nwiley, tandfonline, sagepub}

    B -->|YES| C[_stealth_extract url\nUsing Scrapling\nStealthyFetcher]
    B -->|NO| D[_standard_extract url\nRequests + Standard\nUser-Agent, timeout=15s]

    D --> E{HTTP Status\nCode?}
    E -->|403 / 429 / 503| F[Blocked by server]
    E -->|200 OK| G{Bot detection\nstring found in HTML?}

    G -->|YES\ncaptcha / cf-turnstile\nAccess Denied etc| F
    G -->|NO| H{Content length\n>= 200 chars?}

    H -->|NO - too short| F
    H -->|YES| I([Return Result\nmethod used = standard\nsuccess = True])

    F --> J{Is Scrapling\navailable?}
    J -->|NO - not installed| K([Return Result\nmethod used = failed\nsuccess = False])
    J -->|YES| C

    C --> L{Scrapling fetch\nHTTP status = 200\nand text length >= 200?}
    L -->|YES| M([Return Result\nmethod used = stealth\nsuccess = True])
    L -->|NO| K

    style A fill:#4A90D9,color:#fff,stroke:#2C5F8A
    style I fill:#27AE60,color:#fff,stroke:#1E8449
    style M fill:#27AE60,color:#fff,stroke:#1E8449
    style K fill:#E74C3C,color:#fff,stroke:#C0392B
    style B fill:#F39C12,color:#fff,stroke:#D68910
    style E fill:#F39C12,color:#fff,stroke:#D68910
    style G fill:#F39C12,color:#fff,stroke:#D68910
    style H fill:#F39C12,color:#fff,stroke:#D68910
    style J fill:#F39C12,color:#fff,stroke:#D68910
    style L fill:#F39C12,color:#fff,stroke:#D68910
    style F fill:#EC407A,color:#fff,stroke:#AD1457
    style C fill:#8E44AD,color:#fff,stroke:#6C3483
    style D fill:#2980B9,color:#fff,stroke:#1A5276
"""

os.makedirs('output', exist_ok=True)
save_png('mermaid', diagram, 'output/StealthExtraction_DecisionTree.png')
