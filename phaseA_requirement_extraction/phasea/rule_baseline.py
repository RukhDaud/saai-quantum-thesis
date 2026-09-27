"""Baseline 1: transparent rule/lexicon extractor.

Every decision comes from a keyword or regular expression listed below, so a
reviewer can trace why a label was produced. It is the floor any learned
model must beat. It never invents a threshold: if no number is in the text,
threshold = 'unspecified' and unit = 'none'.

Usage:
    python -m phasea.rule_baseline data_eu1426.csv --out results/rule_predictions.csv
"""
import argparse
import re

import pandas as pd

# Keyword lexicon per ODD dimension (lower-case, matched on word boundaries).
LEXICON = {
    "precipitation": ["rain", "snow", "precipitation", "hail", "sleet", "ice"],
    "visibility": ["visibility", "fog", "mist", "airborne obscurant", "detection range", "spray", "dust"],
    "lighting": ["glare", "illumination", "lighting", "night", "darkness", "daylight", "sun"],
    "road_markings": ["lane marking", "road marking", "markings"],
    "road_type": ["motorway", "road type", "physical separation", "carriageway", "junction", "roundabout",
                  "tunnel", "toll", "intersection", "road geometry", "curvature", "gradient"],
    "geography": ["geographic", "geo-fenc", "area", "country", "region", "zone"],
    "speed": ["speed", "km/h", "velocity"],
    "traffic_participants": ["pedestrian", "cyclist", "vulnerable road user", "road users", "traffic"],
    "temperature": ["temperature", "°c", "degrees"],
}
# Phrases that signal the statement is conditioned on the ODD or its boundary.
ODD_TRIGGERS = [r"\bodd\b", r"operational design domain", r"odd boundar", r"within the odd",
                r"outside the odd", r"odd condition", r"odd limit", r"environmental condition",
                r"weather condition"]

OPERATOR_PATTERNS = [  # order matters: longer/more specific first
    (r"\b(not exceed|no more than|up to|maximum|at most|shall not be greater than)\b", "<="),
    (r"\b(at least|minimum|no less than|not less than)\b", ">="),
    (r"\b(less than|below|lower than|under)\b", "<"),
    (r"\b(more than|greater than|above|exceed(s|ing)?)\b", ">"),
    (r"\b(outside|except|excluding|other than)\b", "not in"),
    (r"\b(within|one of|including|such as)\b", "in"),
    (r"\b(equal to|exactly)\b", "="),
]
NUM_UNIT = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(km/h|m/s2|m/s²|m/s|km|m|s|ms|%|°c|lux|degrees?)\b", re.I)

RESPONSE_PAT = re.compile(
    r"(minimal risk manoeuvre|minimal risk maneuver|\bmrm\b|minimal risk condition|\bmrc\b|"
    r"transition demand|warn[a-z]*|deactivat[a-z]*|hand ?over|take[- ]?over|reduce (the )?speed|"
    r"come to a (stop|standstill)|stop the vehicle)", re.I)


def _has(text, word):
    return re.search(r"(?<![a-z])" + re.escape(word), text) is not None


def predict_one(text):
    t = str(text).lower()
    hits = {d: sum(_has(t, w) for w in ws) for d, ws in LEXICON.items()}
    best = max(hits, key=hits.get)
    trigger = any(re.search(p, t) for p in ODD_TRIGGERS)
    has_odd = "yes" if (trigger or hits[best] > 0 and best in
                        ("precipitation", "visibility", "lighting", "road_markings", "temperature")) else "no"
    if has_odd == "no":
        dim = "none"
    elif hits[best] == 0:
        dim = "generic"
    else:
        dim = best
    m = NUM_UNIT.search(t)
    threshold, unit = (m.group(1), m.group(2).lower()) if m else ("unspecified", "none")
    op = "none"
    if has_odd == "yes":
        op = "qualitative"
        for pat, lab in OPERATOR_PATTERNS:
            if re.search(pat, t):
                op = lab
                break
    variable = ""
    if dim not in ("none", "generic"):
        # the lexicon word that matched first in the sentence is used as the variable name
        found = [(t.find(w), w) for w in LEXICON[dim] if _has(t, w)]
        variable = min(found)[1] if found else ""
    elif dim == "generic":
        variable = "position relative to ODD boundary"
    r = RESPONSE_PAT.search(t)
    response = r.group(0) if (r and has_odd == "yes") else ""
    return {"has_odd_condition": has_odd, "odd_dimension": dim, "variable": variable,
            "operator": op, "threshold": threshold if has_odd == "yes" else "",
            "unit": unit if has_odd == "yes" else "", "response": response}


def predict(df):
    rows = [dict(req_id=r.req_id, **predict_one(r.text)) for r in df.itertuples()]
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("--out", default="results/rule_predictions.csv")
    a = ap.parse_args()
    df = pd.read_csv(a.corpus)
    p = predict(df)
    p.to_csv(a.out, index=False)
    print(f"wrote {len(p)} predictions to {a.out}")
    print(p["has_odd_condition"].value_counts().to_string())
    print(p["odd_dimension"].value_counts().to_string())


if __name__ == "__main__":
    main()
