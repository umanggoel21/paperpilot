# TITLE PAGE

---

**[College Logo Placeholder]**

**[YOUR COLLEGE NAME]**
Affiliated to Dr. A.P.J. Abdul Kalam Technical University, Lucknow

---

# PAPERPILOT: AN AI-POWERED AUTOMATED ACADEMIC LITERATURE REVIEW AND SYNTHESIS PLATFORM

---

*Project Report submitted in partial fulfillment of the requirement for the degree of*
**Bachelor of Technology**
*in*
**Computer Science and Engineering (Artificial Intelligence & Machine Learning)**

---

**Submitted by:**
[Student Name]
Enrollment No.: [Enrollment No.]
Branch: CSE (AI & ML)
Semester: VIII

**Under the Supervision of:**
[Supervisor Name]
[Supervisor Designation]
Department of Computer Science and Engineering

---

**Department of Computer Science and Engineering**
**Session: 2025–2026**

---
---

# DECLARATION

I, [Student Name], student of B.Tech VIII Semester, Department of Computer Science and Engineering, [College Name], hereby declare that the project report entitled **"PaperPilot: An AI-Powered Automated Academic Literature Review and Synthesis Platform"** submitted to Dr. A.P.J. Abdul Kalam Technical University, Lucknow, in partial fulfillment of the requirement for the award of the degree of Bachelor of Technology, is a record of bonafide work carried out by me under the supervision of [Supervisor Name].

I further declare that the work reported in this report has not been submitted, either in part or full, for the award of any other degree or diploma of this university or any other university or institution.

**Date:** ___________
**Place:** ___________

**[Student Name]**
Enrollment No.: [Enrollment No.]

---
---

# CERTIFICATE

This is to certify that the project report entitled **"PaperPilot: An AI-Powered Automated Academic Literature Review and Synthesis Platform"** submitted by [Student Name] (Enrollment No.: [Enrollment No.]) in partial fulfillment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering (AI & ML) from Dr. A.P.J. Abdul Kalam Technical University, Lucknow, is a record of bonafide project work carried out by the student under my supervision and guidance.

To the best of my knowledge and belief, the work has not been submitted, either in part or full, for any other degree or diploma to this university or any other institution.

**Date:** ___________
**Place:** ___________

**[Supervisor Name]**
[Supervisor Designation]
Department of Computer Science and Engineering
[College Name]

**Head of Department**
Department of Computer Science and Engineering
[College Name]

---
---

# ACKNOWLEDGEMENTS

The successful completion of this project would not have been possible without the guidance, support, and encouragement of several individuals, and the author wishes to express sincere gratitude to each of them.

First and foremost, the author extends deep appreciation to **[Supervisor Name]**, [Supervisor Designation], for providing invaluable academic guidance, constructive feedback, and continuous motivation throughout the development of this project. The supervisor's expertise in Artificial Intelligence and Software Engineering significantly shaped the technical direction of PaperPilot.

The author is equally grateful to **[HOD Name]**, Head of the Department of Computer Science and Engineering, for providing access to the necessary computing resources and for fostering an academic environment conducive to innovation.

Gratitude is also extended to all **faculty members** of the Department of Computer Science and Engineering for their academic support throughout the B.Tech programme, and to the **university library staff** for facilitating access to research databases and literature.

Finally, the author wishes to express heartfelt thanks to **family members and friends** whose unwavering moral support, patience, and encouragement throughout the duration of this work made its completion possible.

**[Student Name]**

---
---

# ABSTRACT

The exponential growth of academic literature in recent years has created a significant bottleneck for researchers, students, and analysts who require synthesised, credible insights from vast bodies of published work. Manually reviewing hundreds of research papers, extracting relevant information, and producing structured literature reviews is a time-intensive process that can span days or weeks. PaperPilot is an AI-powered automated academic literature review and synthesis platform developed to address this challenge directly. The system orchestrates a multi-phase data acquisition and synthesis pipeline that autonomously searches targeted academic repositories (including arXiv, PubMed, IEEE, and Springer), extracts full-text content, and synthesises coherent, citation-backed research reports using a state-of-the-art Large Language Model. The platform exposes three distinct research modes: Lite Mode for rapid single-pass synthesis, Deep Mode for conversational multi-turn scoping, and Pro Mode for a fully guided wizard-driven research pipeline incorporating live browser automation. The backend is implemented as a Python Flask REST API following the Model-View-Controller (MVC) architectural pattern, interfacing with the Groq API (LLaMA-3.3-70b-versatile model) for natural language synthesis and the Tavily API for targeted web search and content extraction. An evidence verification engine employing a hybrid fuzzy-matching algorithm (combining Python's difflib SequenceMatcher with keyword overlap scoring) enables users to verify any AI-generated claim against its original raw source. Professional-quality PDF reports are generated using the ReportLab library. The system achieves end-to-end report generation with multi-source synthesis and verifiable citations, representing a significant step beyond existing generic AI chatbot interfaces.

**Keywords:** Academic Literature Review, Artificial Intelligence, Large Language Model, Natural Language Processing, Retrieval-Augmented Generation, Flask API, Evidence Verification, Research Automation, LLaMA, Tavily

---
---

# TABLE OF CONTENTS

| Section | Title | Page |
|---------|-------|------|
| — | Title Page | i |
| — | Declaration | ii |
| — | Certificate | iii |
| — | Acknowledgements | iv |
| — | Abstract | v |
| — | Table of Contents | vi |
| — | List of Figures | vii |
| — | List of Tables | viii |
| — | List of Abbreviations | ix |
| **Chapter 1** | **Introduction** | 1 |
| 1.1 | Background and Motivation | 1 |
| 1.2 | Problem Statement | 3 |
| 1.3 | Objectives | 3 |
| 1.4 | Scope of the Project | 4 |
| 1.5 | Organisation of the Report | 4 |
| **Chapter 2** | **Literature Review** | 5 |
| 2.1 | Automated Information Retrieval Systems | 5 |
| 2.2 | Large Language Models for Text Synthesis | 6 |
| 2.3 | Retrieval-Augmented Generation (RAG) | 7 |
| 2.4 | Browser Automation and Web Scraping | 8 |
| 2.5 | Academic PDF Generation Tools | 9 |
| 2.6 | Summary of Literature Review | 9 |
| **Chapter 3** | **System Architecture and Design** | 10 |
| 3.1 | Architectural Overview | 10 |
| 3.2 | Presentation Layer | 11 |
| 3.3 | Application Layer | 12 |
| 3.4 | Service Layer | 12 |
| 3.5 | Data and Infrastructure Layer | 13 |
| 3.6 | Package and Folder Structure | 13 |
| **Chapter 4** | **Application Modules** | 15 |
| 4.1 | Home Screen and Search Interface | 15 |
| 4.2 | Pro Research Wizard | 15 |
| 4.3 | Live Agent Terminal | 16 |
| 4.4 | Results View | 16 |
| 4.5 | Document Editor | 17 |
| **Chapter 5** | **Functional Modules** | 18 |
| 5.1 | Lite Research Pipeline | 18 |
| 5.2 | Deep Research Pipeline | 19 |
| 5.3 | Pro Research Pipeline | 20 |
| 5.4 | Evidence Verification Engine | 21 |
| **Chapter 6** | **LLM Integration and Synthesis Engine** | 23 |
| **Chapter 7** | **Browser Automation and Stealth Extraction** | 26 |
| **Chapter 8** | **PDF Report Generation** | 29 |
| **Chapter 9** | **Testing Strategy** | 32 |
| **Chapter 10** | **Limitations, Future Work and Conclusion** | 35 |
| — | References | 38 |

---

# LIST OF FIGURES

| Figure No. | Caption | Page |
|-----------|---------|------|
| Figure 3.1 | System Architecture Diagram: MVC Layered View | 11 |
| Figure 4.1 | Home Screen and Search Interface | 15 |
| Figure 4.2 | Pro Research Intake Form (Step 1 of 3) | 16 |
| Figure 4.3 | Live Agent Terminal (SSE Stream) | 16 |
| Figure 4.4 | Research Results View with Action Bar | 17 |
| Figure 4.5 | Document Editor (Split-Pane View) | 17 |
| Figure 5.1 | Lite Research Pipeline Flowchart | 18 |
| Figure 5.2 | Deep Research Pipeline Flowchart | 20 |
| Figure 5.3 | Pro Research Pipeline Flowchart | 21 |
| Figure 5.4 | Evidence Verification Workflow | 22 |
| Figure 6.1 | Sequence Diagram: Groq API Interaction | 24 |
| Figure 7.1 | Browser Agent Agentic Loop | 27 |
| Figure 8.1 | PDF Generation Pipeline | 30 |

---

# LIST OF TABLES

| Table No. | Caption | Page |
|-----------|---------|------|
| Table 3.1 | Project Folder and File Structure | 14 |
| Table 5.1 | Research Mode Comparison | 22 |
| Table 6.1 | Groq API Parameters and Rationale | 25 |
| Table 6.2 | Evidence Scoring Formula Parameters | 25 |
| Table 7.1 | Browser Agent Action Types | 28 |
| Table 8.1 | ReportLab PDF Styles Configuration | 31 |
| Table 9.1 | Unit Test Cases | 33 |
| Table 9.2 | Integration Test Cases | 34 |
| Table 10.1 | Known Limitations | 35 |

---

# LIST OF ABBREVIATIONS

| Abbreviation | Full Form |
|---|---|
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| CORS | Cross-Origin Resource Sharing |
| CSS | Cascading Style Sheets |
| DOM | Document Object Model |
| DFD | Data Flow Diagram |
| ERD | Entity-Relationship Diagram |
| HTML | HyperText Markup Language |
| HTTP | HyperText Transfer Protocol |
| IEEE | Institute of Electrical and Electronics Engineers |
| JSON | JavaScript Object Notation |
| JS | JavaScript |
| LLM | Large Language Model |
| LRU | Least Recently Used |
| MVC | Model-View-Controller |
| NLP | Natural Language Processing |
| ORM | Object Relational Mapper |
| PDF | Portable Document Format |
| RAG | Retrieval-Augmented Generation |
| REST | Representational State Transfer |
| SPA | Single Page Application |
| SQL | Structured Query Language |
| SQLite | Self-Contained SQL Database Engine |
| SSE | Server-Sent Events |
| UI | User Interface |
| UML | Unified Modeling Language |
| URL | Uniform Resource Locator |
| UX | User Experience |
