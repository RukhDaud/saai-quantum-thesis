# Phase B: QUBO scenario selection at ODD boundaries (simulator experiments)

Reproducible code for the Phase B experiments of the thesis.

## Contents
- `qsel/odd_space.py` - ODD dimensions (EU 2022/1426 Annex II 3.1.4.1 conditions plus speed), discrete levels,
  and 8 requirement-derived boundary predicates traced to EU 2022/1426 corpus IDs and UN R157 paragraphs.
- `qsel/instance.py` - candidate scenario pools and the evaluation metrics (independent of the QUBO):
  2-way (pairwise) interaction coverage, boundary-level coverage, predicate coverage, traced fraction, cardinality.
- `qsel/qubo.py` - QUBO: rarity-weighted interaction coverage, redundancy penalty, predicate (traceability) reward,
  predicate redundancy, cardinality penalty.
- `qsel/solvers.py` - random, greedy coverage (classical combinatorial baseline), exhaustive QUBO optimum,
  simulated annealing (dwave-neal), genetic algorithm (pymoo), QAOA (statevector simulation, COBYLA).
- `run_experiment.py` - runs all solvers on the same instances; writes `results/runs.csv` and run metadata.
- `analyse.py` - medians/IQR, paired Wilcoxon signed-rank tests and Vargha-Delaney A12 against greedy.
- `tests/` - QAOA simulator validated against Qiskit Statevector (fidelity > 1 - 1e-9).

## Reproduce
    pip install numpy scipy pandas openpyxl dwave-neal dimod pymoo qiskit
    python tests/test_qaoa_vs_qiskit.py
    python run_experiment.py --sizes 12 16 20 --instances 30 --k 5 --out results/runs.csv
    python analyse.py results/runs.csv

Seeds: base seed 20260927; instance seed = base + 1000*n + i. All results are simulator results;
no physical quantum hardware is used in these runs.
