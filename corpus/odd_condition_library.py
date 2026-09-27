"""Formal ODD condition library derived from EU 2022/1426 and UN R157, with traceability.

Every entry is transcribed from the cited clause. Rules followed:
  * operator / threshold / unit are filled ONLY when the clause states them; otherwise
    'qualitative' / 'unspecified' / 'none'.
  * each entry cites the corpus statement id(s) it comes from (eu1426_statements.csv,
    r157_statements.csv) so it can be checked word for word.
  * `kind` separates:
      ODD_CONDITION        - a condition of the operating domain (environment, road, speed)
      BOUNDARY_RESPONSE    - what the system must do when a condition is (no longer) met
      PERFORMANCE_LIMIT    - a numeric capability the system must meet inside the ODD
      ACTIVATION_CONDITION - non-environmental precondition for operation (driver, system state)
  * `model` records how the condition is represented in this repository:
      phaseB predicate id (P1..P8), phaseC simulation parameter, or 'gap'.

    python odd_condition_library.py   # writes odd_condition_library.csv and traceability_matrix.csv
"""
import csv
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

# (cid, kind, dimension, variable, operator, threshold, unit, response, sources, model)
# sources: list of (regulation, paragraph) looked up in the corpora below.
LIB = [
    # ---- EU 2022/1426, Annex II point 3.1.4.1: ODD conditions to be recognised ----
    ("C01", "ODD_CONDITION", "precipitation", "precipitation type", "in", "rain; snow", "none",
     "detect and respond when not fulfilled; MRM to MRC at boundary",
     [("EU", "Annex II, point 3.1.4.1(a)"), ("EU", "Annex II, point 3.1.2"), ("EU", "Annex II, point 3.1.5")], "P1; phaseC Weather/Precipitation"),
    ("C02", "ODD_CONDITION", "lighting", "time of day", "qualitative", "unspecified", "none",
     "detect and respond when not fulfilled; MRM to MRC at boundary",
     [("EU", "Annex II, point 3.1.4.1(b)"), ("EU", "Annex II, point 3.1.2"), ("EU", "Annex II, point 3.1.5")], "P2; phaseC TimeOfDay"),
    ("C03", "ODD_CONDITION", "lighting", "light intensity (incl. use of lighting devices)", "qualitative", "unspecified", "none",
     "detect and respond when not fulfilled; MRM to MRC at boundary",
     [("EU", "Annex II, point 3.1.4.1(c)"), ("EU", "Annex II, point 3.1.2"), ("EU", "Annex II, point 3.1.5")], "P3; phaseC Sun"),
    ("C04", "ODD_CONDITION", "visibility", "airborne obscurant", "in", "fog; mist", "none",
     "detect and respond when not fulfilled; MRM to MRC at boundary",
     [("EU", "Annex II, point 3.1.4.1(d)"), ("EU", "Annex II, point 3.1.2"), ("EU", "Annex II, point 3.1.5")], "P4; phaseC Weather/Fog"),
    ("C05", "ODD_CONDITION", "road_markings", "road and lane marking condition", "qualitative", "unspecified", "none",
     "detect and respond when not fulfilled; MRM to MRC at boundary",
     [("EU", "Annex II, point 3.1.4.1(e)"), ("EU", "Annex II, point 3.1.2"), ("EU", "Annex II, point 3.1.5")], "P5; gap in phaseC (road file not varied)"),
    ("C06", "ODD_CONDITION", "road_type", "road category (number of lanes, separated lanes)", "qualitative", "unspecified", "none",
     "detect and respond when not fulfilled; MRM to MRC at boundary",
     [("EU", "Annex II, point 3.1.4.1(f)"), ("EU", "Annex II, point 3.1.2"), ("EU", "Annex II, point 3.1.5")], "P6; gap in phaseC (road file not varied)"),
    ("C07", "ODD_CONDITION", "geography", "geographical area (if applicable)", "qualitative", "unspecified", "none",
     "detect and respond when not fulfilled; MRM to MRC at boundary",
     [("EU", "Annex II, point 3.1.4.1(g)"), ("EU", "Annex II, point 3.1.2"), ("EU", "Annex II, point 3.1.5")], "gap"),
    ("C08", "ODD_CONDITION", "precipitation", "environmental conditions (e.g. rain, snow)", "qualitative", "unspecified", "none",
     "detect and respond appropriately (e.g. lower speed)",
     [("EU", "Annex II, point 1.2(h)")], "P1"),
    ("C09", "ODD_CONDITION", "speed", "vehicle speed", "qualitative", "safe speed; applicable speed limitations", "none",
     "operate at safe speeds and respect speed limitations",
     [("EU", "Annex II, point 1.1.2(a)")], "gap (speed limit of road not modelled)"),
    # ---- EU 2022/1426 boundary behaviour and performance ----
    ("C10", "BOUNDARY_RESPONSE", "generic", "ODD exit", "qualitative", "unspecified", "none",
     "anticipate exits from the ODD", [("EU", "Annex II, point 3.1.3")], "gap"),
    ("C11", "PERFORMANCE_LIMIT", "generic", "MRM deceleration demand", "<=", "4.0", "m/s2",
     "slow to standstill in safest possible place; higher values allowed for severe failure",
     [("EU", "Annex II, point 5.1")], "gap"),
    ("C12", "PERFORMANCE_LIMIT", "generic", "combined horizontal acceleration (standing/unrestrained occupants)", "<=", "2.4", "m/s2",
     "may be exceeded e.g. in emergency operations", [("EU", "Annex II, point 1.3.2")], "gap"),
    ("C13", "PERFORMANCE_LIMIT", "traffic_participants", "speed at which crossing pedestrian/cyclist collision is avoided", "<=", "60", "km/h",
     "avoid collision (pedestrian lateral speed <= 5 km/h, cyclist <= 15 km/h)", [("EU", "Annex III, point 1.4.3.1.1")], "gap"),
    ("C14", "PERFORMANCE_LIMIT", "traffic_participants", "cut-in collision avoidance", "qualitative", "TTC equation of point 1.4.2", "s",
     "avoid collision independently of environmental conditions (cut-in visible >= 0.72 s)",
     [("EU", "Annex III, point 1.4.2")], "phaseC oracle (collision = FAIL)"),
    # ---- UN R157 ----
    ("C15", "ODD_CONDITION", "speed", "vehicle speed", "<=", "60", "km/h",
     "system not permitted to operate above this speed", [("R157", "paragraph 5.2.3.1"), ("R157", "paragraph 2.1")], "P7; phaseC EgoSpeed"),
    ("C16", "ODD_CONDITION", "road_type", "road with pedestrians and cyclists prohibited and physical separation of opposite traffic", "=", "true", "none",
     "system shall not become active otherwise", [("R157", "paragraph 6.2.3")], "P6"),
    ("C17", "ODD_CONDITION", "generic", "environmental and infrastructural conditions allow operation", "=", "true", "none",
     "system shall not become active otherwise", [("R157", "paragraph 6.2.3")], "P1-P6 (jointly)"),
    ("C18", "ODD_CONDITION", "visibility", "environmental conditions that reduce the detection range", "qualitative", "unspecified", "none",
     "prevent enabling; disable and transfer control to driver; reduce speed when visibility too low",
     [("R157", "paragraph 7.1.3")], "P8; gap in phaseC (sensor range not degraded)"),
    ("C19", "ODD_CONDITION", "generic", "infrastructural and environmental conditions (e.g. narrow curve radii, inclement weather)", "qualitative", "unspecified", "none",
     "adapt vehicle speed", [("R157", "paragraph 5.2.3.2")], "gap"),
    ("C20", "PERFORMANCE_LIMIT", "visibility", "declared forward detection range", ">=", "46", "m",
     "verified by technical service in Annex 5 test", [("R157", "paragraph 7.1.1")], "gap"),
    ("C21", "PERFORMANCE_LIMIT", "traffic_participants", "minimum following distance dmin = v * tfront", ">=", "tfront 1.0-1.6 (table)", "s",
     "adapt speed; readjust after cut-in without harsh braking",
     [("R157", "paragraph 5.2.3.3"), ("R157", "paragraph 5.2.3.3 table")], "phaseC min gap (to be scored)"),
    ("C22", "PERFORMANCE_LIMIT", "traffic_participants", "cut-in lateral movement visible before TTCLaneIntrusion", ">=", "0.72", "s",
     "avoid collision with cutting-in vehicle", [("R157", "paragraph 5.2.5.2")], "phaseC template scenario"),
    ("C23", "PERFORMANCE_LIMIT", "traffic_participants", "crossing pedestrian lateral speed", "<=", "5", "km/h",
     "avoid collision up to maximum operational speed (impact point offset <= 0.2 m)", [("R157", "paragraph 5.2.5.3")], "gap"),
    ("C24", "PERFORMANCE_LIMIT", "generic", "deceleration demand classed as emergency manoeuvre", ">", "5.0", "m/s2",
     "treated as EM", [("R157", "paragraph 5.3.1.1")], "gap"),
    ("C25", "PERFORMANCE_LIMIT", "road_markings", "MRM deceleration demand (lane markings not visible: appropriate trajectory)", "<=", "4.0", "m/s2",
     "slow inside lane to standstill; hazard lights on", [("R157", "paragraph 5.5.1")], "gap"),
    ("C26", "BOUNDARY_RESPONSE", "generic", "time from transition demand to MRM start", ">=", "10", "s",
     "start MRM if driver does not respond", [("R157", "paragraph 5.4.4.1")], "gap"),
    ("C27", "BOUNDARY_RESPONSE", "generic", "time to escalate transition demand", "<=", "4", "s",
     "escalate transition demand", [("R157", "paragraph 5.4.3.2")], "gap"),
    ("C28", "ACTIVATION_CONDITION", "driver", "driver out of seat", ">", "1", "s",
     "initiate transition demand", [("R157", "paragraph 6.1.2")], "out of scope (driver state)"),
    ("C29", "ACTIVATION_CONDITION", "driver", "driver availability criteria confirmed within", "<=", "30", "s",
     "driver deemed unavailable otherwise", [("R157", "paragraph 6.1.3.1")], "out of scope (driver state)"),
]


def load_corpora():
    eu = pd.read_csv(os.path.join(HERE, "eu1426_statements.csv"))
    r157 = pd.read_csv(os.path.join(HERE, "r157_statements.csv"))
    eu["key"] = eu["source"].str.split(r"\), ").str[-1].str.strip()
    r157["key"] = r157["source"].str.split(r"\), ").str[-1].str.strip()
    return {"EU": eu, "R157": r157}


def resolve(corp, reg, para):
    d = corp[reg]
    hit = d[d["key"] == para]
    if hit.empty:
        raise KeyError(f"{reg} {para} not found in corpus")
    return hit.iloc[0]["req_id"]


def main():
    corp = load_corpora()
    lib_rows, tm_rows = [], []
    for cid, kind, dim, var, op, thr, unit, resp, sources, model in LIB:
        ids = [resolve(corp, r, p) for r, p in sources]
        clauses = [f"{'EU 2022/1426' if r == 'EU' else 'UN R157'} {p}" for r, p in sources]
        lib_rows.append(dict(condition_id=cid, kind=kind, odd_dimension=dim, variable=var, operator=op,
                             threshold=thr, unit=unit, response=resp, statement_ids="; ".join(ids),
                             clauses="; ".join(clauses), represented_in=model))
        for sid, cl in zip(ids, clauses):
            tm_rows.append(dict(statement_id=sid, clause=cl, condition_id=cid, kind=kind,
                                represented_in=model, status="gap" if model.startswith(("gap", "out of scope")) else "modelled"))
    lib = pd.DataFrame(lib_rows)
    tm = pd.DataFrame(tm_rows)
    lib.to_csv(os.path.join(HERE, "odd_condition_library.csv"), index=False, quoting=csv.QUOTE_MINIMAL)
    tm.to_csv(os.path.join(HERE, "traceability_matrix.csv"), index=False)
    print(f"{len(lib)} conditions from {tm.statement_id.nunique()} statements")
    print(lib.groupby("kind").size().to_string())
    modelled = ~lib.represented_in.str.startswith(("gap", "out of scope"))
    print(f"modelled in code: {modelled.sum()} / {len(lib)}")


if __name__ == "__main__":
    main()
