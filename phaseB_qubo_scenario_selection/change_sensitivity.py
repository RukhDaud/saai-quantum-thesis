"""E3: sensitivity of change-aware re-selection to the stability weight mu and sub-problem size m.

Same instances, seeds and clause changes as change_experiment.py (n = 16), exact sub-problem solution.

    python change_sensitivity.py
"""
import numpy as np
import pandas as pd

from change_experiment import BASE, CHANGES
from qsel.change import best_feasible, change_aware, feasible
from qsel.instance import Instance, sample_pool
from qsel.odd_space import PREDICATES

MUS = [0.0, 0.5, 1.0, 2.0, 4.0]
MS = [8, 12, 14]


def main(n=16, instances=30):
    rows = []
    for i in range(instances):
        seed = BASE + 1000 * n + i
        pool = sample_pool(n, np.random.default_rng(seed))
        old = Instance(pool, 5)
        old_sel, _ = best_feasible(old)
        for cname, fn in CHANGES.items():
            new = Instance(pool, 5, predicates=fn(PREDICATES))
            _, best_cov = best_feasible(new)
            for mu in MUS:
                for m in MS:
                    sel, info = change_aware(old, new, old_sel, mu=mu, m=m, method="exact", seed=seed)
                    rows.append(dict(seed=seed, change=cname.split(" ")[0], mu=mu, m=m, size_ok=int(len(sel) == 5),
                                     feasible=int(feasible(new, sel)),
                                     cov_ratio=new.pairwise_coverage(sel) / best_cov,
                                     churn=len(set(old_sel) - set(sel))))
        print("instance", i + 1, flush=True)
    d = pd.DataFrame(rows)
    d.to_csv("results/change_sensitivity.csv", index=False)
    s = d.groupby(["mu", "m"]).agg(feasible=("feasible", "mean"), cov_ratio=("cov_ratio", "mean"),
                                   churn=("churn", "mean"), size_ok=("size_ok", "mean")).round(4)
    print(s.to_string())
    s.to_csv("results/change_sensitivity_summary.csv")


if __name__ == "__main__":
    main()
