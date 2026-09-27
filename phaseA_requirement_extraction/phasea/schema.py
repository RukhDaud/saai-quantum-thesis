"""Label schema shared by all Phase A components.

Matches the Lists sheet of EU1426_annotation_template.xlsx and the
Phase 2 Annotation Guideline. Change it in one place only.
"""
FIELDS = ["has_odd_condition", "odd_dimension", "variable", "operator",
          "threshold", "unit", "response"]
CATEGORICAL = ["has_odd_condition", "odd_dimension", "operator"]
TEXTUAL = ["variable", "threshold", "unit", "response"]

HAS_ODD = ["yes", "no"]
DIMENSIONS = ["precipitation", "visibility", "lighting", "road_markings",
              "road_type", "geography", "speed", "traffic_participants",
              "temperature", "generic", "none"]
OPERATORS = ["<", "<=", ">", ">=", "=", "in", "not in", "qualitative", "none"]


def norm(v):
    """Normalise a cell for comparison: lower-case, collapse spaces, blanks -> ''."""
    if v is None:
        return ""
    s = str(v).strip().lower()
    if s in ("nan", "none_", ""):
        return ""
    return " ".join(s.split())
