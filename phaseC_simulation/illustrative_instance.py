"""One instance of the solver comparison examined in detail (Sections 5.3 and 6.5).

Selects the first instance at n = 16 on which the exact QUBO optimum has higher pairwise coverage than the
greedy heuristic but detects fewer faults, and prints the selections of greedy, QAOA, the exact optimum and
random selection with the faults each scenario reveals. Writes results/illustrative_instance.txt.
"""
import os
import sys

import numpy as np
import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(H, "..", "phaseB_qubo_scenario_selection"))
from qsel.instance import Instance, sample_pool  # noqa: E402
from qsel.odd_space import PREDICATES  # noqa: E402

rv = pd.read_csv(os.path.join(H, "..", "phaseB_qubo_scenario_selection", "results", "runs_v2_full.csv"))
fs = pd.read_csv(os.path.join(H, "results", "fdm_scores.csv"))
km = pd.read_csv(os.path.join(H, "results", "fdm_kill_matrix.csv"))
MUT = [c for c in km.columns if c.startswith("M")]
kills = {(r.precipitation, r.visibility, int(r.speed_kmh)): [m[:2] for m in MUT if getattr(r, m)] for r in km.itertuples()}
N = 16
cv = rv[rv.n == N].pivot_table(index="seed", columns="method", values="pairwise_cov")
ms = fs[(fs.formulation == "v2") & (fs.n == N)].pivot_table(index="seed", columns="method", values="killed")
seed = next(s for s in sorted(cv.index) if cv.loc[s, "exhaustive"] > cv.loc[s, "greedy"] and ms.loc[s, "exhaustive"] < ms.loc[s, "greedy"])
inst = Instance(sample_pool(N, np.random.default_rng(seed)), 5)
L = [f"n = {N}, seed = {seed}, instance {sorted(cv.index).index(seed) + 1}"]
for m in ("greedy", "qaoa", "exhaustive", "random"):
    sel = [int(x) for x in rv[(rv.n == N) & (rv.seed == seed) & (rv.method == m)].selected.iloc[0].split()]
    L.append(f"{m}: coverage {100 * cv.loc[seed, m]:.1f}%, faults {int(ms.loc[seed, m])}")
    for i in sel:
        s = inst.pool[i]
        pr = [p for (p, _, f) in PREDICATES if f(s)]
        k = kills[(s["precipitation"], s["visibility"], int(s["speed_kmh"]))]
        L.append(f"   #{i + 1:2d} {s['precipitation']:5s} {s['lighting']:14s} {s['visibility']:5s} {s['road_markings']:6s} "
                 f"{s['road_category']:19s} {s['speed_kmh']:>2s}  preds {' '.join(pr):24s} reveals {' '.join(k)}")
open(os.path.join(H, "results", "illustrative_instance.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
