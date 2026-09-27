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
| `phaseB_qubo_scenario_selection/` | QUBO scenario selection over the regulation-derived ODD space: first (v1) and coverage-aligned (v2) formulations; random, greedy, GA, simulated annealing, QAOA (statevector simulator, checked against Qiskit), exhaustive optimum; alignment study; change-aware re-selection (RQ4); decomposition + ILP reference for n = 50-200 | Complete: v1 and v2 (540 runs each), alignment study, RQ4 (2,160 runs), large-scale n = 50-200 |
| `phaseC_simulation/` | OpenSCENARIO generation from selected scenarios; headless esmini with the UN R157 ALKS controller; collision, gap, TTC, PASS/FAIL traced to clauses | Chain working; 48 runs; degradation model and fault injection next |
| `phaseA_requirement_extraction/` | Optional automated extraction (rule, TF-IDF, SciBERT) - supporting tool, no accuracy claim | Parked |
| `figures/` | Editable thesis figures (.drawio, .svg, .png) and their generators | Figures 2.1, 3.1, 3.2 |

## Key results so far (all runs seeded and reproducible)

**1. Alignment of the QUBO with true coverage** (`alignment_study.py`, all C(n,5) selections enumerated, 30 instances per size)

| | v1 n=12 / 16 / 20 | v2 (coverage-aligned) n=12 / 16 / 20 |
|---|---|---|
| QUBO optimum = true coverage optimum | 26.7% / 20.0% / 10.0% | **100% / 100% / 100%** |

**2. Solver comparison, median pairwise coverage (k = 5, 30 instances per size)**

| Method | v1 n=12 | v1 n=16 | v1 n=20 | v2 n=12 | v2 n=16 | v2 n=20 |
|---|---|---|---|---|---|---|
| Random | 55.7% | 50.0% | 47.1% | 55.7% | 50.0% | 47.1% |
| Greedy | 64.5% | 58.1% | 54.5% | 64.5% | 58.1% | 54.5% |
| GA | 63.6% | 58.0% | 53.9% | 65.3% | 59.8% | 55.8% |
| Simulated annealing | 64.4% | 57.4% | 53.1% | 64.7% | 58.9% | 54.2% |
| QAOA (p=2, simulator) | 63.2% | 56.9% | 52.3% | 64.7% | 59.0% | 55.0% |
| Exhaustive QUBO optimum | 63.6% | 58.0% | 53.9% | 65.3% | 59.9% | 55.8% |

QAOA vs greedy (Wilcoxon): v1 significantly worse at every size (p = 0.029, 0.0005, < 0.0001); v2 significantly better
at n=12 (p = 0.010) and n=16 (p = 0.015), no significant difference at n=20 (p = 0.25), where QAOA (p=2) reaches the
QUBO optimum on only 3.3% of instances. The exact v2 optimum beats greedy at every size (p < 0.001).
Data: `results/runs_full.csv` (v1), `results/runs_v2_full.csv` (v2); statistics in `results/analysis_*.txt`.

**3. Scaling to 50-200 candidates** (`large_scale.py`, v2 QUBO, reference = ILP optimum within 60 s)

| Method | n=50 | n=100 | n=200 | vs greedy (W/T/L; p) n=50 / 100 / 200 |
|---|---|---|---|---|
| Greedy | 48.7% | 48.7% | 48.7% | reference |
| Decomposition, exact 12-variable sub-QUBOs | 49.3% | 48.7% | 49.3% | 17/13/0, p<0.001 / 10/20/0, p=0.004 / 8/22/0, p=0.009 |
| Decomposition, QAOA 10-qubit sub-QUBOs | 49.0% | 48.7% | 48.7% | 10/20/0, p=0.005 / 11/19/0, p=0.003 / 3/27/0, p=0.083 |
| Genetic algorithm (full QUBO) | 49.3% | 49.3% | 49.3% | better at all sizes (p <= 0.012) |
| Simulated annealing (full QUBO) | 47.5% | 47.3% | 46.7% | worse at all sizes (p < 0.001) |

**4. Change-aware re-selection (RQ4)** (`change_experiment.py`, 6 illustrative clause changes x 30 instances x n = 16, 20)

| | Keep old | Full re-selection | Change-aware (exact, 12 vars) | Change-aware (QAOA, 12 qubits) |
|---|---|---|---|---|
| All clause obligations exercised | 92-94% | 98-99% | **100%** | 97-98% |
| Coverage vs best feasible | - | 99.99-100% | 99.95% | 99.0% |
| Tests replaced (mean) | 0 | 0.76-0.77 | **0.06-0.10** (p < 0.001) | 0.68-0.79 |

Summary: `results/change_rq4_summary.xlsx`, `results/analysis_change_rq4.txt`.
