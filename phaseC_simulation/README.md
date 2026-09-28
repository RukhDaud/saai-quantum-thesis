# Phase C — executing ODD scenarios in a driving simulator (esmini)

Selected ODD scenarios (Phase B) → OpenSCENARIO 1.1 files → esmini (headless) → PASS/FAIL per scenario,
with every run traced back to its regulation clauses.

| File | Role |
|---|---|
| `generate_xosc.py` | Builds one `.xosc` per ODD scenario from esmini's UN R157 cut-in-and-brake test; sets speed, `EnvironmentAction` (time of day, sun, fog visual range, precipitation) and the ALKS controller model; writes a JSON side-car with ODD levels, predicates and regulation clauses |
| `run_sim.py` | Runs esmini headless (20 Hz), logs trajectories, computes collision, minimum gap and minimum TTC; verdict FAIL on collision |
| `templates/alks_r157_cut_in_quick_brake.xosc` | Base scenario from esmini (MPL-2.0, v3.8.2, commit 61b44a7) |
| `results/sim_check.csv` | First check: 24 ODD scenarios × 2 R157 controller models = 48 runs |

## Build esmini (Linux, no GPU needed)
```bash
git clone --depth 1 https://github.com/esmini/esmini && cd esmini && mkdir build && cd build
cmake .. -DUSE_OSG=OFF -DUSE_OSI=OFF -DUSE_SUMO=OFF -DUSE_IMPLOT=OFF -DUSE_GTEST=OFF -DCMAKE_BUILD_TYPE=Release
make -j4 esmini
export ESMINI_HOME=$(cd .. && pwd)
```
(On Windows, the prebuilt esmini release zip works the same way; set `ESMINI_HOME` to its folder.)

## First results (`results/sim_check.csv`, real esmini runs)
| Controller model | Speed | Runs | Collisions | Min gap (m) | Min TTC (s) |
|---|---|---|---|---|---|
| ReferenceDriver | 40 | 8 | 0 | 6.97 | 3.59 |
| ReferenceDriver | 60 | 8 | 0 | 5.71 | 3.57 |
| ReferenceDriver | 70 | 8 | 0 | 4.46 | 3.57 |
| Regulation | 40 | 8 | 0 | 3.13 | 2.07 |
| Regulation | 60 | 8 | 0 | 2.55 | 1.94 |
| Regulation | 70 | 8 | 0 | 1.01 | 0.73 |

Finding: esmini's ALKS_R157SM models react to speed but not to weather or lighting — the eight
weather/lighting combinations at each speed give identical trajectories. The environment is
set in the scenario but does not reach the controller. For weather to affect outcomes, an
explicit, sourced model of how each ODD condition degrades the vehicle (braking friction,
sensor range) must be added — the next step of this phase.

## Fault detection (mutation analysis) - first run
- `esmini_patch/reqoddq_alks.patch`: adds `frictionLimit`, `reactionTime`, `maxRange` properties to esmini's
  ALKS_R157SM controller (apply to esmini v3.8.2, then rebuild).
- `sut.py`: environment effects from published values (friction: Lorencic 2023, Sustainability 15:6945, dry 0.83
  measured, wet 0.40-0.65 and compacted snow/ice 0.24-0.40 from its Table 1, midpoints used; fog visual range:
  Kim et al. 2023, Sensors 23:2972, weak fog < 150 m, thick fog <= 50 m), reference SUT and 6 mutants.
- `fault_detection.py`: 27 simulation-relevant ODD combinations x 7 variants; cut-in gap 20 m (smallest safe gap for
  the reference SUT, dry, 60 km/h); kill = mutant collides where the reference does not.

Result (`results/fd_*.csv`): with esmini's ALKS ReferenceDriver as the SUT, only M3 (no 60 km/h cap) is killable;
M1, M4 and M6 produce no observable behavioural difference, M2 differs by < 0.1 m, M5 reduces the minimum gap
but causes no collision. The reference SUT itself collides in snow at 60 km/h. The scripted controller is too
simple for most injected faults to become observable - see thesis Chapter 6 for the design decision taken.

## Fault detection with the R157 longitudinal model (final design)
The esmini controller makes most faults unobservable, so fault detection uses `r157_model.py`, a documented
longitudinal model of the R157 cut-in-and-brake test (speed cap R157 5.2.3.1; surface and visibility speed adaptation
R157 5.2.3.2 / 7.1.3; perception at the R157 5.2.5.2 lane-intrusion point; reaction 0.75 s; 0.6 s braking ramp to
min(0.774 g, mu g); AEB at TTC < 1.5 s up to min(0.85 g, mu g); lead vehicle brakes at its full braking performance,
R157 5.2.5.1). Each logical ODD scenario is run as a fixed sweep of 20 concrete manoeuvres (gap 7.5-30 m, cut-in
speed 0.5 or 0.75 x scenario speed).

```bash
python fault_detection_model.py --crosscheck     # ESMINI_HOME needed for the cross-check
```

| Result | Value |
|---|---|
| Simulations | 27 logical scenarios x 20 manoeuvres x 7 variants = 3,780 |
| Reference collisions (excluded from kills) | 87 of 540 |
| Killable faults | 6 of 6 (logical scenarios killing each: M1 18, M2 12, M3 9, M4 21, M5 9, M6 2) |
| Agreement with esmini ReferenceDriver (fault-free) | 81.7% of verdicts, Cohen's kappa 0.43 |
| Mean mutation score, v2 selections n=12/16/20 | greedy 0.87/0.89/0.86; QAOA 0.88/0.88/0.86; exact QUBO 0.88/0.89/0.88; random 0.83/0.79/0.85 |
| Best achievable with 5 scenarios | 0.92/0.96/0.95 |
| Spearman(pairwise coverage, mutation score) | 0.18 / 0.07 / -0.02 (v2) |

Files: `results/fdm_*.csv`, `results/fdm_meta.json`, `results/fdm_upper_bound.csv`.
