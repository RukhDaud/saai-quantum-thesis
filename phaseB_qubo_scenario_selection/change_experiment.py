"""RQ4 experiment: change-aware re-selection after a requirement change.

For each instance, the selection before the change is the best selection that exercises every
clause predicate (exhaustive search). A clause change is then applied to the predicate derived
from it, and each strategy produces the new selection:
  keep_old     - no re-selection
  full_exact   - full n-variable QUBO (coverage-aligned + obligation terms), solved exactly
  full_qaoa    - the same with QAOA (n = 16 only; n = 20 is too slow for statevector simulation)
  aware_exact  - change-aware re-selection (m = 12 variables, stability term), solved exactly
  aware_qaoa   - change-aware re-selection solved with QAOA
Metrics: all clause obligations met (feasible), pairwise coverage relative to the best feasible
selection, tests replaced (churn), variables (qubits) used, time.

The changes are illustrative edits of the kind a regulation amendment makes (adding a combined
condition, tightening a threshold, narrowing or removing a condition); they are not actual
amendments.

    python change_experiment.py --sizes 16 20 --instances 30 --out results/change_rq4.csv
"""
import argparse
import csv
import time

import numpy as np

from qsel.change import (add, best_feasible, change_aware, feasible, full_resolve, impact_set, modify,
                         remove, unmet)
from qsel.instance import Instance, sample_pool
from qsel.odd_space import PREDICATES

BASE = 55550000  # seeds disjoint from all other experiments
MU = 1.0
NOFQ = False

CHANGES = {
    "CH1 add condition: fog at or above 60 km/h":
        lambda P: add(P, "P9", "UN R157 para 7.1.3 [illustrative addition]",
                      lambda s: s["visibility"] == "fog" and s["speed_kmh"] in ("60", "70")),
    "CH2 add condition: lane markings absent in snow":
        lambda P: add(P, "P10", "UN R157 para 5.5.1 [illustrative addition]",
                      lambda s: s["road_markings"] == "absent" and s["precipitation"] == "snow"),
    "CH3 tighten speed boundary (P7: 60/70 -> 70 km/h)":
        lambda P: modify(P, "P7", "UN R157 para 5.2.3.1 [illustrative edit]", lambda s: s["speed_kmh"] == "70"),
    "CH4 narrow obscurant condition (P4: mist/fog -> fog)":
        lambda P: modify(P, "P4", "EU1426-042 [illustrative edit]", lambda s: s["visibility"] == "fog"),
    "CH5 narrow road category (P6: non-motorway -> single carriageway)":
        lambda P: modify(P, "P6", "EU1426-044 [illustrative edit]", lambda s: s["road_category"] == "single_carriageway"),
    "CH6 remove detection-range condition (P8)":
        lambda P: remove(P, "P8"),
}


def run(n, k, seed, w, do_full_qaoa):
    rng = np.random.default_rng(seed)
    pool = sample_pool(n, rng)
    inst_old = Instance(pool, k)
    old_sel, _ = best_feasible(inst_old)
    for cname, fn in CHANGES.items():
        inst_new = Instance(pool, k, predicates=fn(PREDICATES))
        best_sel, best_cov = best_feasible(inst_new)
        imp = impact_set(inst_old, inst_new)
        n_unmet = len(unmet(inst_new, old_sel))
        methods = {"keep_old": lambda: (old_sel, dict(variables=0)),
                   "full_exact": lambda: full_resolve(inst_old, inst_new, old_sel, "exact", seed),
                   "aware_exact": lambda: change_aware(inst_old, inst_new, old_sel, MU, 12, "exact", seed),
                   "aware_qaoa": lambda: change_aware(inst_old, inst_new, old_sel, MU, 12, "qaoa", seed)}
        if do_full_qaoa:
            methods["full_qaoa"] = lambda: full_resolve(inst_old, inst_new, old_sel, "qaoa", seed)
        for mname, f in methods.items():
            t = time.perf_counter()
            sel, info = f()
            dt = time.perf_counter() - t
            cov = inst_new.pairwise_coverage(sel)
            w.writerow(dict(n=n, k=k, seed=seed, change=cname, method=mname, seconds=round(dt, 4),
                            variables=info.get("variables", ""), impact_set=len(imp), unmet_before=n_unmet,
                            size=len(sel), size_ok=int(len(sel) == k), feasible=int(feasible(inst_new, sel)),
                            pairwise_cov=cov, best_cov=best_cov, cov_ratio=round(cov / best_cov, 6),
                            churn=len(set(old_sel) - set(sel)), best_churn=len(set(old_sel) - set(best_sel)),
                            selected=" ".join(map(str, sel))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[16, 20])
    ap.add_argument("--instances", type=int, default=30)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--out", default="results/change_rq4.csv")
    a = ap.parse_args()
    f = ["n", "k", "seed", "change", "method", "seconds", "variables", "impact_set", "unmet_before", "size", "size_ok",
         "feasible", "pairwise_cov", "best_cov", "cov_ratio", "churn", "best_churn", "selected"]
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=f)
        w.writeheader()
        for n in a.sizes:
            for i in range(a.instances):
                run(n, a.k, BASE + 1000 * n + i, w, do_full_qaoa=(n <= 16 and not NOFQ))
                fh.flush()
                print(f"n={n} instance {i + 1}/{a.instances} done", flush=True)


if __name__ == "__main__":
    main()
