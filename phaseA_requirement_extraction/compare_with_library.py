"""Compare the rule-based extractor's output on EU 2022/1426 with the verified condition library (Section 4.1).

    python compare_with_library.py      (writes results/compare_with_library.txt)
"""
import os

import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(H, "..", "corpus")
p = pd.read_csv(os.path.join(H, "results", "rule_predictions_eu1426.csv"))
tm = pd.read_csv(os.path.join(C, "traceability_matrix.csv"))
lib = pd.read_csv(os.path.join(C, "odd_condition_library.csv"))
src = {s for s in tm.statement_id if s.startswith("EU")}
p["source"] = p.req_id.isin(src)
p["flagged"] = p.has_odd_condition == "yes"
L = ["Flagged by the extractor (rows) against source of a library condition (columns):",
     pd.crosstab(p.flagged, p.source).to_string(),
     f"flagged {p.flagged.sum()} of {len(p)}; sources flagged {int((p.flagged & p.source).sum())} of {p.source.sum()}; "
     f"share of flagged statements that are sources {100 * (p.flagged & p.source).sum() / p.flagged.sum():.1f}%",
     "dimensions assigned to flagged statements: " + str(p[p.flagged].odd_dimension.value_counts().to_dict())]
m = tm.merge(lib[["condition_id", "odd_dimension"]], on="condition_id")
m = m[m.statement_id.str.startswith("EU")].groupby("statement_id").odd_dimension.apply(set).reset_index()
j = m.merge(p, left_on="statement_id", right_on="req_id", suffixes=("_lib", "_rule"))
j["same_dimension"] = [r in l for l, r in zip(j.odd_dimension_lib, j.odd_dimension_rule)]
L.append(j[["statement_id", "odd_dimension_lib", "odd_dimension_rule", "has_odd_condition", "same_dimension"]].to_string())
f = j[j.has_odd_condition == "yes"]
L.append(f"flagged sources with a dimension of one of their conditions: {int(f.same_dimension.sum())} of {len(f)}")
open(os.path.join(H, "results", "compare_with_library.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
