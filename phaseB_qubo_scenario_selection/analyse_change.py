"""Summarise the RQ4 change-aware re-selection experiment.

    python analyse_change.py results/change_rq4.csv results/change_rq4_part2.csv --out results/change_rq4_summary.xlsx
Reports, per problem size and change type, for each strategy: share of cases meeting every clause
obligation (feasible), mean coverage relative to the best feasible selection, mean tests replaced
(churn), variables used and median time; and paired Wilcoxon tests of churn and coverage between
change-aware re-selection and full re-selection.
"""
import argparse

import pandas as pd
from scipy.stats import wilcoxon


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default="results/change_rq4_summary.xlsx")
    a = ap.parse_args()
    d = pd.concat([pd.read_csv(f) for f in a.files]).drop_duplicates(["n", "seed", "change", "method"])
    d["change_type"] = d["change"].str.split(" ").str[0]
    g = d.groupby(["n", "change_type", "method"]).agg(
        cases=("seed", "nunique"), feasible=("feasible", "mean"), cov_ratio=("cov_ratio", "mean"),
        churn=("churn", "mean"), variables=("variables", "max"), seconds=("seconds", "median")).reset_index()
    overall = d.groupby(["n", "method"]).agg(
        cases=("seed", "size"), feasible=("feasible", "mean"), cov_ratio=("cov_ratio", "mean"),
        churn=("churn", "mean"), variables=("variables", "max"), seconds=("seconds", "median")).reset_index()
    tests = []
    for n in sorted(d.n.unique()):
        for aware in ("aware_exact", "aware_qaoa"):
            for metric in ("churn", "cov_ratio"):
                x = d[(d.n == n) & (d.method == aware)].set_index(["seed", "change"])[metric]
                y = d[(d.n == n) & (d.method == "full_exact")].set_index(["seed", "change"])[metric]
                j = x.index.intersection(y.index)
                diff = (x[j] - y[j])
                p = wilcoxon(x[j], y[j]).pvalue if (diff != 0).any() else 1.0
                tests.append(dict(n=n, method=aware, vs="full_exact", metric=metric, pairs=len(j),
                                  mean_method=x[j].mean(), mean_full=y[j].mean(), wilcoxon_p=p))
    t = pd.DataFrame(tests)
    with pd.ExcelWriter(a.out) as w:
        overall.to_excel(w, sheet_name="Overall", index=False)
        g.to_excel(w, sheet_name="By change", index=False)
        t.to_excel(w, sheet_name="Tests", index=False)
    pd.set_option("display.width", 200)
    print(overall.round(4).to_string(index=False))
    print()
    print(t.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
