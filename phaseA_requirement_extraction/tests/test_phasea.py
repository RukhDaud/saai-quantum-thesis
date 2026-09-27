"""Toy tests: check the plumbing, not the science. Toy labels are invented
for the test only and are never reported as results."""
import pandas as pd

from phasea.evaluate import evaluate
from phasea.rule_baseline import predict_one
from phasea.tfidf_baseline import fit_predict


def test_rule_numbers_and_operator():
    p = predict_one("The system shall operate only up to a maximum speed of 60 km/h within the ODD.")
    assert p["has_odd_condition"] == "yes"
    assert p["odd_dimension"] == "speed"
    assert p["operator"] == "<="
    assert (p["threshold"], p["unit"]) == ("60", "km/h")


def test_rule_never_invents_threshold():
    p = predict_one("The ADS shall detect fog that reduces the detection range.")
    assert p["threshold"] == "unspecified" and p["unit"] == "none"


def test_rule_no_odd():
    p = predict_one("The manufacturer shall provide documentation to the technical service.")
    assert p["has_odd_condition"] == "no" and p["odd_dimension"] == "none"


def _toy():
    rows = [("r%d" % i, t, h, d, o) for i, (t, h, d, o) in enumerate([
        ("operate in rain within the ODD", "yes", "precipitation", "qualitative"),
        ("snow outside the ODD triggers MRM", "yes", "precipitation", "not in"),
        ("fog reduces visibility within the ODD", "yes", "visibility", "qualitative"),
        ("visibility below 50 m outside the ODD", "yes", "visibility", "<"),
        ("documentation shall be provided", "no", "none", "none"),
        ("the manufacturer shall keep records", "no", "none", "none"),
    ])]
    df = pd.DataFrame(rows, columns=["req_id", "text", "has_odd_condition", "odd_dimension", "operator"])
    for f in ["variable", "threshold", "unit", "response"]:
        df[f] = ""
    return df


def test_evaluate_perfect_is_one():
    g = _toy()
    s, _, _ = evaluate(g, g.copy())
    assert (s.loc[s.metric == "accuracy", "value"] == 1.0).all()


def test_tfidf_runs():
    g = _toy()
    p = fit_predict(g, g)
    assert len(p) == len(g) and set(p.columns) >= {"has_odd_condition", "odd_dimension", "operator"}
