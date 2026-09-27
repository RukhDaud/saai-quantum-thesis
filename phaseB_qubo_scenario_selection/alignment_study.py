"""Alignment study: how well does each QUBO objective rank selections by true coverage?

For every instance, all C(n, k) selections of size k are enumerated. For each objective we
report
  * spearman  - rank correlation between objective value and true pairwise coverage
  * regret    - best achievable pairwise coverage minus the coverage of the objective's
                best selection (0 = the QUBO optimum is also the coverage optimum)
  * opt_cov   - pairwise coverage of the objective's best selection
alongside the greedy heuristic and the true optimum (the best of all C(n, k) selections).

Instances use the same seeds as run_experiment.py (evaluation set) or a disjoint seed
base (training set for tuning).

    python alignment_study.py --sizes 12 16 20 --instances 30 --out results/alignment_eval.csv
"""
import argparse
import itertools

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from qsel import solvers as S
from qsel.instance import Instance, sample_pool
from qsel.qubo import build_qubo
from qsel.qubo_v2 import objective_terms

EVAL_BASE = 20260927   # seeds used by run_experiment.py
TRAIN_BASE = 77770000  # disjoint seeds used only for tuning


def subsets(n, k):
    return np.array(list(itertools.combinations(range(n), k)), dtype=np.int32)


def objective_values(lin, quad, subs):
    """Objective (without budget penalty) for every subset of size k."""
    v = lin[subs].sum(axis=1)
    k = subs.shape[1]
    for a in range(k):
        for b in range(a + 1, k):
            i, j = subs[:, a], subs[:, b]
            lo, hi = np.minimum(i, j), np.maximum(i, j)
            v += quad[lo, hi]
    return v


def v1_terms(inst):
    Q, _ = build_qubo(inst)
    n = inst.n
    # remove the budget penalty so only the objective remains (penalty is constant for |S| = k)
    C = None
    # recover C from the off-diagonal: Q_ij = quad_ij + 2C; the diagonal = lin + C(1-2k)
    # simpler: rebuild the terms with C = 0
    Q0, _ = build_qubo(inst, C=0.0)
    lin = np.diag(Q0).copy()
    quad = np.triu(Q0, 1)
    return lin, quad


def true_cov(inst, subs):
    return np.array([inst.pairwise_coverage(s) for s in subs])


def study_instance(n, k, seed, configs):
    rng = np.random.default_rng(seed)
    inst = Instance(sample_pool(n, rng), k)
    subs = subsets(n, k)
    cov = true_cov(inst, subs)
    best = cov.max()
    g = inst.pairwise_coverage(S.greedy_coverage(inst))
    rows = []
    for name, (lin, quad) in configs(inst).items():
        val = objective_values(lin, quad, subs)
        arg = int(np.argmin(val))
        rho = spearmanr(-val, cov).correlation
        rows.append(dict(n=n, seed=seed, objective=name, spearman=rho, opt_cov=cov[arg],
                         regret=best - cov[arg], best_cov=best, greedy_cov=g,
                         greedy_regret=best - g))
    return rows


def default_configs(inst):
    cfg = {"v1 (current)": v1_terms(inst)}
    for beta in (1.0, 0.75, 0.5):
        cfg[f"v2 beta={beta}"] = objective_terms(inst, beta=beta)
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[12, 16, 20])
    ap.add_argument("--instances", type=int, default=30)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--train", action="store_true", help="use the disjoint training seeds")
    ap.add_argument("--out", default="results/alignment_eval.csv")
    a = ap.parse_args()
    base = TRAIN_BASE if a.train else EVAL_BASE
    rows = []
    for n in a.sizes:
        for i in range(a.instances):
            rows += study_instance(n, a.k, base + 1000 * n + i, default_configs)
        print(f"n={n} done")
    d = pd.DataFrame(rows)
    d.to_csv(a.out, index=False)
    s = d.groupby(["n", "objective"]).agg(spearman=("spearman", "median"), regret_mean=("regret", "mean"),
                                          opt_is_best=("regret", lambda r: (r < 1e-12).mean()),
                                          greedy_regret=("greedy_regret", "mean"))
    print(s.round(4).to_string())


if __name__ == "__main__":
    main()
