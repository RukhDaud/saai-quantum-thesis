"""Longitudinal model of a UN R157 ALKS in the cut-in-and-brake scenario (ReqODD-Q, Phase C).

Why a dedicated model: with esmini's scripted ALKS controller most injected faults produce no
observable difference (see README). This model makes every behaviour that a fault can affect
explicit, and is cross-checked against esmini on the fault-free cases (crosscheck_esmini.py).

Scenario (same as esmini's alks_r157_cut_in_quick_brake): the ego vehicle drives in its lane at v_e;
a vehicle in the adjacent lane at 0.75 x the scenario speed cuts in over 3 s, its lane change
starting at t = 0 with a bumper-to-bumper gap g0; 2 s after the lane change starts (template value) it
brakes to standstill at its full braking performance on the current surface, mu g (UN R157 5.2.5.1:
"a leading vehicle which decelerates up to its full braking performance"). The cut-in vehicle becomes relevant to the ego when
it reaches the lane-intrusion reference point of UN R157 5.2.5.2 (near edge 0.3 m beyond the lane
marking), provided it is within sensor range.

Ego behaviour (reference system):
  * speed: min(scenario speed, 60 km/h)                               UN R157 5.2.3.1
  * surface adaptation: speed reduced so that the braking distance on the
    current surface equals that on dry asphalt, v <= v * sqrt(mu / mu_dry)  UN R157 5.2.3.2
  * visibility adaptation: speed such that reaction + braking distance fits
    within the sensor range                                                 UN R157 7.1.3
  * from the onset of the hazard (first instant the gap closes after detection), after the
    reaction time, braking ramps up over 0.6 s (as in esmini's reference driver) to
    min(0.774 g, mu g), holding until the relative speed is zero
  * emergency braking when TTC < 1.5 s, up to min(0.85 g, mu g)             (esmini AEB defaults)
Physical limit: deceleration never exceeds mu g (friction values in sut.py).
"""
import math

from sut import MU, VIS_M

G = 9.81
DT = 0.01
LEN = 5.04          # vehicle length (esmini car_white / car_red bounding box)
LC_T, BRAKE_DELAY = 3.0, 2.0
LANE_W, VEH_W = 3.07, 2.0        # esmini straight_500m lane width; vehicle width
# The cut-in becomes relevant when the intruding vehicle's near edge is 0.3 m beyond the lane marking
# (the TTC_LaneIntrusion reference point of UN R157 5.2.5.2). With a sinusoidal lane change of LC_T s
# between lane centres LANE_W apart, lateral progress is LANE_W/2 * (1 - cos(pi t / LC_T)).
T_INTRUSION = LC_T / math.pi * math.acos(1 - 2 * (LANE_W - (LANE_W / 2 - 0.3 + VEH_W / 2)) / LANE_W)
REF = dict(reaction=0.75, drv_dec=0.774 * G, aeb_dec=0.85 * G, aeb_ttc=1.5, range_m=100.0, ramp=0.6,
           speed_cap=60.0, surface_adapt=True, visibility_adapt=True, aeb=True, brake_scale=1.0,
           precip_range_factor=1.0)

MUTANTS = {
    "M1_surface_unaware": dict(surface_adapt=False),
    "M2_aeb_unavailable": dict(aeb=False),
    "M3_no_speed_cap": dict(speed_cap=None),
    "M4_late_reaction": dict(reaction=1.25),
    "M5_weak_brakes": dict(brake_scale=0.7),
    "M6_visibility_unaware": dict(visibility_adapt=False, precip_range_factor=0.5),
}
MUTANT_TEXT = {
    "M1_surface_unaware": "does not adapt speed to wet or snowy surfaces",
    "M2_aeb_unavailable": "emergency braking unavailable",
    "M3_no_speed_cap": "does not limit speed to 60 km/h",
    "M4_late_reaction": "reaction time 1.25 s instead of 0.75 s",
    "M5_weak_brakes": "service and emergency braking 30% weaker",
    "M6_visibility_unaware": "no speed reduction for reduced sensor range; range halved in rain/snow",
}


def params(variant):
    p = dict(REF)
    if variant != "reference":
        p.update(MUTANTS[variant])
    return p


def ego_speed(scen_kmh, mu, rng, p):
    v = scen_kmh / 3.6
    if p["speed_cap"] is not None:
        v = min(v, p["speed_cap"] / 3.6)
    a = min(p["drv_dec"], mu * G) * p["brake_scale"]
    if p["surface_adapt"]:
        v = min(v, v * math.sqrt(mu / MU["none"]))
    if p["visibility_adapt"]:
        tr = p["reaction"]
        v_vis = (-tr + math.sqrt(tr * tr + 2 * rng / a)) * a   # v*tr + v^2/(2a) = rng
        v = min(v, v_vis)
    return v


def simulate(scenario, variant, gap0, ratio=0.75, trace=False):
    """Returns dict(collision, min_gap_m, min_ttc_s, ego_kmh); with trace=True also the time series
    (t, gap, ego speed, target speed, ego deceleration), which does not change the result."""
    p = params(variant)
    mu = MU[scenario["precipitation"]]
    vis = VIS_M[scenario["visibility"]]
    rng = p["range_m"] if vis is None else min(p["range_m"], vis)
    if scenario["precipitation"] != "none":
        rng *= p["precip_range_factor"]
    ve = ego_speed(float(scenario["speed_kmh"]), mu, rng, p)
    vt = ratio * float(scenario["speed_kmh"]) / 3.6
    a_phys = mu * G
    a_srv = min(p["drv_dec"] * p["brake_scale"], a_phys)
    a_aeb = min(p["aeb_dec"] * p["brake_scale"], a_phys)
    xe, xt = 0.0, gap0 + LEN          # rear of target at gap0 ahead of ego front
    t, acc_e = 0.0, 0.0
    t_detect = None
    t_hazard = None
    min_gap, min_ttc = float("inf"), float("inf")
    ego_kmh = ve * 3.6
    tr = []
    while t < 40.0:
        gap = xt - xe - LEN
        # perception: relevant once intrusion has started and the target is within range
        if t_detect is None and t >= T_INTRUSION and gap <= rng:
            t_detect = t
        # target braking
        at = -a_phys if (t >= BRAKE_DELAY and vt > 0) else 0.0
        # hazard onset: first instant after detection at which the gap is closing
        if t_detect is not None and t_hazard is None and ve > vt:
            t_hazard = t
        # ego control: react after the reaction time, then ramp braking up over p["ramp"] seconds
        a_cmd = 0.0
        if t_hazard is not None and t >= t_hazard + p["reaction"] and ve > vt:
            ramp = min(1.0, (t - t_hazard - p["reaction"]) / p["ramp"])
            a_cmd = a_srv * ramp
        ttc = gap / (ve - vt) if ve > vt and gap > 0 else float("inf")
        if p["aeb"] and t_detect is not None and ttc < p["aeb_ttc"]:
            a_cmd = max(a_cmd, a_aeb)
        a_cmd = min(a_cmd, a_phys)
        # integrate
        ve = max(0.0, ve - a_cmd * DT)
        vt = max(0.0, vt + at * DT)
        xe += ve * DT
        xt += vt * DT
        t += DT
        gap = xt - xe - LEN
        if trace:
            tr.append((round(t, 2), gap, ve, vt, a_cmd))
        min_gap = min(min_gap, gap)
        if ve > vt:
            min_ttc = min(min_ttc, max(gap, 0) / (ve - vt))
        if gap <= 0:
            out = dict(collision=1, min_gap_m=round(gap, 3), min_ttc_s=0.0, ego_kmh=round(ego_kmh, 2))
            if trace:
                out["trace"] = tr
            return out
        if ve == 0.0 and vt == 0.0:
            break
    out = dict(collision=0, min_gap_m=round(min_gap, 3),
               min_ttc_s=round(min_ttc, 3) if min_ttc != float("inf") else None, ego_kmh=round(ego_kmh, 2))
    if trace:
        out["trace"] = tr
    return out
