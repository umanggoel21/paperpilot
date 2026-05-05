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

uml = r"""
@startuml
skinparam actorStyle awesome
skinparam backgroundColor #FFFFFF
skinparam usecase {
  BackgroundColor #DDEEFF
  BorderColor #336699
}
skinparam actor {
  BackgroundColor #FFFFFF
  BorderColor #333333
}

title PaperPilot - Use Case Diagram

left to right direction

actor "User / Researcher" as User

rectangle "PaperPilot" {
  usecase "Search Research Topic" as UC1
  usecase "Run Lite Research" as UC2
  usecase "Run Deep Research" as UC3
  usecase "Run Pro Research" as UC4
  usecase "View Research Report" as UC5
  usecase "Verify Evidence" as UC6
  usecase "Download PDF" as UC7
  usecase "Edit Document" as UC8
  usecase "View History" as UC9
}

User --> UC1
User --> UC2
User --> UC3
User --> UC4
User --> UC5
User --> UC6
User --> UC7
User --> UC8
User --> UC9

UC1 ..> UC2 : extends
UC1 ..> UC3 : extends
UC1 ..> UC4 : extends
UC5 ..> UC6 : include
UC5 ..> UC7 : include
UC5 ..> UC8 : include
@enduml
"""

os.makedirs('output', exist_ok=True)
save_png('plantuml', uml, 'output/UseCaseDiagram_Simple.png')
