"""QUBO for coverage- and traceability-aware scenario selection.

E(x) = - A * sum_i r_i x_i                (rarity-weighted 2-way interactions: coverage proxy)
       + B * sum_{i<j} o_ij x_i x_j       (shared 2-way interactions: redundancy penalty)
       - T * sum_i q_i x_i                (rarity-weighted predicates exercised: traceability)
       + Tp* sum_{i<j} s_ij x_i x_j       (shared predicates: predicate redundancy)
       + C * (sum_i x_i - k)^2            (cardinality)
All terms are expressed as an upper-triangular matrix Q with E(x) = x^T Q x + const.
"""
import numpy as np
from collections import Counter

def build_qubo(inst, A=1.0, B=1.0, T=1.0, Tp=0.5, C=None):
    n, k = inst.n, inst.k
    freq = Counter(p for ps in inst.pairs for p in ps)
    r = np.array([sum(1.0 / freq[p] for p in ps) for ps in inst.pairs])
    o = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            o[i, j] = sum(1.0 / freq[p] for p in inst.pairs[i] & inst.pairs[j])
    pf = inst.pred.sum(axis=0).astype(float); pf[pf == 0] = 1
    q = (inst.pred / pf).sum(axis=1)
    s = np.triu((inst.pred / pf) @ inst.pred.T, 1)
    lin = -A * r - T * q
    quad = B * o + Tp * s
    if C is None:
        C = 1.0 + np.abs(lin).max() + quad.sum(axis=1).max()   # large enough to enforce |S| = k
    Q = np.triu(quad, 1).copy()
    Q[np.diag_indices(n)] = lin + C * (1 - 2 * k)
    Q[np.triu_indices(n, 1)] += 2 * C
    const = C * k * k
    return Q, const

def energy(Q, x, const=0.0):
    x = np.asarray(x, dtype=float)
    return float(x @ Q @ x) + const

def all_energies(Q, const=0.0):
    """Vectorised energies of all 2^n bitstrings (bit i of the integer = x_i)."""
    n = Q.shape[0]
    idx = np.arange(2 ** n, dtype=np.int64)
    X = ((idx[:, None] >> np.arange(n)) & 1).astype(np.float32)
    e = np.einsum('bi,ij,bj->b', X, Q.astype(np.float32), X, optimize=True)
    return e.astype(np.float64) + const
