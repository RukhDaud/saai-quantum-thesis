"""Scaling beyond simulable/embeddable size: sub-QUBO decomposition and an exact reference.

decomposed()          - iterative sub-QUBO decomposition (in the spirit of qbsolv and of the
                        decomposition used by BootQA / IGDec-QAOA): start from a feasible
                        selection, repeatedly free m variables (the current selection plus the
                        most promising unselected candidates), hold the rest fixed, solve the
                        m-variable sub-QUBO exactly or with QAOA, keep the result if the full
                        energy improves.
exact_max_coverage()  - the true coverage optimum as an integer linear programme
                        (max sum_e y_e  s.t.  y_e <= sum_{i covers e} x_i,  sum_i x_i = k),
                        solved with HiGHS via scipy.optimize.milp. Used only as a reference.
"""
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .qubo import all_energies, energy


def reduced_qubo(Q, x, free):
    """Sub-QUBO over `free` with all other variables fixed at x. Returns (Qs, offset)."""
    free = np.asarray(free)
    fixed = np.setdiff1d(np.arange(Q.shape[0]), free)
    xs = np.asarray(x, float)
    Qf = Q[np.ix_(free, free)].copy()
    Qsym = np.triu(Q) + np.triu(Q, 1).T  # full symmetric coupling view
    lin_add = Qsym[np.ix_(free, fixed)] @ xs[fixed] if len(fixed) else np.zeros(len(free))
    Qf[np.diag_indices(len(free))] += lin_add
    off = float(xs[fixed] @ Q[np.ix_(fixed, fixed)] @ xs[fixed]) if len(fixed) else 0.0
    return np.triu(Qf), off


def _solve_sub(Qs, method, seed):
    m = Qs.shape[0]
    if method == "exact":
        E = all_energies(Qs)
        v = int(np.argmin(E))
        return np.array([(v >> i) & 1 for i in range(m)])
    if method == "qaoa":
        from .solvers import qaoa
        x, _, _ = qaoa(Qs, 0.0, seed, p=2, restarts=2, maxiter=100)
        return np.array(x)
    raise ValueError(method)


def decomposed(Q, const, x0, m=12, method="exact", seed=0, max_iter=30, patience=4):
    rng = np.random.default_rng(seed)
    n = Q.shape[0]
    x = np.array(x0, int)
    best_e = energy(Q, x, const)
    Qsym = np.triu(Q) + np.triu(Q, 1).T
    stale, it = 0, 0
    while it < max_iter and stale < patience:
        it += 1
        sel = np.where(x == 1)[0]
        un = np.where(x == 0)[0]
        # marginal energy of adding each unselected candidate to the current selection
        gain = np.diag(Q)[un] + Qsym[np.ix_(un, sel)].sum(axis=1)
        n_new = m - len(sel)
        top = un[np.argsort(gain)[: max(1, n_new // 2)]]
        rest = np.setdiff1d(un, top)
        extra = rng.choice(rest, size=min(len(rest), n_new - len(top)), replace=False) if len(rest) else []
        free = np.sort(np.concatenate([sel, top, extra]).astype(int))
        Qs, _ = reduced_qubo(Q, x, free)
        xs = _solve_sub(Qs, method, int(seed) + it)
        cand = x.copy()
        cand[free] = xs
        e = energy(Q, cand, const)
        if e < best_e - 1e-9:
            x, best_e, stale = cand, e, 0
        else:
            stale += 1
    return x.tolist(), best_e, it


def exact_max_coverage(inst, time_limit=60):
    """True optimum of pairwise coverage with |S| = k (reference only)."""
    elems = sorted(inst.pool_pairs)
    eidx = {e: j for j, e in enumerate(elems)}
    n, E = inst.n, len(elems)
    # variables: x_0..x_{n-1}, y_0..y_{E-1}
    c = np.concatenate([np.zeros(n), -np.ones(E)])
    A = lil_matrix((E + 1, n + E))
    for i, ps in enumerate(inst.pairs):
        for p in ps:
            A[eidx[p], i] = -1.0
    for j in range(E):
        A[j, n + j] = 1.0
    A[E, :n] = 1.0
    lb = np.concatenate([np.full(E, -np.inf), [inst.k]])
    ub = np.concatenate([np.zeros(E), [inst.k]])
    res = milp(c, constraints=LinearConstraint(A.tocsr(), lb, ub), integrality=np.ones(n + E),
               bounds=Bounds(0, 1), options={"time_limit": time_limit})
    sel = [i for i in range(n) if res.x[i] > 0.5]
    return sel, res.status == 0
