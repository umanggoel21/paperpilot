import urllib.request
import zlib
import base64
import os

def encode(text):
    compressed = zlib.compress(text.encode('utf-8'))
    b64 = base64.urlsafe_b64encode(compressed).decode('ascii')
    return b64

def generate_diagram(diagram_type, source, output_filename):
    url = f'https://kroki.io/{diagram_type}/png/{encode(source)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            with open(output_filename, 'wb') as f:
                f.write(response.read())
        print(f'Successfully created: {output_filename}')
    except Exception as e:
        print(f'Error creating {output_filename}: {e}')

os.makedirs('output', exist_ok=True)

# 1. Use Case Diagram
generate_diagram('plantuml', '''
@startuml
left to right direction
actor "Researcher" as R
actor "Tavily API" as T
actor "Groq API" as G
rectangle "PaperPilot System" {
  usecase "Run Lite Research" as UC1
  usecase "Run Pro Research" as UC2
  usecase "Run Deep Research" as UC3
  usecase "Verify Evidence (RAG)" as UC4
  usecase "Use Document Editor" as UC5
}
R --> UC1
R --> UC2
R --> UC3
R --> UC4
R --> UC5
UC1 --> T
UC2 --> T
UC3 --> T
UC1 --> G
UC2 --> G
UC3 --> G
@enduml
''', 'output/01_UseCaseDiagram.png')

# 2. System Architecture
generate_diagram('plantuml', '''
@startuml
package "Layer 1: Frontend" {
    [index.html] as UI1
    [editor.html] as UI2
}
package "Layer 2: API & Logic" {
    [api_server.py] as API
    [paper_fetch.py]
    [pro_research.py]
}
database "Layer 3: Data" {
    [paperpilot.db]
    [ChromaDB]
}
cloud "External APIs" {
    [Tavily]
    [Groq LLaMA]
}
UI1 --> API
UI2 --> API
API --> [paper_fetch.py]
API --> [pro_research.py]
[paper_fetch.py] --> Tavily
[pro_research.py] --> Groq
API --> [paperpilot.db]
@enduml
''', 'output/02_SystemArchitecture.png')

# 3. User Flow
generate_diagram('mermaid', '''
graph TD
A[Home index.html] --> B{Choose Mode}
B -->|Lite| C[Search & Extract]
B -->|Deep| D[Answer 3 Qs Modal]
B -->|Pro| E[Intake Form Modal]
C --> F[Results View]
D --> F
E --> G[Agent Terminal] --> F
F --> H[Download PDF]
F --> I[Open Editor]
F --> J[Verify Evidence]
I --> K[Export Markdown/PDF]
''', 'output/03_UserFlow.png')

# 4. ERD
generate_diagram('mermaid', '''
erDiagram
    research_sessions {
        INTEGER id PK
        VARCHAR session_id UK
        VARCHAR topic
        VARCHAR mode
        TEXT report_json
        DATETIME created_at
    }
''', 'output/04_ERD.png')

# 5. DFD Level 0
generate_diagram('mermaid', '''
graph LR
U((User)) -->|Query & Config| S[PaperPilot System]
S -->|JSON/PDF Report| U
S -->|Search Request| T((Tavily API))
T -->|Raw Web Data| S
S -->|Context & Prompts| G((Groq LLaMA))
G -->|Synthesized Data| S
S -->|Agent Commands| P((Playwright))
P -->|DOM Content| S
''', 'output/05_DFD_Context.png')

# 6. Sequence Diagram
generate_diagram('mermaid', '''
sequenceDiagram
    participant UI as Frontend
    participant API as api_server
    participant Pro as pro_research
    participant T as Tavily
    participant G as Groq
    participant DB as SQLite

    UI->>API: POST /api/pro/execute
    API->>Pro: run execution
    Pro->>T: Search Queries
    T-->>Pro: URL list
    Pro->>T: Extract Content
    T-->>Pro: Raw HTML/Text
    Pro->>G: Prompt + Context
    G-->>Pro: Final JSON Report
    Pro-->>API: JSON Dict
    API->>DB: Save Session
    API-->>UI: Return JSON
''', 'output/06_Sequence_ProResearch.png')

# 7. Lite Pipeline
generate_diagram('mermaid', '''
graph TD
Start --> CheckCache{In Cache?}
CheckCache -->|Yes| Return[Return JSON]
CheckCache -->|No| Search[Tavily Search]
Search --> Extract[Tavily Extract URLs]
Extract --> Prompt[Build Context Prompt]
Prompt --> Groq[Call Groq LLaMA]
Groq --> Cache[Save to Cache]
Cache --> Return
Return --> End
''', 'output/07_Flow_LitePipeline.png')

# 8. RAG Pipeline
generate_diagram('mermaid', '''
graph TD
subgraph Indexing
A[Raw Extracted Text] --> B[Chunk Text]
B --> C[Sentence Transformers Embed]
C --> D[(ChromaDB)]
end
subgraph Querying
E[User Clicks Claim] --> F[Encode Claim]
F --> G{Chroma Similarity}
G --> D
D --> H[Return Top 3 Snippets]
H --> I[Highlight Evidence]
end
''', 'output/08_Flow_RAG_Evidence.png')

# 9. PDF Pipeline
generate_diagram('mermaid', '''
graph TD
A[JSON Report Data] --> B[Init ReportLab Canvas]
B --> C[Draw Title & Metadata]
C --> D[Draw Abstract]
D --> E[Loop Sections]
E --> F[Draw Paragraphs & Key Points]
F --> G[Draw References]
G --> H[Save PDF to Disk]
H --> I[Return Bytes to Client]
''', 'output/09_Flow_PDF_Gen.png')

print("All 9 diagrams generated successfully.")
