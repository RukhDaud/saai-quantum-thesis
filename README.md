# Traceable ODD-boundary test-scenario generation from safety requirements (PhD, COMSATS)

Saadia Sadaf (SP24-PCS-002). Supervisor: Prof. Dr. Manzoor Ilahi Tamimy. Co-supervisor: Prof. Dr. Majid Iqbal Khan.

| Folder | Contents | Status |
|---|---|---|
| `thesis/` | Thesis source (`content.py`, `refs.json`) + build scripts + latest `.docx` | Draft v5, Ch. 1–4 |
| `phase0_references/` | Verified reference tracker, DOI list for Zotero | 146 refs, all checked |
| `phase1_review/` | Systematic review workbook (search log, screening, PRISMA, extraction) | Database searches to run |
| `phase2_corpus/` | EU 2022/1426 statement extraction (370), annotation template, agreement tool | Awaiting annotators; R157 text needed |
| `phaseA_extraction/` | Requirement → ODD predicate extraction: rule, TF-IDF, SciBERT, evaluation | Code ready; needs gold labels |
| `phaseB_qubo_selection/` | QUBO scenario selection: greedy, GA, SA, QAOA, exhaustive; stats | n=12, 16 done; n=20 running |

Rebuild the thesis: `cd thesis && python3 prep.py && node build.js PhD_Thesis_Draft.docx`
