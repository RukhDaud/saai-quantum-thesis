"""Fault detection of the Phase B selections with the R157 longitudinal model (RQ2, fault part).

Each ODD scenario is a logical scenario; it is executed as a fixed sweep of concrete cut-in
manoeuvres (initial gap 7.5-30 m in 2.5 m steps; cutting-in speed 0.5 or 0.75 x scenario speed;
lead vehicle brakes at its full braking performance on the surface). A mutant is killed by an ODD
scenario if, in at least one concrete manoeuvre, the mutant collides and the reference system does
not. The mutation score of a selection is the share of killable mutants killed by at least one
of its scenarios.

Cross-check: the reference system's verdicts are compared with esmini's ALKS ReferenceDriver on the
same concrete manoeuvres (patched esmini, same speeds, gap and lead braking).

    python fault_detection_model.py [--crosscheck]      # ESMINI_HOME needed for --crosscheck
"""
import argparse
import itertools
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "phaseB_qubo_scenario_selection"))

from r157_model import MUTANT_TEXT, MUTANTS, params, simulate, ego_speed  # noqa: E402
from sut import MU, VIS_M  # noqa: E402
from qsel.instance import sample_pool  # noqa: E402
from qsel.odd_space import DIMENSIONS  # noqa: E402

SIM_DIMS = ["precipitation", "visibility", "speed_kmh"]
GAPS = [7.5 + 2.5 * i for i in range(10)]
RATIOS = [0.5, 0.75]


def run_sweep():
    rows = []
    for c in itertools.product(*[DIMENSIONS[d] for d in SIM_DIMS]):
        sc = dict(zip(SIM_DIMS, c))
        for g in GAPS:
            for r in RATIOS:
                for v in ["reference"] + list(MUTANTS):
                    rows.append(dict(**sc, gap_m=g, ratio=r, variant=v, **simulate(sc, v, g, r)))
    return pd.DataFrame(rows)


def kill_matrix(sw):
    key = SIM_DIMS + ["gap_m", "ratio"]
    ref = sw[sw.variant == "reference"].set_index(key)["collision"]
    k = {}
    for m in MUTANTS:
        mc = sw[sw.variant == m].set_index(key)["collision"]
        k[m] = ((mc == 1) & (ref == 0)).groupby(level=SIM_DIMS).any().astype(int)
    km = pd.DataFrame(k)
    km["reference_collisions"] = ref.groupby(level=SIM_DIMS).sum()
    return km


def score_selections(km, phaseb):
    killable = [m for m in MUTANTS if km[m].sum() > 0]
    pools, rows = {}, []
    for fname, form in (("runs_full.csv", "v1"), ("runs_v2_full.csv", "v2")):
        d = pd.read_csv(os.path.join(phaseb, fname))
        for r in d.itertuples():
            key = (r.n, r.seed)
            if key not in pools:
                pools[key] = sample_pool(r.n, np.random.default_rng(r.seed))
            sel = [int(x) for x in str(r.selected).split()]
            combos = {tuple(pools[key][i][dm] for dm in SIM_DIMS) for i in sel}
            killed = [m for m in killable if any(km.loc[c, m] for c in combos)]
            rows.append(dict(formulation=form, n=r.n, seed=r.seed, method=r.method, pairwise_cov=r.pairwise_cov,
                             killed=len(killed), killable=len(killable), mutation_score=len(killed) / len(killable),
                             killed_mutants=" ".join(killed)))
    return pd.DataFrame(rows), killable


def stats(res):
    out = []
    for (form, n), g in res.groupby(["formulation", "n"]):
        base = g[g.method == "greedy"].set_index("seed").mutation_score
        for m in sorted(g.method.unique()):
            x = g[g.method == m].set_index("seed").mutation_score
            diff = x - base
            p = wilcoxon(x, base).pvalue if (diff != 0).any() else 1.0
            out.append(dict(formulation=form, n=n, method=m, mean_score=x.mean(), wins=int((diff > 0).sum()),
                            ties=int((diff == 0).sum()), losses=int((diff < 0).sum()), wilcoxon_p=p))
    return pd.DataFrame(out)


def crosscheck(sw):
    from generate_xosc import build
    from run_sim import run_one
    ref = sw[sw.variant == "reference"]
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for r in ref.itertuples():
            sc = {"precipitation": r.precipitation, "lighting": "day", "visibility": r.visibility,
                  "road_markings": "clear", "road_category": "motorway_separated", "speed_kmh": r.speed_kmh}
            p = params("reference")
            mu = MU[r.precipitation]
            rng = p["range_m"] if VIS_M[r.visibility] is None else min(p["range_m"], VIS_M[r.visibility])
            kmh = ego_speed(float(r.speed_kmh), mu, rng, p) * 3.6
            a = mu * 9.81
            props = {"frictionLimit": round(a, 4), "maxRange": rng, "reactionTime": p["reaction"],
                     "driverDeceleration": round(min(p["drv_dec"], a), 4), "aebDeceleration": round(min(p["aeb_dec"], a), 4)}
            path = build(sc, "x", [], [], model="ReferenceDriver", out_dir=tmp, props=props, ego_kmh=kmh,
                         variant="ref", gap_m=r.gap_m)
            # lead vehicle: speed ratio and full braking on the surface
            import xml.etree.ElementTree as ET
            t = ET.parse(path)
            for pd_ in t.getroot().iter("ParameterDeclaration"):
                if pd_.get("name") == "TargetSpeed":
                    pd_.set("value", f"{r.ratio * float(r.speed_kmh) / 3.6:.4f}")
                if pd_.get("name") == "TargetBrakeRate":
                    pd_.set("value", f"{a:.4f}")
            t.write(path)
            e = run_one(path)
            rows.append(dict(precipitation=r.precipitation, visibility=r.visibility, speed_kmh=r.speed_kmh,
                             gap_m=r.gap_m, ratio=r.ratio, model_collision=r.collision, esmini_collision=e["collision"]))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    ap.add_argument("--phaseb", default=os.path.join(HERE, "..", "phaseB_qubo_scenario_selection", "results"))
    ap.add_argument("--crosscheck", action="store_true")
    a = ap.parse_args()
    sw = run_sweep()
    sw.to_csv(os.path.join(a.out, "fdm_sweep.csv"), index=False)
    km = kill_matrix(sw)
    km.to_csv(os.path.join(a.out, "fdm_kill_matrix.csv"))
    res, killable = score_selections(km, a.phaseb)
    res.to_csv(os.path.join(a.out, "fdm_scores.csv"), index=False)
    st = stats(res)
    st.to_csv(os.path.join(a.out, "fdm_stats.csv"), index=False)
    json.dump({"killable": killable, "mutants": MUTANT_TEXT, "gaps": GAPS, "ratios": RATIOS,
               "reference_collisions": int(sw[sw.variant == "reference"].collision.sum()),
               "concrete_runs_per_variant": int((sw.variant == "reference").sum())},
              open(os.path.join(a.out, "fdm_meta.json"), "w"), indent=1)
    pd.set_option("display.width", 200)
    print("killable:", killable)
    print(km.sum().to_string())
    print(st.round(4).to_string(index=False))
    rho = res.groupby(["formulation", "n"]).apply(lambda g: g[["pairwise_cov", "mutation_score"]].corr(method="spearman").iloc[0, 1])
    print("Spearman(pairwise coverage, mutation score):\n", rho.round(3).to_string())
    if a.crosscheck:
        cc = crosscheck(sw)
        cc.to_csv(os.path.join(a.out, "fdm_crosscheck_esmini.csv"), index=False)
        agree = (cc.model_collision == cc.esmini_collision).mean()
        print(f"cross-check with esmini: verdict agreement {agree:.3f} on {len(cc)} concrete manoeuvres;",
              "model collisions", int(cc.model_collision.sum()), "esmini collisions", int(cc.esmini_collision.sum()))


if __name__ == "__main__":
    main()
