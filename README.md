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
| `phaseB_qubo_scenario_selection/` | QUBO formulation of scenario selection over an ODD space built from EU 2022/1426 Annex II 3.1.4.1 and UN R157; solvers: random, greedy, GA (pymoo), simulated annealing (neal), QAOA (statevector simulator, cross-checked against Qiskit), exhaustive optimum; Wilcoxon + Vargha–Delaney A12 statistics | n=12, 16 complete; n=20 finishing |
| `phaseA_requirement_extraction/` | Requirement → ODD predicate: rule baseline, TF-IDF + LR baseline, SciBERT fine-tuning (Colab), evaluation, random and held-out-source splits | Code ready; accuracy needs gold labels |
| `phaseC_simulation/` | OpenSCENARIO generation from selected ODD scenarios; headless esmini execution with the UN R157 ALKS controller; collision, gap, TTC, PASS/FAIL, traced to clauses | Chain working; 48 real runs |
| `corpus/` | Extraction of 370 statements from EU 2022/1426; inter-annotator agreement tool (Cohen's kappa) | R157 extraction next |

## Current Phase B results (median pairwise coverage, k = 5)
| Method | n=12 | n=16 |
|---|---|---|
| Random | 55.7% | 50.0% |
| Greedy | 64.5% | 58.1% |
| GA | 63.6% | 58.0% |
| Simulated annealing | 64.4% | 57.4% |
| QAOA (simulated, p=2) | 63.2% | 56.9% |
| Exhaustive QUBO optimum | 63.6% | 58.0% |

Full per-instance data: `phaseB_qubo_scenario_selection/results/runs.csv`. All runs are seeded and reproducible.
