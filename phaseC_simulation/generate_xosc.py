"""Stage 6: turn selected ODD scenarios into executable OpenSCENARIO (.xosc) files.

Base scenario: esmini's `alks_r157_cut_in_quick_brake.xosc` (MPL-2.0, esmini commit
61b44a7), a UN R157 cut-in-and-brake test with the ego vehicle driven by esmini's
ALKS_R157SM_Controller. For each ODD scenario we set:
  * ego and target speed from the scenario's speed_kmh level,
  * an OpenSCENARIO EnvironmentAction (TimeOfDay, Weather: sun, fog visual range,
    precipitation) from the lighting / visibility / precipitation levels,
  * the controller model (Regulation or ReferenceDriver),
and write traceability metadata (scenario id, ODD levels, predicates, regulation clauses)
into the file header and a JSON side-car.

Mapping of ODD levels to OpenSCENARIO values is in ENV_MAP below, in one place.
"""
import json
import os
import re
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "templates", "alks_r157_cut_in_quick_brake.xosc")

# OpenSCENARIO 1.1 Environment values per ODD level.
# precipitation: precipitationType is an enumeration in the standard (dry/rain/snow).
# visibility: Fog@visualRange in metres. lighting: TimeOfDay + Sun elevation (rad).
ENV_MAP = {
    "precipitation": {"none": ("dry", 0.0), "rain": ("rain", 1.0), "snow": ("snow", 1.0)},
    "visibility": {"clear": 100000.0, "mist": 1000.0, "fog": 100.0},
    "lighting": {"day": ("12:00:00", 1.0), "dusk": ("19:30:00", 0.05),
                 "night": ("23:00:00", -0.5), "low_sun_glare": ("07:00:00", 0.05)},
}


def environment_action(s):
    ptype, pint = ENV_MAP["precipitation"][s["precipitation"]]
    tod, sun_el = ENV_MAP["lighting"][s["lighting"]]
    ga = ET.Element("GlobalAction")
    ea = ET.SubElement(ga, "EnvironmentAction")
    env = ET.SubElement(ea, "Environment", name="ODDEnvironment")
    ET.SubElement(env, "TimeOfDay", animation="false", dateTime=f"2026-06-21T{tod}")
    w = ET.SubElement(env, "Weather", atmosphericPressure="101325", temperature="288")
    ET.SubElement(w, "Sun", azimuth="0", elevation=str(sun_el), intensity="100000" if sun_el > 0 else "0")
    ET.SubElement(w, "Fog", visualRange=str(ENV_MAP["visibility"][s["visibility"]]))
    ET.SubElement(w, "Precipitation", precipitationType=ptype, precipitationIntensity=str(pint))
    ET.SubElement(env, "RoadCondition", frictionScaleFactor="1.0")
    return ga


def build(scenario, sid, predicates, clauses, model="Regulation", out_dir=None):
    tree = ET.parse(TEMPLATE)
    root = tree.getroot()
    v = float(scenario["speed_kmh"]) / 3.6
    params = {p.get("name"): p for p in root.iter("ParameterDeclaration")}
    params["EgoSpeed"].set("value", f"{v:.4f}")
    params["TargetSpeed"].set("value", f"{0.75 * v:.4f}")  # template ratio 15/20 kept
    for prop in root.iter("Property"):
        if prop.get("name") == "model":
            prop.set("value", model)
        if prop.get("name") == "logLevel":
            prop.set("value", "0")
    init_actions = root.find("./Storyboard/Init/Actions")
    init_actions.insert(0, environment_action(scenario))
    # template paths are relative to esmini/resources/xosc; make them absolute via ESMINI_HOME
    home = os.environ.get("ESMINI_HOME", "")
    if home:
        for el in root.iter():
            for attr in ("filepath", "path"):
                if el.get(attr, "").startswith("../"):
                    el.set(attr, os.path.join(home, "resources", el.get(attr)[3:]))
    fh = root.find("FileHeader")
    fh.set("description", f"{sid}: " + ", ".join(f"{k}={scenario[k]}" for k in scenario))
    fh.set("author", "saai-quantum-thesis generate_xosc.py")
    out_dir = out_dir or os.path.join(HERE, "generated")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{sid}_{model}.xosc")
    ET.indent(tree)
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    meta = {"scenario_id": sid, "model": model, "odd": scenario, "predicates": predicates,
            "traces_to": clauses, "xosc": os.path.basename(path)}
    with open(re.sub(r"\.xosc$", ".json", path), "w") as f:
        json.dump(meta, f, indent=1)
    return path
