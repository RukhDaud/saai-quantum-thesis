"""Structure of the QUBO optimum and QAOA success (Section 5.3).

For every coverage-aligned instance (k = 5, n = 12, 16, 20) counts the optimal selections (ties in energy) and the
energy gap between the best and second-best selection levels, and relates them to whether QAOA and simulated annealing
returned an optimum.   python optimum_structure.py   (writes results/optimum_structure.csv and .txt)
"""
import itertools

import numpy as np
import pandas as pd

from qsel.instance import Instance, sample_pool
from qsel.qubo_v2 import objective_terms

runs = pd.read_csv("results/runs_v2_full.csv")
rows = []
for n in (12, 16, 20):
    for i in range(30):
        seed = 20260927 + 1000 * n + i
        inst = Instance(sample_pool(n, np.random.default_rng(seed)), 5)
        lin, quad = objective_terms(inst)
        E = np.array([sum(lin[a] for a in s) + sum(quad[a, b] for a, b in itertools.combinations(s, 2))
                      for s in itertools.combinations(range(n), 5)])
        lv = np.unique(np.round(E, 6))
        r = runs[(runs.n == n) & (runs.seed == seed)].set_index("method")
        rows.append(dict(n=n, seed=seed, n_optima=int((E <= lv[0] + 1e-6).sum()), gap_to_second=float(lv[1] - lv[0]),
                         share_within_1=float((E <= lv[0] + 1 + 1e-6).mean()),
                         qaoa_hit=bool(abs(r.loc["qaoa", "energy_gap"]) < 1e-9), sa_hit=bool(abs(r.loc["sa", "energy_gap"]) < 1e-9),
                         greedy_hit=bool(abs(r.loc["greedy", "energy_gap"]) < 1e-9)))
d = pd.DataFrame(rows)
d.to_csv("results/optimum_structure.csv", index=False)
L = ["optimal selections per instance (median, min, max) and QAOA/SA/greedy hit rates by whether the optimum is unique"]
for n, g in d.groupby("n"):
    L.append(f"n={n}: optima median {g.n_optima.median():.0f} [{g.n_optima.min()}-{g.n_optima.max()}]; unique on {int((g.n_optima == 1).sum())}/30; "
             f"hit QAOA unique {g[g.n_optima == 1].qaoa_hit.mean():.2f} vs tied {g[g.n_optima > 1].qaoa_hit.mean():.2f}; "
             f"SA unique {g[g.n_optima == 1].sa_hit.mean():.2f} vs tied {g[g.n_optima > 1].sa_hit.mean():.2f}; "
             f"greedy unique {g[g.n_optima == 1].greedy_hit.mean():.2f} vs tied {g[g.n_optima > 1].greedy_hit.mean():.2f}; "
             f"share of selections within 1 of optimum median {100 * g.share_within_1.median():.2f}%")
open("results/optimum_structure.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
