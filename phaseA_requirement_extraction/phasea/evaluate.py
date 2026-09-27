"""Score predictions against adjudicated gold labels.

Categorical fields: accuracy, macro-F1 (sklearn), per-class P/R/F1.
Textual fields: normalised exact match, computed only on rows where gold
has_odd_condition == 'yes' (other rows have no predicate to extract).
Also reports whole-predicate exact match (all six predicate fields right),
the headline number comparable to Req2Spec's 71% figure.

Usage:
    python -m phasea.evaluate gold.csv|xlsx predictions.csv --out results/eval.xlsx
"""
import argparse

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score

from .schema import CATEGORICAL, TEXTUAL, norm

PREDICATE = ["odd_dimension", "variable", "operator", "threshold", "unit"]


def load(path):
    if str(path).endswith((".xlsx", ".xls")):
        return pd.read_excel(path, sheet_name="Corpus", dtype=str)
    return pd.read_csv(path, dtype=str)


def evaluate(gold, pred):
    m = gold.merge(pred, on="req_id", suffixes=("_g", "_p"))
    m = m[m["has_odd_condition_g"].map(norm) != ""]  # only rows with a gold label
    rows, reports = [], {}
    for f in CATEGORICAL:
        g, p = m[f + "_g"].map(norm), m[f + "_p"].map(norm)
        rows.append(dict(field=f, n=len(m), metric="accuracy", value=accuracy_score(g, p)))
        rows.append(dict(field=f, n=len(m), metric="macro_F1",
                         value=f1_score(g, p, average="macro", zero_division=0)))
        reports[f] = pd.DataFrame(classification_report(g, p, output_dict=True, zero_division=0)).T
    pos = m[m["has_odd_condition_g"].map(norm) == "yes"]
    for f in TEXTUAL:
        if f + "_g" not in pos:
            continue
        ok = (pos[f + "_g"].map(norm) == pos[f + "_p"].map(norm))
        rows.append(dict(field=f, n=len(pos), metric="exact_match", value=ok.mean() if len(pos) else float("nan")))
    if len(pos):
        allok = pd.concat([(pos[f + "_g"].map(norm) == pos[f + "_p"].map(norm)) for f in PREDICATE], axis=1).all(axis=1)
        rows.append(dict(field="whole_predicate", n=len(pos), metric="exact_match", value=allok.mean()))
    return pd.DataFrame(rows), reports, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gold")
    ap.add_argument("pred")
    ap.add_argument("--out", default="results/eval.xlsx")
    a = ap.parse_args()
    summ, reps, m = evaluate(load(a.gold), load(a.pred))
    with pd.ExcelWriter(a.out) as w:
        summ.to_excel(w, "Summary", index=False)
        for f, r in reps.items():
            r.to_excel(w, f[:31])
    print(summ.to_string(index=False))


if __name__ == "__main__":
    main()
