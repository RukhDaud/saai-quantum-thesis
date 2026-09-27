# saai-quantum-thesis — code, experiments and simulations

Traceable ODD-boundary test-scenario generation from safety requirements, with QUBO / quantum optimisation.
PhD research, COMSATS University Islamabad.

```
Safety requirement  ──►  Phase A: extract ODD boundary predicate  ──►  Phase B: select test scenarios (QUBO)
(EU 2022/1426, R157)     (dimension, variable, operator, threshold)     (greedy, GA, SA, QAOA, exhaustive)
```

## Quick start
```bash
pip install -r requirements.txt
python -m pytest -q phaseB_qubo_scenario_selection/tests corpus/tests phaseA_requirement_extraction/tests   # 7 tests

# Phase B: one instance, every solver, with traceability printout (≈2 s)
cd phaseB_qubo_scenario_selection
python run_single_instance.py
cd ..

# Phase B: small experiment (≈5 s)
cd phaseB_qubo_scenario_selection
python run_experiment.py --sizes 12 --instances 3 --out results/demo.csv
python analyse.py results/demo.csv

# Phase B: full experiment (n = 12, 16, 20; 30 instances each; QAOA at n=20 ≈ 3 min per instance)
python run_experiment.py --sizes 12 16 20 --instances 30 --out results/runs.csv
python analyse.py results/runs.csv
```

## Folders
| Folder | What it runs | Status |
|---|---|---|
| `corpus/` | EU 2022/1426 (370 statements) and UN R157 (71 statements, verified) corpora; formal ODD condition library (29 conditions); traceability matrix | Complete |
| `phaseB_qubo_scenario_selection/` | QUBO scenario selection over the regulation-derived ODD space: first (v1) and coverage-aligned (v2) formulations; random, greedy, GA, simulated annealing, QAOA (statevector simulator, checked against Qiskit), exhaustive optimum; alignment study; change-aware re-selection (RQ4); decomposition + ILP reference for n = 50-200 | v1 complete; v2 n=12/16 complete, n=20 running; RQ4 running; large-scale next |
| `phaseC_simulation/` | OpenSCENARIO generation from selected scenarios; headless esmini with the UN R157 ALKS controller; collision, gap, TTC, PASS/FAIL traced to clauses | Chain working; 48 runs; degradation model and fault injection next |
| `phaseA_requirement_extraction/` | Optional automated extraction (rule, TF-IDF, SciBERT) - supporting tool, no accuracy claim | Parked |
| `figures/` | Editable thesis figures (.drawio, .svg, .png) and their generators | Figures 2.1, 3.1, 3.2 |

## Key results so far (all runs seeded and reproducible)

**1. Alignment of the QUBO with true coverage** (`alignment_study.py`, all C(n,5) selections enumerated, 30 instances per size)

| | v1 n=12 / 16 / 20 | v2 (coverage-aligned) n=12 / 16 / 20 |
|---|---|---|
| QUBO optimum = true coverage optimum | 26.7% / 20.0% / 10.0% | **100% / 100% / 100%** |

**2. Solver comparison, median pairwise coverage (k = 5, 30 instances per size)**

| Method | v1 n=12 | v1 n=16 | v1 n=20 | v2 n=12 | v2 n=16 |
|---|---|---|---|---|---|
| Random | 55.7% | 50.0% | 47.1% | 55.7% | 50.0% |
| Greedy | 64.5% | 58.1% | 54.5% | 64.5% | 58.1% |
| GA | 63.6% | 58.0% | 53.9% | 65.3% | 59.8% |
| Simulated annealing | 64.4% | 57.4% | 53.1% | 64.7% | 58.9% |
| QAOA (p=2, simulator) | 63.2% | 56.9% | 52.3% | 64.7% | 59.0% |
| Exhaustive QUBO optimum | 63.6% | 58.0% | 53.9% | 65.3% | 59.9% |

QAOA vs greedy (Wilcoxon): v1 significantly worse (p = 0.029, 0.0005, < 0.0001); v2 significantly better (p = 0.010 at n=12, 0.015 at n=16).
Data: `results/runs_full.csv` (v1), `results/runs_v2_n12_16.csv` (v2); statistics in `results/analysis_*.txt`.

**3. Change-aware re-selection (RQ4)** - `change_experiment.py`: when a clause changes, trace links identify affected
scenarios; unmet obligations are enforced with exact one-hot penalties; a stability term keeps still-valid tests; a
12-variable sub-QUBO is solved. Full run (6 illustrative clause changes x 30 instances x n = 16, 20) in progress:
`results/change_rq4.csv`.
