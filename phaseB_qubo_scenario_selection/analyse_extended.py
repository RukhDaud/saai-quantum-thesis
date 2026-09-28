"""Extended analysis of the Phase B results (Chapter 5 detail tables).

Reads the result files written by run_experiment.py, large_scale.py, alignment_study.py and
change_experiment.py and writes results/analysis_extended.txt with:
  A  per-method distribution of pairwise, boundary and predicate coverage, optimum-hit rate and time
  B  pairwise Wilcoxon comparison of all methods (coverage-aligned formulation)
  C  alignment study: Spearman correlation between QUBO energy and coverage, regret
  D  scaling study: time per method, ILP solve statistics
  E  change study broken down by clause change
  F  the first formulation: boundary and predicate coverage per method

    python analyse_extended.py
"""
import itertools
import os

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
OUT = os.path.join(R, "analysis_extended.txt")
lines = []


def out(s=""):
    lines.append(str(s))


def a12(x, y):
    x, y = np.asarray(x), np.asarray(y)
    gt = (x[:, None] > y[None, :]).sum()
    eq = (x[:, None] == y[None, :]).sum()
    return (gt + 0.5 * eq) / (len(x) * len(y))


def wp(x, y):
    d = np.asarray(x) - np.asarray(y)
    if np.allclose(d, 0):
        return 1.0
    return wilcoxon(x, y).pvalue


def q(s, p):
    return np.percentile(s, p)


NAMES = {"random": "Random", "greedy": "Greedy", "ga": "Genetic algorithm", "sa": "Simulated annealing",
         "qaoa": "QAOA", "exhaustive": "Exact QUBO optimum"}
ORDER = ["random", "greedy", "ga", "sa", "qaoa", "exhaustive"]

# ---------------------------------------------------------------- A
v2 = pd.read_csv(os.path.join(R, "runs_v2_full.csv"))
out("A. Coverage-aligned formulation: distribution per method (30 instances per n)")
out("n  method  cov_mean cov_sd cov_q1 cov_q3 | boundary_mean predicate_mean traced_mean | opt_hit | sec_median sec_q1 sec_q3")
for n in (12, 16, 20):
    for m in ORDER:
        d = v2[(v2.n == n) & (v2.method == m)]
        out(f"{n} {m:10s} {100*d.pairwise_cov.mean():6.2f} {100*d.pairwise_cov.std():5.2f} "
            f"{100*q(d.pairwise_cov,25):6.2f} {100*q(d.pairwise_cov,75):6.2f} | "
            f"{100*d.boundary_cov.mean():6.2f} {100*d.predicate_cov.mean():6.2f} {100*d.traced_frac.mean():6.2f} | "
            f"{100*(d.energy_gap.abs() < 1e-9).mean():5.1f} | "
            f"{d.seconds.median():9.4f} {q(d.seconds,25):9.4f} {q(d.seconds,75):9.4f}")
out()

# ---------------------------------------------------------------- B
out("B. Pairwise comparison of all methods on pairwise coverage (row vs column: Wilcoxon p; A12)")
for n in (12, 16, 20):
    out(f"n = {n}")
    piv = v2[v2.n == n].pivot_table(index="seed", columns="method", values="pairwise_cov")
    for a, b in itertools.combinations(ORDER, 2):
        out(f"  {a:10s} vs {b:10s}  p = {wp(piv[a], piv[b]):.4f}  A12 = {a12(piv[a], piv[b]):.3f}  "
            f"wins/ties/losses = {(piv[a] > piv[b] + 1e-12).sum()}/{(np.isclose(piv[a], piv[b])).sum()}/{(piv[a] < piv[b] - 1e-12).sum()}")
out()

# ---------------------------------------------------------------- C
al = pd.read_csv(os.path.join(R, "alignment_eval.csv"))
out("C. Alignment study: Spearman(QUBO energy rank, coverage rank) over all C(n,5) selections; regret of QUBO optimum")
out("n objective  spearman_mean spearman_min  opt_is_best  regret_mean(pp) regret_max(pp)")
for (n, o), d in al.groupby(["n", "objective"]):
    out(f"{n} {o:24s} {d.spearman.mean():.3f} {d.spearman.min():.3f} {100*(d.regret.abs() < 1e-12).mean():5.1f}% "
        f"{100*d.regret.mean():.2f} {100*d.regret.max():.2f}")
out()

# ---------------------------------------------------------------- D
lg = pd.read_csv(os.path.join(R, "large_v2.csv"))
out("D. Scaling study: time per method (s) and ILP reference statistics")
for n, d in lg.groupby("n"):
    out(f"n = {n}: ILP proven optimal on {int(d.groupby('seed').ilp_optimal.first().sum())}/30; "
        f"ILP time median {d.groupby('seed').ilp_seconds.first().median():.2f} s, max {d.groupby('seed').ilp_seconds.first().max():.2f} s")
    for m, dm in d.groupby("method"):
        out(f"   {m:14s} time median {dm.seconds.median():8.4f}  q1 {q(dm.seconds,25):8.4f}  q3 {q(dm.seconds,75):8.4f}  "
            f"boundary_cov mean {100*dm.boundary_cov.mean():6.2f}  gap mean {100*dm.gap_to_optimum.mean():.2f} pp")
out()

# ---------------------------------------------------------------- E
ch = pd.concat([pd.read_csv(os.path.join(R, "change_rq4.csv")), pd.read_csv(os.path.join(R, "change_rq4_part2.csv"))])
ch["cid"] = ch.change.str[:3]
out("E. Change study by clause change (feasible = all obligations exercised)")
out("n change method  cases feasible cov_ratio churn impact_set unmet_before")
for (n, cid, m), d in ch.groupby(["n", "cid", "method"]):
    out(f"{n} {cid} {m:12s} {len(d):4d} {100*d.feasible.mean():6.1f} {100*d.cov_ratio.mean():7.2f} "
        f"{d.churn.mean():5.2f} {d.impact_set.mean():5.2f} {100*(d.unmet_before > 0).mean():6.1f}")
out()
for cid, d in ch.groupby("cid"):
    out(f"{cid}: {d.change.iloc[0]}")
out()

# ---------------------------------------------------------------- F
v1 = pd.read_csv(os.path.join(R, "runs_full.csv"))
ex1 = v1[v1.method == "exhaustive"].set_index(["n", "seed"]).qubo_energy
v1["hit"] = [abs(e - ex1[(n, s)]) <= 1e-6 * max(1.0, abs(ex1[(n, s)])) for e, n, s in zip(v1.qubo_energy, v1.n, v1.seed)]
out("F. First formulation: mean coverage per method")
out("n method  pairwise boundary predicate opt_hit")
for n in (12, 16, 20):
    for m in ORDER:
        d = v1[(v1.n == n) & (v1.method == m)]
        if len(d) == 0:
            continue
        out(f"{n} {m:10s} {100*d.pairwise_cov.mean():6.2f} {100*d.boundary_cov.mean():6.2f} "
            f"{100*d.predicate_cov.mean():6.2f} {100*d.hit.mean():5.1f}")

open(OUT, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
