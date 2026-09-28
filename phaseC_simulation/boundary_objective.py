"""E1: boundary-aware selection objective and its effect on fault detection.

The coverage-aligned objective counts all two-way interactions between ODD levels. The boundary-aware
objective counts only boundary interactions: pairs of levels that both exercise a clause-derived
predicate (e.g. snow with 70 km/h, fog with snow). It uses regulation information only - never the
planted faults. For every evaluation instance the exact optimum of each objective (tie-broken by
pairwise coverage) is found by enumeration, and its mutation score is computed with the kill matrix
of Chapter 6.

    python boundary_objective.py
"""
import itertools
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "phaseB_qubo_scenario_selection"))
from qsel.instance import Instance, sample_pool  # noqa: E402
from qsel.qubo_v2 import coverage_terms  # noqa: E402
from qsel.qubo import all_energies  # noqa: E402

SIM = ["precipitation", "visibility", "speed_kmh"]


def boundary_pairs(inst):
    return [{p for p in inst.pairs[i] if p[0] in inst.boundary_levels and p[1] in inst.boundary_levels}
            for i in range(inst.n)]


def best_by(inst, sets, k):
    best, arg = None, None
    for sel in itertools.combinations(range(inst.n), k):
        key = (len(set().union(*[sets[i] for i in sel])), inst.pairwise_coverage(sel))
        if best is None or key > best:
            best, arg = key, list(sel)
    return arg


def qubo_opt(inst, sets):
    lin, quad = coverage_terms(sets)
    n, k = inst.n, inst.k
    C = 1.0 + np.abs(lin).max() + quad.sum(axis=1).max() + quad.sum(axis=0).max()
    Q = np.triu(quad, 1).copy()
    Q[np.diag_indices(n)] = -lin + C * (1 - 2 * k)
    Q[np.triu_indices(n, 1)] += 2 * C
    v = int(np.argmin(all_energies(Q, C * k * k)))
    return [i for i in range(n) if (v >> i) & 1]


def main():
    km = pd.read_csv(os.path.join(HERE, "results", "fdm_kill_matrix.csv"), dtype={"speed_kmh": str}).set_index(SIM)
    muts = [c for c in km.columns if c.startswith("M") and km[c].sum() > 0]
    rows = []
    for n in (12, 16, 20):
        for i in range(30):
            seed = 20260927 + 1000 * n + i
            inst = Instance(sample_pool(n, np.random.default_rng(seed)), 5)
            bp = boundary_pairs(inst)
            sels = {"coverage_optimum": best_by(inst, inst.pairs, 5),
                    "boundary_optimum": best_by(inst, bp, 5),
                    "boundary_qubo": qubo_opt(inst, bp)}
            for name, sel in sels.items():
                combos = {tuple(inst.pool[j][d] for d in SIM) for j in sel}
                killed = [m for m in muts if any(km.loc[c, m] for c in combos)]
                cov_b = len(set().union(*[bp[j] for j in sel])) / max(1, len(set().union(*bp)))
                rows.append(dict(n=n, seed=seed, method=name, size=len(sel), pairwise_cov=inst.pairwise_coverage(sel),
                                 boundary_pair_cov=cov_b, mutation_score=len(killed) / len(muts)))
        print("n", n, "done", flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(HERE, "results", "boundary_objective.csv"), index=False)
    print(d.groupby(["n", "method"])[["pairwise_cov", "boundary_pair_cov", "mutation_score"]].mean().round(4).to_string())
    for n in (12, 16, 20):
        a = d[(d.n == n) & (d.method == "boundary_optimum")].set_index("seed").mutation_score
        b = d[(d.n == n) & (d.method == "coverage_optimum")].set_index("seed").mutation_score
        diff = a - b
        p = wilcoxon(a, b).pvalue if (diff != 0).any() else 1.0
        print(n, "boundary vs coverage optimum: W/T/L", (diff > 0).sum(), (diff == 0).sum(), (diff < 0).sum(), "p=%.4f" % p)


if __name__ == "__main__":
    main()
