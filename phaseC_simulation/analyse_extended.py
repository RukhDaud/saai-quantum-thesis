"""Extended analysis of the fault-detection results (Chapter 6 detail tables).

Writes results/analysis_extended.txt with:
  A  operating speed of the reference system per ODD condition and scenario speed
  B  reference-system collisions by initial gap and cut-in speed ratio, and by condition
  C  concrete manoeuvres in which each fault is revealed, by precipitation and speed
  D  agreement of the model with esmini by gap and ratio (confusion counts, Cohen's kappa)
  E  share of selections detecting each fault, per method (coverage-aligned formulation)
  F  mutation score against random selection (Wilcoxon), both formulations
  G  friction sensitivity per setting and method

    python analyse_extended.py
"""
import itertools
import os

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from r157_model import G, REF, ego_speed, params
from sut import MU, VIS_M

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(H, "results")
L = []


def out(s=""):
    L.append(str(s))


# ---------------------------------------------------------------- A
out("A. Reference operating speed (km/h) by precipitation, visibility and scenario speed")
p = params("reference")
for prec, vis in itertools.product(("none", "rain", "snow"), ("clear", "mist", "fog")):
    rng = p["range_m"] if VIS_M[vis] is None else min(p["range_m"], VIS_M[vis])
    row = [f"{3.6 * ego_speed(float(s), MU[prec], rng, p):5.1f}" for s in (40, 60, 70)]
    out(f"{prec:5s} {vis:6s} mu={MU[prec]:.3f} range={rng:5.0f} m  -> 40/60/70: {' '.join(row)}  "
        f"a_max={min(p['drv_dec'], MU[prec] * G):.2f} m/s2")
out()

sw = pd.read_csv(os.path.join(R, "fdm_sweep.csv"))
ref = sw[sw.variant == "reference"].copy()
out("B. Reference collisions by gap (rows) and cut-in speed ratio (columns), of 27 scenarios each")
out(ref.pivot_table(index="gap_m", columns="ratio", values="collision", aggfunc="sum").to_string())
out("by precipitation: " + str(ref.groupby("precipitation").collision.sum().to_dict()))
out("by visibility: " + str(ref.groupby("visibility").collision.sum().to_dict()))
out("by speed: " + str(ref.groupby("speed_kmh").collision.sum().to_dict()))
out()

key = ["precipitation", "visibility", "speed_kmh", "gap_m", "ratio"]
base = ref.set_index(key).collision
out("C. Concrete manoeuvres revealing each fault (fault collides, reference does not)")
for v in sorted(sw.variant.unique()):
    if v == "reference":
        continue
    d = sw[sw.variant == v].set_index(key)
    k = ((d.collision == 1) & (base == 0))
    kk = k.rename("kill").reset_index()
    out(f"{v:24s} total {int(k.sum()):3d}  by precipitation {kk.groupby('precipitation')['kill'].sum().to_dict()}  "
        f"by speed {kk.groupby('speed_kmh')['kill'].sum().to_dict()}  by ratio {kk.groupby('ratio')['kill'].sum().to_dict()}")
out()

cc = pd.read_csv(os.path.join(R, "fdm_crosscheck_esmini.csv"))
out("D. Model vs esmini on the reference system")
agree = (cc.model_collision == cc.esmini_collision)
po = agree.mean()
p1, p2 = cc.model_collision.mean(), cc.esmini_collision.mean()
pe = p1 * p2 + (1 - p1) * (1 - p2)
out(f"agreement {100 * po:.1f}%  kappa {(po - pe) / (1 - pe):.3f}  model collisions {cc.model_collision.sum()}  "
    f"esmini collisions {cc.esmini_collision.sum()}")
out("confusion (model, esmini): " + str(cc.groupby(["model_collision", "esmini_collision"]).size().to_dict()))
g = cc.assign(agree=agree).groupby("gap_m").agg(agree=("agree", "mean"), model=("model_collision", "sum"),
                                                 esmini=("esmini_collision", "sum"))
out(g.to_string())
out("by ratio: " + str(cc.assign(agree=agree).groupby("ratio").agree.mean().round(3).to_dict()))
out()

sc = pd.read_csv(os.path.join(R, "fdm_scores.csv"))
MUT = ["M1_surface_unaware", "M2_aeb_unavailable", "M3_no_speed_cap", "M4_late_reaction", "M5_weak_brakes",
       "M6_visibility_unaware"]
out("E. Share of selections detecting each fault (coverage-aligned formulation, 90 selections per method)")
v2 = sc[sc.formulation == "v2"]
for m, d in v2.groupby("method"):
    s = " ".join(f"{mm[:2]} {100 * d.killed_mutants.fillna('').str.contains(mm).mean():5.1f}" for mm in MUT)
    out(f"{m:11s} {s}   mean score {d.mutation_score.mean():.3f}")
out()

out("F. Mutation score against random selection (Wilcoxon p; wins/ties/losses of the method)")
for f in ("v1", "v2"):
    for n in (12, 16, 20):
        d = sc[(sc.formulation == f) & (sc.n == n)].pivot_table(index="seed", columns="method", values="mutation_score")
        parts = []
        for m in ("greedy", "ga", "sa", "qaoa", "exhaustive"):
            diff = d[m] - d["random"]
            pv = wilcoxon(d[m], d["random"]).pvalue if (diff != 0).any() else 1.0
            parts.append(f"{m} p={pv:.3f} {(diff > 0).sum()}/{(diff == 0).sum()}/{(diff < 0).sum()}")
        out(f"{f} n={n}: " + "; ".join(parts))
out()

fs = pd.read_csv(os.path.join(R, "friction_sensitivity.csv"))
out("G. Friction sensitivity: mean mutation score per setting (mean over n = 12, 16, 20)")
out(fs.groupby(["setting", "method"]).mutation_score.mean().unstack(0).round(3).to_string())
out(pd.read_csv(os.path.join(R, "friction_sensitivity_kills.csv")).to_string(index=False))

from scipy.stats import spearmanr  # noqa: E402
out()
out("H. Spearman correlation between pairwise coverage and mutation score (coverage-aligned), per method and pooled")
for n in (12, 16, 20):
    d = v2[v2.n == n]
    parts = [f"pooled {spearmanr(d.pairwise_cov, d.mutation_score).correlation:.2f}"]
    for m, dm in d.groupby("method"):
        parts.append(f"{m} {spearmanr(dm.pairwise_cov, dm.mutation_score).correlation:.2f}")
    out(f"n={n}: " + "; ".join(parts))
ub = pd.read_csv(os.path.join(R, "fdm_upper_bound.csv")).set_index(["n", "seed"]).best
hv = v2.assign(best=[ub[(a, b)] for a, b in zip(v2.n, v2.seed)])
hv["hit"] = hv.mutation_score >= hv.best - 1e-9
out("I. Share of instances on which the method reached the best achievable score")
out(hv.groupby(["n", "method"]).hit.mean().unstack().round(3).to_string())
out("Best achievable score distribution: " + str(pd.read_csv(os.path.join(R, "fdm_upper_bound.csv")).groupby("n").best.value_counts().to_dict()))

open(os.path.join(R, "analysis_extended.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
