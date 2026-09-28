"""E2: sensitivity of the fault-detection results to the friction values.

Repeats the Chapter 6 analysis with the lower and upper bounds of the published ranges for wet
asphalt (0.40-0.65) and compacted snow (0.24-0.40) instead of their midpoints (dry stays at the
measured 0.83).

    python friction_sensitivity.py
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sut  # noqa: E402
import fault_detection_model as fdm  # noqa: E402

SETTINGS = {"lower": {"rain": 0.40, "snow": 0.24}, "midpoint": {"rain": 0.525, "snow": 0.32},
            "upper": {"rain": 0.65, "snow": 0.40}}


def main():
    phaseb = os.path.join(HERE, "..", "phaseB_qubo_scenario_selection", "results")
    rows, kills = [], []
    for name, mu in SETTINGS.items():
        sut.MU.update(mu)               # r157_model reads the same dictionary
        sw = fdm.run_sweep()
        km = fdm.kill_matrix(sw)
        res, killable = fdm.score_selections(km, phaseb)
        res = res[res.formulation == "v2"]
        g = res.groupby(["n", "method"]).mutation_score.mean().reset_index()
        g["setting"] = name
        rows.append(g)
        kills.append(dict(setting=name, reference_collisions=int(sw[sw.variant == "reference"].collision.sum()),
                          **{m: int(km[m].sum()) for m in fdm.MUTANTS}, killable=len(killable)))
        print(name, "done", flush=True)
    sut.MU.update(SETTINGS["midpoint"])
    d = pd.concat(rows)
    d.to_csv(os.path.join(HERE, "results", "friction_sensitivity.csv"), index=False)
    k = pd.DataFrame(kills)
    k.to_csv(os.path.join(HERE, "results", "friction_sensitivity_kills.csv"), index=False)
    print(k.to_string(index=False))
    print(d.pivot_table(index=["setting", "n"], columns="method", values="mutation_score").round(3).to_string())


if __name__ == "__main__":
    main()
