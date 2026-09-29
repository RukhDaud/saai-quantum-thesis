"""Worked example of the coverage-aligned QUBO on a small instance (Section 3.4, Chapter 3).

    python worked_example.py        (writes results/worked_example.txt)
"""
import itertools
import os

import numpy as np

from qsel import solvers as S
from qsel.instance import Instance, sample_pool
from qsel.odd_space import DIM_NAMES, PREDICATES
from qsel.qubo import all_energies, energy
from qsel.qubo_v2 import build_qubo_v2, objective_terms

SEED, N, K = 2026, 6, 3
rng = np.random.default_rng(SEED)
inst = Instance(sample_pool(N, rng), K)
Q, const = build_qubo_v2(inst)
lin, quad = objective_terms(inst)
L = [f"seed {SEED}, n = {N}, k = {K}"]
for i, s in enumerate(inst.pool):
    preds = [p for (p, _, f) in PREDICATES if f(s)]
    L.append(f"x{i + 1}: " + ", ".join(s[d] for d in DIM_NAMES) + f"  | predicates {' '.join(preds)}  | |P| = {len(inst.pairs[i])}")
L.append(f"pool interactions: {len(inst.pool_pairs)}")
L.append("overlaps |P_i & P_j| (upper triangle):")
for i in range(N):
    L.append("  " + " ".join(f"{int(quad[i, j]):2d}" if j > i else " ." for j in range(N)))
C = const / K ** 2
L.append(f"C = {C:.0f}; constant C k^2 = {const:.0f}")
L.append("QUBO matrix (upper triangle):")
for i in range(N):
    L.append("  " + " ".join(f"{Q[i, j]:6.0f}" if j >= i else "      " for j in range(N)))
E_all = all_energies(Q, const)
x_opt, e_opt = S.exhaustive(Q, const, E_all)
g = S.greedy_coverage(inst)
L.append(f"exact optimum: {sorted(i + 1 for i in S.bits_to_sel(x_opt))}, energy {e_opt:.0f}, "
         f"pairwise coverage {100 * inst.pairwise_coverage(S.bits_to_sel(x_opt)):.1f}%")
xg = [1 if i in g else 0 for i in range(N)]
L.append(f"greedy: {sorted(i + 1 for i in g)}, energy {energy(Q, xg, const):.0f}, "
         f"pairwise coverage {100 * inst.pairwise_coverage(g):.1f}%")
L.append("all selections of size k ranked by energy (energy, covered interactions, selection):")
rows = []
for sel in itertools.combinations(range(N), K):
    x = [1 if i in sel else 0 for i in range(N)]
    cov = len(set().union(*[inst.pairs[i] for i in sel]))
    rows.append((energy(Q, x, const), cov, [i + 1 for i in sel]))
for e, cov, sel in sorted(rows):
    L.append(f"  {e:6.0f} {cov:3d} {sel}")
L.append(f"lowest energy of a selection of size != k: {min(E_all[v] for v in range(2 ** N) if bin(v).count('1') != K):.0f}")
os.makedirs("results", exist_ok=True)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "worked_example.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))

# ---------------------------------------------------------------- first formulation on the same pool
from qsel.qubo import build_qubo  # noqa: E402
Q1, c1 = build_qubo(inst)
E1 = all_energies(Q1, c1)
x1, e1 = S.exhaustive(Q1, c1, E1)
s1 = S.bits_to_sel(x1)
L2 = [f"first formulation optimum: {sorted(i + 1 for i in s1)}, coverage {100 * inst.pairwise_coverage(s1):.1f}% "
      f"({len(set().union(*[inst.pairs[i] for i in s1]))} interactions)"]

# ---------------------------------------------------------------- change-aware re-selection on a change-study instance
import pandas as pd  # noqa: E402
from qsel.change import add, change_aware, full_resolve, impact_set, unmet  # noqa: E402
ch = pd.concat([pd.read_csv(os.path.join("results", f)) for f in ("change_rq4.csv", "change_rq4_part2.csv")])
row = ch[(ch.n == 16) & ch.change.str.startswith("CH2") & (ch.method == "keep_old") & (ch.unmet_before > 0)].iloc[0]
seed2 = int(row.seed)
pool2 = sample_pool(16, np.random.default_rng(seed2))
old = Instance(pool2, 5)
new = Instance(pool2, 5, predicates=add(PREDICATES, "P10", "UN R157 para 5.5.1 [illustrative addition]",
                                        lambda s: s["road_markings"] == "absent" and s["precipitation"] == "snow"))
old_sel = [int(x) for x in row.selected.split()]
L2.append(f"change example: n = 16, seed {seed2}, CH2 (lane markings absent in snow)")
L2.append(f"previous selection {sorted(i + 1 for i in old_sel)}; unmet obligations after the change: {unmet(new, old_sel)}")
L2.append(f"impact set size {len(impact_set(old, new))}; candidates satisfying P10: "
          f"{[i + 1 for i, s in enumerate(pool2) if s['road_markings'] == 'absent' and s['precipitation'] == 'snow']}")
for name, fn in (("full re-selection", lambda: full_resolve(old, new, old_sel, "exact", seed2)),
                 ("change-aware", lambda: change_aware(old, new, old_sel, 1.0, 12, "exact", seed2))):
    res = fn()
    sel = res[0] if isinstance(res, tuple) else res
    sel = list(sel)
    L2.append(f"{name}: {sorted(i + 1 for i in sel)}; replaced {len(set(old_sel) - set(sel))}; "
              f"unmet {unmet(new, sel)}; coverage {100 * new.pairwise_coverage(sel):.1f}%")
L2.append(f"previous selection coverage {100 * old.pairwise_coverage(old_sel):.1f}%")
for i in sorted(set(old_sel) | {i for i, s in enumerate(pool2) if s['road_markings'] == 'absent' and s['precipitation'] == 'snow'}):
    L2.append(f"   x{i + 1}: " + ", ".join(pool2[i][d] for d in DIM_NAMES))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "worked_example.txt"), "a").write("\n".join(L2) + "\n")
print("\n".join(L2))
