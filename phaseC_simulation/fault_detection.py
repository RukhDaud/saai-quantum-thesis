"""Stage 7-8: fault detection of selected scenario sets (mutation analysis in simulation).

1. Every simulation-relevant ODD combination (precipitation x visibility x speed = 27; lighting,
   road markings and road category do not change the simulated physics here) is run in esmini
   with the reference SUT and with each mutant (sut.py): 27 x 7 = 189 runs.
2. A mutant is killed by a scenario when the mutant collides in that scenario and the reference
   SUT does not (a safety-relevant behavioural difference). Scenarios in which the reference SUT
   itself collides are reported separately.
3. For every selection produced in Phase B (v1 and v2 runs, all methods), the mutation score is
   the share of killable mutants killed by at least one selected scenario.

    export ESMINI_HOME=/path/to/esmini
    python fault_detection.py --out results/
"""
import argparse
import itertools
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "phaseB_qubo_scenario_selection"))

from generate_xosc import build  # noqa: E402
from run_sim import run_one  # noqa: E402
from sut import MUTANTS, VARIANTS, configure  # noqa: E402
from qsel.instance import sample_pool  # noqa: E402
from qsel.odd_space import DIMENSIONS  # noqa: E402

SIM_DIMS = ["precipitation", "visibility", "speed_kmh"]
GAP_M = 20.0  # critical cut-in gap: smallest (2.5 m steps from the template 30 m) at which the reference SUT avoids collision, dry, 60 km/h


def simulate_all(outdir):
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for combo in itertools.product(*[DIMENSIONS[d] for d in SIM_DIMS]):
            sc = dict(zip(SIM_DIMS, combo))
            full = {"precipitation": sc["precipitation"], "lighting": "day", "visibility": sc["visibility"],
                    "road_markings": "clear", "road_category": "motorway_separated", "speed_kmh": sc["speed_kmh"]}
            sid = "_".join(combo)
            for v in VARIANTS:
                props, kmh = configure(full, v)
                path = build(full, sid, [], [], model="ReferenceDriver", out_dir=tmp, props=props, ego_kmh=kmh, variant=v, gap_m=GAP_M)
                r = run_one(path)
                rows.append(dict(**sc, variant=v, ego_kmh=kmh, **props, **r))
            print("simulated", sid, flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(outdir, "fd_simulations.csv"), index=False)
    return d


def kill_matrix(sims):
    ref = sims[sims.variant == "reference"].set_index(SIM_DIMS)["collision"]
    km = {}
    for m in MUTANTS:
        mc = sims[sims.variant == m].set_index(SIM_DIMS)["collision"]
        km[m] = ((mc == 1) & (ref == 0)).astype(int)
    k = pd.DataFrame(km)
    k["reference_collision"] = ref
    return k


def selections(phaseb_results):
    out = []
    for fname, form in (("runs_full.csv", "v1"), ("runs_v2_full.csv", "v2")):
        d = pd.read_csv(os.path.join(phaseb_results, fname))
        for r in d.itertuples():
            out.append(dict(formulation=form, n=r.n, seed=r.seed, method=r.method,
                            selected=[int(x) for x in str(r.selected).split()]))
    return out


def score(sel_rows, k):
    killable = [m for m in MUTANTS if k[m].sum() > 0]
    pools = {}
    res = []
    for s in sel_rows:
        key = (s["n"], s["seed"])
        if key not in pools:
            pools[key] = sample_pool(s["n"], np.random.default_rng(s["seed"]))
        pool = pools[key]
        combos = {tuple(pool[i][d] for d in SIM_DIMS) for i in s["selected"]}
        killed = [m for m in killable if any(k.loc[c, m] for c in combos)]
        res.append(dict(formulation=s["formulation"], n=s["n"], seed=s["seed"], method=s["method"],
                        mutants_killed=len(killed), killable=len(killable),
                        mutation_score=len(killed) / len(killable) if killable else float("nan"),
                        killed=" ".join(killed),
                        reference_failures=int(sum(k.loc[c, "reference_collision"] for c in combos))))
    return pd.DataFrame(res), killable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--phaseb", default=os.path.join(HERE, "..", "phaseB_qubo_scenario_selection", "results"))
    ap.add_argument("--reuse", action="store_true", help="reuse fd_simulations.csv")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sims = pd.read_csv(os.path.join(a.out, "fd_simulations.csv"), dtype={"speed_kmh": str}) if a.reuse else simulate_all(a.out)
    sims["speed_kmh"] = sims["speed_kmh"].astype(str)
    k = kill_matrix(sims)
    k.to_csv(os.path.join(a.out, "fd_kill_matrix.csv"))
    print(k.to_string())
    res, killable = score(selections(a.phaseb), k)
    res.to_csv(os.path.join(a.out, "fd_scores.csv"), index=False)
    print("killable mutants:", killable)
    print(res.groupby(["formulation", "n", "method"]).mutation_score.mean().unstack().round(3).to_string())
    json.dump({"killable": killable, "mutants": MUTANTS}, open(os.path.join(a.out, "fd_meta.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
