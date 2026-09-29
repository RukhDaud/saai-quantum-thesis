"""Alignment of the coverage-aligned QUBO with true pairwise coverage for budgets k = 3, 5 and 7 (Section 5.3).

For every instance of the solver comparison at n = 12 and 16, enumerates all C(n, k) selections and records whether the
QUBO optimum is a coverage optimum, the coverage lost by the worst QUBO-optimal selection, and the Spearman correlation.
    python budget_alignment.py        (writes results/budget_alignment.csv and .txt)
"""
import itertools
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from qsel.instance import Instance, sample_pool
from qsel.qubo_v2 import objective_terms

rows = []
for k in (3, 5, 7):
    for n in (12, 16):
        for i in range(30):
            seed = 20260927 + 1000 * n + i
            inst = Instance(sample_pool(n, np.random.default_rng(seed)), k)
            lin, quad = objective_terms(inst)
            E, C = [], []
            for sel in itertools.combinations(range(n), k):
                e = sum(lin[a] for a in sel) + sum(quad[a, b] for a, b in itertools.combinations(sel, 2))
                E.append(e)
                C.append(len(set().union(*[inst.pairs[a] for a in sel])))
            E, C = np.array(E), np.array(C)
            opt = E <= E.min() + 1e-9
            rows.append(dict(k=k, n=n, seed=seed, aligned=bool(C[opt].max() == C.max()),
                             all_optima_aligned=bool(C[opt].min() == C.max()),
                             worst_loss_pp=100 * (C.max() - C[opt].min()) / len(inst.pool_pairs),
                             spearman=spearmanr(-E, C).correlation))
d = pd.DataFrame(rows)
d.to_csv("results/budget_alignment.csv", index=False)
s = d.groupby(["k", "n"]).agg(some_optimum_aligned=("aligned", "mean"), all_optima_aligned=("all_optima_aligned", "mean"),
                              mean_worst_loss_pp=("worst_loss_pp", "mean"), max_worst_loss_pp=("worst_loss_pp", "max"),
                              spearman_mean=("spearman", "mean")).round(3)
open("results/budget_alignment.txt", "w").write(s.to_string() + "\n")
print(s.to_string())
