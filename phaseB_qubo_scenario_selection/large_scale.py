"""Large-scale experiment: pools of 50-200 candidate scenarios, coverage-aligned QUBO (v2).

Methods: random, greedy, simulated annealing and genetic algorithm on the full QUBO,
and sub-QUBO decomposition started from the greedy selection with the sub-problems
solved exactly (m=12) or with QAOA on the statevector simulator (m=10).
Reference: exact coverage optimum from an integer linear programme.

    python large_scale.py --sizes 50 100 200 --instances 30 --k 5 --out results/large_v2.csv
"""
import argparse
import csv
import time

import numpy as np

from qsel import solvers as S
from qsel.decomp import decomposed, exact_max_coverage
from qsel.instance import Instance, sample_pool
from qsel.qubo import energy
from qsel.qubo_v2 import build_qubo_v2

BASE = 31415926  # seeds disjoint from the n <= 20 experiment and from tuning


def run(n, k, seed, w, qaoa_m):
    rng = np.random.default_rng(seed)
    inst = Instance(sample_pool(n, rng), k)
    Q, const = build_qubo_v2(inst)
    t = time.perf_counter()
    opt_sel, ok = exact_max_coverage(inst)
    t_ilp = time.perf_counter() - t
    best = inst.pairwise_coverage(opt_sel)
    g = S.greedy_coverage(inst)
    xg = [1 if i in g else 0 for i in range(n)]
    methods = {
        "random": lambda: S.random_selection(inst, np.random.default_rng(seed + 1)),
        "greedy": lambda: g,
        "sa": lambda: S.bits_to_sel(S.simulated_annealing(Q, const, seed)[0]),
        "ga": lambda: S.bits_to_sel(S.genetic_algorithm(Q, const, seed, pop=100, gens=200)[0]),
        "decomp_exact": lambda: S.bits_to_sel(decomposed(Q, const, xg, m=12, method="exact", seed=seed)[0]),
        "decomp_qaoa": lambda: S.bits_to_sel(decomposed(Q, const, xg, m=qaoa_m, method="qaoa", seed=seed)[0]),
    }
    for name, fn in methods.items():
        t = time.perf_counter()
        sel = fn()
        dt = time.perf_counter() - t
        x = [1 if i in sel else 0 for i in range(n)]
        ev = inst.evaluate(sel)
        w.writerow(dict(n=n, k=k, seed=seed, method=name, seconds=round(dt, 4),
                        qubo_energy=energy(Q, x, const), pairwise_cov=ev["pairwise_cov"],
                        boundary_cov=ev["boundary_cov"], size_ok=ev["size_ok"],
                        optimum_cov=best, gap_to_optimum=best - ev["pairwise_cov"],
                        ilp_optimal=int(ok), ilp_seconds=round(t_ilp, 3),
                        selected=" ".join(map(str, sel))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[50, 100, 200])
    ap.add_argument("--instances", type=int, default=30)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--qaoa_m", type=int, default=10)
    ap.add_argument("--out", default="results/large_v2.csv")
    a = ap.parse_args()
    f = ["n", "k", "seed", "method", "seconds", "qubo_energy", "pairwise_cov", "boundary_cov", "size_ok",
         "optimum_cov", "gap_to_optimum", "ilp_optimal", "ilp_seconds", "selected"]
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=f)
        w.writeheader()
        for n in a.sizes:
            for i in range(a.instances):
                run(n, a.k, BASE + 1000 * n + i, w, a.qaoa_m)
                fh.flush()
                print(f"n={n} instance {i + 1}/{a.instances} done", flush=True)


if __name__ == "__main__":
    main()
