"""Coverage-aligned QUBO (formulation v2).

Pairwise coverage of a selection S is |U_{i in S} P_i|, where P_i is the set of 2-way
ODD-level interactions of scenario i. By inclusion-exclusion,

    |U P_i| = sum_i |P_i| - sum_{i<j} |P_i & P_j| + sum_{i<j<l} |P_i & P_j & P_l| - ...

A QUBO can hold only the first two terms. v2 keeps them with unit weights (the metric
counts every interaction once, so no rarity weighting) and scales the pairwise term by
beta in (0, 1] to compensate for the dropped positive third-order term. The same
construction is applied to boundary-exercising levels with weight lam:

E(x) = - sum_i |P_i| x_i + beta * sum_{i<j} |P_i & P_j| x_i x_j
       - lam * ( sum_i |L_i| x_i - beta_L * sum_{i<j} |L_i & L_j| x_i x_j )
       + C * (sum_i x_i - k)^2

beta, beta_L and lam are tuned on training instances whose seeds are disjoint from the
evaluation instances (see tune_v2.py).
"""
import numpy as np


def coverage_terms(sets):
    n = len(sets)
    lin = np.array([len(s) for s in sets], float)
    quad = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            quad[i, j] = len(sets[i] & sets[j])
    return lin, quad


def boundary_sets(inst):
    from .odd_space import DIM_NAMES
    return [{(d, s[d]) for d in DIM_NAMES} & inst.pool_boundary for s in inst.pool]


def objective_terms(inst, beta=1.0, lam=0.0, beta_l=1.0):
    """Linear and upper-triangular quadratic terms of the objective (without the budget penalty)."""
    lp, qp = coverage_terms(inst.pairs)
    lb, qb = coverage_terms(boundary_sets(inst))
    lin = -lp - lam * lb
    quad = beta * qp + lam * beta_l * qb
    return lin, quad


def build_qubo_v2(inst, beta=1.0, lam=0.0, beta_l=1.0, C=None):
    n, k = inst.n, inst.k
    lin, quad = objective_terms(inst, beta, lam, beta_l)
    if C is None:
        C = 1.0 + np.abs(lin).max() + quad.sum(axis=1).max() + quad.sum(axis=0).max()
    Q = np.triu(quad, 1).copy()
    Q[np.diag_indices(n)] = lin + C * (1 - 2 * k)
    Q[np.triu_indices(n, 1)] += 2 * C
    return Q, C * k * k
