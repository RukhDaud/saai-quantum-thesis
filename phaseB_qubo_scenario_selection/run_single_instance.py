"""Single-instance run with full trace: ODD-boundary scenario selection as a QUBO, solved classically and with QAOA.

    python run_single_instance.py                 # n=12 candidate scenarios, choose k=5 (runs in a few seconds)
    python run_single_instance.py --n 14 --seed 7

Walks through the pipeline step by step:
  1. Requirement-derived ODD boundary predicates (each traced to its regulation clause)
  2. A pool of candidate test scenarios from the ODD grid
  3. The QUBO built from the pool
  4. Every solver's selection (random, greedy, GA, simulated annealing, QAOA simulator, exhaustive)
  5. Results table + traceability of the QAOA selection back to the regulation
"""
import argparse
import time

import numpy as np

from qsel import solvers as S
from qsel.instance import Instance, sample_pool
from qsel.odd_space import DIMENSIONS, DIM_NAMES, PREDICATES
from qsel.qubo import all_energies, build_qubo, energy

LINE = "=" * 96


def show_scenario(i, s, inst):
    preds = [PREDICATES[j][0] for j in np.where(inst.pred[i])[0]]
    vals = ", ".join(f"{d}={s[d]}" for d in DIM_NAMES)
    return f"  S{i:02d}: {vals}  -> {' '.join(preds) or '-'}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12, help="number of candidate scenarios (qubits)")
    ap.add_argument("--k", type=int, default=5, help="scenarios to select")
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()

    print(LINE + "\nSTEP 1  ODD boundary predicates derived from safety requirements\n" + LINE)
    for pid, src, _ in PREDICATES:
        print(f"  {pid}: {src}")
    print("\n  ODD dimensions and levels:")
    for d, lv in DIMENSIONS.items():
        print(f"    {d:14s} {lv}")

    rng = np.random.default_rng(a.seed)
    inst = Instance(sample_pool(a.n, rng), a.k)
    print("\n" + LINE + f"\nSTEP 2  Candidate pool: {a.n} scenarios (seed {a.seed}); budget k = {a.k}\n" + LINE)
    for i, s in enumerate(inst.pool):
        print(show_scenario(i, s, inst))

    Q, const = build_qubo(inst)
    print("\n" + LINE + "\nSTEP 3  QUBO  min x^T Q x   (x_i = 1 if scenario i is selected)\n" + LINE)
    print(f"  variables (qubits): {a.n}   non-zero couplings: {int(np.count_nonzero(np.triu(Q, 1)))}")
    print("  terms: reward rare 2-way interactions, reward boundary predicates,")
    print("         penalise redundant overlap, penalty C*(sum x - k)^2 enforces the budget")
    t = time.perf_counter()
    E = all_energies(Q, const)
    x_opt, e_opt = S.exhaustive(Q, const, E)
    t_ex = time.perf_counter() - t
    print(f"  exhaustive search over 2^{a.n} = {2 ** a.n:,} states: optimum energy {e_opt:.4f}")

    print("\n" + LINE + "\nSTEP 4  Solving\n" + LINE)
    runs = {}

    def timed(name, fn):
        t = time.perf_counter()
        sel = fn()
        runs[name] = (sorted(sel), time.perf_counter() - t)
        print(f"  {name:22s} done in {runs[name][1]:7.3f} s   selected {sorted(sel)}")

    timed("Random", lambda: S.random_selection(inst, np.random.default_rng(a.seed + 1)))
    timed("Greedy", lambda: S.greedy_coverage(inst))
    timed("Genetic algorithm", lambda: S.bits_to_sel(S.genetic_algorithm(Q, const, a.seed)[0]))
    timed("Simulated annealing", lambda: S.bits_to_sel(S.simulated_annealing(Q, const, a.seed)[0]))
    qinfo = {}

    def run_qaoa():
        x, _, info = S.qaoa(Q, const, a.seed, p=2, restarts=3, E_all=E)
        qinfo.update(info)
        return S.bits_to_sel(x)

    timed("QAOA (p=2, simulator)", run_qaoa)
    runs["Exhaustive (optimum)"] = (sorted(S.bits_to_sel(x_opt)), t_ex)
    print(f"  {'Exhaustive (optimum)':22s} done in {t_ex:7.3f} s   selected {runs['Exhaustive (optimum)'][0]}")
    print(f"\n  QAOA: probability of measuring the optimal selection = {qinfo['p_opt']:.4f}"
          f"  (uniform guess would be {1 / 2 ** a.n:.6f}); optimiser evaluations = {qinfo['nfev']}")

    print("\n" + LINE + "\nSTEP 5  Results (true coverage metrics, computed independently of the QUBO)\n" + LINE)
    print(f"  {'Method':22s} {'size':>4s} {'pairwise':>9s} {'boundary':>9s} {'predicate':>9s} {'QUBO gap':>9s} {'time s':>8s}")
    for name, (sel, dt) in runs.items():
        ev = inst.evaluate(sel)
        x = [1 if i in sel else 0 for i in range(a.n)]
        gap = energy(Q, x, const) - e_opt
        print(f"  {name:22s} {ev['size']:4d} {ev['pairwise_cov']:9.1%} {ev['boundary_cov']:9.1%}"
              f" {ev['predicate_cov']:9.1%} {gap:9.4f} {dt:8.3f}")

    print("\n  Traceability of the QAOA selection:")
    for i in runs["QAOA (p=2, simulator)"][0]:
        srcs = [PREDICATES[j][1] for j in np.where(inst.pred[i])[0]]
        print(show_scenario(i, inst.pool[i], inst))
        for src in srcs:
            print(f"        traces to {src}")


if __name__ == "__main__":
    main()
