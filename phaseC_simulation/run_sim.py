"""Stage 7: execute generated .xosc files in esmini (headless) and score each run.

Per run: collision (esmini CollisionCondition / bounding-box overlap), minimum
bumper-to-bumper gap in the ego lane, minimum time-to-collision, verdict FAIL if
collision else PASS.

    export ESMINI_HOME=/path/to/esmini        # built from source, see README
    python run_sim.py generated/*.xosc --out results/sim_results.csv
"""
import argparse
import csv
import glob
import json
import os
import subprocess
import tempfile

ESMINI = os.path.join(os.environ.get("ESMINI_HOME", ""), "build", "EnvironmentSimulator",
                      "Applications", "esmini", "esmini")


def parse_csv(path):
    with open(path) as f:
        lines = f.read().splitlines()
    h = next(i for i, l in enumerate(lines) if l.startswith("Index"))
    cols = [c.strip() for c in lines[h].split(",")]
    rows = [[c.strip() for c in l.split(",")] for l in lines[h + 1:] if l.strip()]
    ci = {c: i for i, c in enumerate(cols)}
    per_block = len([c for c in cols if c.startswith("#1 ")])
    out = {}
    for r in rows:
        t = float(r[1])
        for b in range(2):  # Ego, Target
            base = 2 + b * per_block
            name = r[base]
            x = float(r[base + ci["#1 World_Position_X [m]"] - 2])
            y = float(r[base + ci["#1 World_Position_Y [m]"] - 2])
            v = float(r[base + ci["#1 Current_Speed [m/s]"] - 2])
            L = float(r[base + ci["#1 bb_length [m]"] - 2])
            out.setdefault(t, {})[name] = (x, y, v, L)
    return out


def score(traj):
    min_gap, min_ttc = float("inf"), float("inf")
    for t, d in sorted(traj.items()):
        if "Ego" not in d or "Target" not in d:
            continue
        (xe, ye, ve, Le), (xt, yt, vt, Lt) = d["Ego"], d["Target"]
        if abs(ye - yt) < 1.75 and xt > xe:  # target ahead in (roughly) the same lane
            gap = (xt - xe) - (Le + Lt) / 2
            min_gap = min(min_gap, gap)
            if ve > vt:
                min_ttc = min(min_ttc, max(gap, 0) / (ve - vt))
    return min_gap, min_ttc


def run_one(xosc, dt=0.05):
    with tempfile.TemporaryDirectory() as tmp:
        log = os.path.join(tmp, "log.csv")
        p = subprocess.run([ESMINI, "--headless", "--osc", xosc, "--fixed_timestep", str(dt),
                            "--collision", "--csv_logger", log], capture_output=True, text=True, timeout=120)
        txt = p.stdout + p.stderr
        collided = "CollisionCondition: true" in txt
        min_gap, min_ttc = score(parse_csv(log))
    collided = collided or min_gap <= 0
    return {"collision": int(collided), "min_gap_m": round(min_gap, 3),
            "min_ttc_s": round(min_ttc, 3) if min_ttc != float("inf") else "",
            "verdict": "FAIL" if collided else "PASS", "esmini_rc": p.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default="results/sim_results.csv")
    a = ap.parse_args()
    files = sorted(f for g in a.files for f in glob.glob(g))
    rows = []
    for f in files:
        meta = json.load(open(f[:-5] + ".json"))
        r = {"scenario_id": meta["scenario_id"], "model": meta["model"], **meta["odd"],
             "predicates": " ".join(meta["predicates"]), "traces_to": " | ".join(meta["traces_to"]),
             **run_one(f)}
        rows.append(r)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    fails = sum(r["verdict"] == "FAIL" for r in rows)
    print(f"{len(rows)} runs, {fails} FAIL, {len(rows) - fails} PASS -> {a.out}")


if __name__ == "__main__":
    main()
