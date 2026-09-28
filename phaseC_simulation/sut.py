"""System under test (SUT), environment effects and planted faults (mutants).

Environment effects (applied to every variant - they are physics, not behaviour):
  * tyre-road friction limits the achievable deceleration to mu * g
      dry  mu = 0.83  measured mean, dry asphalt with ABS (Lorencic 2023, Sustainability 15:6945)
      rain mu = 0.525 midpoint of 0.40-0.65, smooth asphalt wet (ibid., Table 1)
      snow mu = 0.32  midpoint of 0.24-0.40, compacted snow and ice (ibid., Table 1)
  * reduced visibility limits the sensor range to the visual range of the fog level
      mist 150 m (weak fog), fog 50 m (thick fog) - categories of Kim et al. 2023 (Sensors 23:2972)
    (modelling assumption: the perception chain cannot detect beyond the visual range)

Reference SUT (correct behaviour), esmini ALKS ReferenceDriver model with:
  * braking planned with the deceleration the surface allows: min(default, mu*g)
    (UN R157 5.2.3.2: adapt speed to environmental conditions)
  * ego speed capped at 60 km/h (UN R157 5.2.3.1)

Mutants: each changes one behaviour of the reference SUT, as a real defect would.
"""
G = 9.81
MU = {"none": 0.83, "rain": 0.525, "snow": 0.32}
VIS_M = {"clear": None, "mist": 150.0, "fog": 50.0}
DEFAULTS = dict(driver_dec=0.774 * G, aeb_dec=0.85 * G, reaction=0.75, range_m=100.0)
MAX_KMH = 60.0  # UN R157 para 5.2.3.1

MUTANTS = {
    "M1_surface_unaware": "plans braking with dry-road deceleration regardless of the surface",
    "M2_aeb_unavailable": "emergency braking function unavailable",
    "M3_no_speed_cap": "does not limit its speed to 60 km/h (R157 5.2.3.1)",
    "M4_late_reaction": "reaction time 1.25 s instead of 0.75 s (perception latency)",
    "M5_weak_brakes": "service and emergency braking 30% weaker than specified",
    "M6_precip_range_loss": "sensor range halved in rain or snow (unmodelled precipitation effect)",
}
VARIANTS = ["reference"] + list(MUTANTS)


def configure(scenario, variant):
    """Controller properties and ego speed for one ODD scenario and one SUT variant."""
    mu = MU[scenario["precipitation"]]
    a_phys = mu * G
    rng = DEFAULTS["range_m"] if VIS_M[scenario["visibility"]] is None else min(DEFAULTS["range_m"], VIS_M[scenario["visibility"]])
    drv = min(DEFAULTS["driver_dec"], a_phys)
    aeb = min(DEFAULTS["aeb_dec"], a_phys)
    react = DEFAULTS["reaction"]
    aeb_ok = True
    kmh = min(float(scenario["speed_kmh"]), MAX_KMH)
    if variant == "M1_surface_unaware":
        drv, aeb = DEFAULTS["driver_dec"], DEFAULTS["aeb_dec"]
    elif variant == "M2_aeb_unavailable":
        aeb_ok = False
    elif variant == "M3_no_speed_cap":
        kmh = float(scenario["speed_kmh"])
    elif variant == "M4_late_reaction":
        react = 1.25
    elif variant == "M5_weak_brakes":
        drv, aeb = 0.7 * drv, 0.7 * aeb
    elif variant == "M6_precip_range_loss" and scenario["precipitation"] != "none":
        rng = rng / 2
    props = {"frictionLimit": round(a_phys, 4), "maxRange": rng, "reactionTime": react,
             "driverDeceleration": round(drv, 4), "aebDeceleration": round(aeb, 4),
             "aebAvailable": "true" if aeb_ok else "false"}
    return props, kmh
