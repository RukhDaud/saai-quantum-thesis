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
