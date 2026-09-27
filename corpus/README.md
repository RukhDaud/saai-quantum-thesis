# Corpus and ODD condition library (Contribution 1)

Safety requirements → formal ODD conditions → traceability to the code that tests them.

| File | Content |
|---|---|
| `extract_eu1426.py` → `eu1426_statements.csv` | 370 statements from Commission Implementing Regulation (EU) 2022/1426, Annexes II and III |
| `r157_statements.py` → `r157_statements.csv` | 71 statements from UN Regulation No 157 (ALKS), OJ L 82, 9.3.2021: definitions 2.1, 2.10 and all of sections 5, 6, 7 |
| `odd_condition_library.py` → `odd_condition_library.csv` | 29 formal conditions (ODD condition, boundary response, performance limit, activation condition), each with dimension, variable, operator, threshold, unit, required response and source clause(s) |
| `traceability_matrix.csv` | Statement id → clause → condition → where it is represented in the code (Phase B predicate / Phase C simulation parameter) or `gap` |
| `tools/agreement.py` | Cohen's kappa between two labellers (optional use) |

Rules used to write the library:
- Operator, threshold and unit are filled only when the clause states them; otherwise `qualitative` / `unspecified` / `none`.
- Every condition cites the corpus statement id(s), so each line can be checked word for word.
- R157 rows were checked against the official text by Saadia Sadaf on 27 Sep 2026 (`verified = yes`). The equation in 5.2.5.2(c) is not reproduced in the text column and is marked `[equation]`.

Rebuild:
```bash
python extract_eu1426.py        # needs the saved EUR-Lex page (not redistributed)
python r157_statements.py
python odd_condition_library.py
```
