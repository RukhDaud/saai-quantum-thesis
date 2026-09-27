# Coverage-aligned QUBO (v2), scaling and change-aware re-selection

| Script | Purpose |
|---|---|
| `qsel/qubo_v2.py` | Coverage-aligned QUBO: -sum|P_i| x_i + sum|P_i & P_j| x_i x_j + C(sum x - k)^2 (standard inclusion-exclusion construction, Glover et al. 2019) |
| `alignment_study.py` | Enumerates all C(n,k) selections; tests whether each QUBO's optimum is the true coverage optimum |
| `run_experiment.py --qubo v2` | Same solver comparison as v1 on the same seeds |
| `qsel/decomp.py`, `large_scale.py` | Sub-QUBO decomposition (exact / QAOA sub-solver) and exact ILP reference for n = 50-200 |
| `qsel/change.py`, `change_experiment.py` | Change-aware re-selection (RQ4): impact set via trace links, one-hot obligation penalty R(1 - sum_{S_p} x)^2, stability reward -mu sum_{S_old} x, m-variable sub-QUBO |

```bash
python alignment_study.py --sizes 12 16 20 --instances 30 --out results/alignment_eval.csv
python run_experiment.py --qubo v2 --sizes 12 16 20 --instances 30 --out results/runs_v2.csv
python change_experiment.py --sizes 16 20 --instances 30 --out results/change_rq4.csv
python large_scale.py --sizes 50 100 200 --instances 30 --out results/large_v2.csv
```
The clause changes in `change_experiment.py` are illustrative edits (add a combined condition, tighten a
threshold, narrow or remove a condition), not actual amendments.
