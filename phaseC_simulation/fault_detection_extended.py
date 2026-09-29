"""Fault detection beyond the solver comparison (Chapter 6, extended analyses).

Scores, with the kill matrix of the longitudinal model (results/fdm_kill_matrix.csv):
  A  the selections of the scaling study (n = 50, 100, 200)
  B  the selections after each clause change (change study, n = 16, 20)
  C  leave-one-fault-out: the comparison of Table 6.3 with each fault removed in turn
  D  the budget study (k = 3 and k = 7, n = 12 and 16), with the best achievable score by enumeration

    python fault_detection_extended.py      (writes results/fd_extended.csv and results/fd_extended.txt)
"""
import itertools
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

H = os.path.dirname(os.path.abspath(__file__))
PB = os.path.join(H, "..", "phaseB_qubo_scenario_selection")
sys.path.insert(0, PB)
from qsel.instance import sample_pool  # noqa: E402

R = os.path.join(H, "results")
km = pd.read_csv(os.path.join(R, "fdm_kill_matrix.csv"))
MUT = [c for c in km.columns if c.startswith("M")]
KILL = {(r.precipitation, r.visibility, str(r.speed_kmh)): {m for m in MUT if getattr(r, m)} for r in km.itertuples()}
KILLABLE = [m for m in MUT if km[m].sum() > 0]
_pools = {}
L = []


def out(s=""):
    L.append(str(s))


def pool(n, seed):
    if (n, seed) not in _pools:
        _pools[(n, seed)] = sample_pool(n, np.random.default_rng(seed))
    return _pools[(n, seed)]


def killed(n, seed, sel):
    p = pool(n, seed)
    k = set()
    for i in sel:
        s = p[i]
        k |= KILL[(s["precipitation"], s["visibility"], str(s["speed_kmh"]))]
    return k


def wp(x, y):
    d = np.asarray(x) - np.asarray(y)
    return 1.0 if np.allclose(d, 0) else wilcoxon(x, y).pvalue


def sel_of(v):
    return [int(x) for x in str(v).split()]


rows = []
# ---------------------------------------------------------------- A scaling study
lg = pd.read_csv(os.path.join(PB, "results", "large_v2.csv"))
for r in lg.itertuples():
    k = killed(r.n, r.seed, sel_of(r.selected))
    rows.append(dict(study="scaling", n=r.n, seed=r.seed, method=r.method, killed=len(k), score=len(k) / len(KILLABLE),
                     mutants=" ".join(sorted(k))))
out("A. Scaling study: mean mutation score; Wilcoxon p and wins/ties/losses against random and against greedy")
sc = pd.DataFrame([x for x in rows if x["study"] == "scaling"])
for n, g in sc.groupby("n"):
    piv = g.pivot_table(index="seed", columns="method", values="score")
    parts = []
    for m in ("random", "greedy", "sa", "ga", "decomp_exact", "decomp_qaoa"):
        dr, dg = piv[m] - piv["random"], piv[m] - piv["greedy"]
        parts.append(f"{m} {piv[m].mean():.3f} [vs random p={wp(piv[m], piv['random']):.3f} {(dr > 0).sum()}/{(dr == 0).sum()}/{(dr < 0).sum()}; "
                     f"vs greedy p={wp(piv[m], piv['greedy']):.3f} {(dg > 0).sum()}/{(dg == 0).sum()}/{(dg < 0).sum()}]")
    out(f"n={n}:\n   " + "\n   ".join(parts))
    det = {m: " ".join(f"{mm[:2]} {100 * g[g.method == m].mutants.str.contains(mm).mean():.0f}" for mm in KILLABLE)
           for m in ("random", "greedy", "ga", "decomp_qaoa")}
    out("   detection by fault: " + " | ".join(f"{m}: {v}" for m, v in det.items()))
out()

# ---------------------------------------------------------------- B change study
ch = pd.concat([pd.read_csv(os.path.join(PB, "results", f)) for f in ("change_rq4.csv", "change_rq4_part2.csv")])
ch["cid"] = ch.change.str[:3]
for r in ch.itertuples():
    k = killed(r.n, r.seed, sel_of(r.selected))
    rows.append(dict(study="change", n=r.n, seed=r.seed, method=r.method, change=r.cid, killed=len(k),
                     score=len(k) / len(KILLABLE), mutants=" ".join(sorted(k))))
cd = pd.DataFrame([x for x in rows if x["study"] == "change"])
out("B. Change study: mean mutation score after re-selection by strategy (180 changes per size)")
out(cd.groupby(["n", "method"]).score.mean().unstack().round(3).to_string())
for n, g in cd.groupby("n"):
    piv = g.assign(key=g.seed.astype(str) + g.change).pivot_table(index="key", columns="method", values="score")
    for m in ("aware_exact", "full_exact"):
        d = piv[m] - piv["keep_old"]
        out(f"n={n} {m} vs keep_old: p={wp(piv[m], piv['keep_old']):.3f} {(d > 0).sum()}/{(d == 0).sum()}/{(d < 0).sum()}")
out()

# ---------------------------------------------------------------- C leave one fault out
fs = pd.read_csv(os.path.join(R, "fdm_scores.csv"))
fs = fs[fs.formulation == "v2"].copy()
fs["km"] = fs.killed_mutants.fillna("").str.split()
out("C. Leave one fault out (coverage-aligned): mean score of random vs coverage-based methods pooled over n, and Wilcoxon p of greedy vs random per n")
for drop in [None] + KILLABLE:
    keep = [m for m in KILLABLE if m != drop]
    fs["s"] = fs.km.map(lambda ks: sum(m in ks for m in keep) / len(keep))
    means = fs.groupby("method").s.mean()
    ps = []
    for n, g in fs.groupby("n"):
        piv = g.pivot_table(index="seed", columns="method", values="s")
        ps.append(f"{wp(piv['greedy'], piv['random']):.3f}")
    cov = means.drop("random")
    out(f"without {drop or 'none':24s}: random {means['random']:.3f}; coverage-based {cov.min():.3f}-{cov.max():.3f}; greedy vs random p (n=12/16/20) {' / '.join(ps)}")
out()

# ---------------------------------------------------------------- D budget study
for kk in (3, 7):
    f = os.path.join(PB, "results", f"runs_v2_k{kk}.csv")
    if not os.path.exists(f):
        continue
    d = pd.read_csv(f)
    for r in d.itertuples():
        k = killed(r.n, r.seed, sel_of(r.selected))
        rows.append(dict(study=f"budget_k{kk}", n=r.n, seed=r.seed, method=r.method, killed=len(k), score=len(k) / len(KILLABLE),
                         mutants=" ".join(sorted(k)), pairwise_cov=r.pairwise_cov))
out("D. Budget study: mean pairwise coverage and mutation score by method, and best achievable score")
for kk in (3, 7):
    b = pd.DataFrame([x for x in rows if x["study"] == f"budget_k{kk}"])
    if b.empty:
        continue
    for n, g in b.groupby("n"):
        best = []
        for seed in sorted(g.seed.unique()):
            p = pool(n, seed)
            best.append(max(len(killed(n, seed, c)) for c in itertools.combinations(range(n), kk)) / len(KILLABLE))
        piv = g.pivot_table(index="seed", columns="method", values="score")
        pr = []
        for m in ("greedy", "ga", "sa", "qaoa", "exhaustive"):
            dd = piv[m] - piv["random"]
            pr.append(f"{m} p={wp(piv[m], piv['random']):.3f} {(dd > 0).sum()}/{(dd == 0).sum()}/{(dd < 0).sum()}")
        out(f"k={kk} n={n}: best achievable {np.mean(best):.3f}; " +
            "; ".join(f"{m} cov {100 * g[g.method == m].pairwise_cov.mean():.1f}% ms {g[g.method == m].score.mean():.3f}"
                      for m in ("random", "greedy", "ga", "sa", "qaoa", "exhaustive")))
        out("      vs random: " + "; ".join(pr))

pd.DataFrame(rows).to_csv(os.path.join(R, "fd_extended.csv"), index=False)
open(os.path.join(R, "fd_extended.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
