"""Change-aware re-selection (ReqODD-Q, RQ4).

When a regulation clause changes, the predicate derived from it changes. Change-aware
re-selection:

  1. impact analysis  - using the trace links (predicate -> source clause), finds the
     candidates whose predicate profile changed (impact set) and the clause obligations
     that the previous selection no longer meets (unmet predicates);
  2. obligation terms - adds, for every unmet predicate p with satisfying set S_p, the
     exact one-hot penalty R * (1 - sum_{i in S_p} x_i)^2, so that exactly one selected
     scenario exercises the changed clause;
  3. stability term   - adds -mu * sum_{i in S_old} x_i, rewarding tests that remain valid,
     so that the new selection replaces as few tests as necessary;
  4. reduced problem  - frees only the previous selection plus the most promising impacted
     candidates (at most m variables) and solves that sub-QUBO exactly or with QAOA.

The coverage part of the objective is the coverage-aligned QUBO (qubo_v2), whose optimum
equals the true pairwise-coverage optimum on all evaluation instances.
Baselines: keep the old selection; full re-solve of the n-variable QUBO (same objective and
obligation terms, no stability term, no variable reduction).
"""
import itertools

import numpy as np

from .qubo import all_energies
from .qubo_v2 import build_qubo_v2

# ---- change operators on the predicate list (id, source, test) ----


def modify(preds, pid, new_src, new_test):
    return [(p, new_src, new_test) if p == pid else (p, s, f) for p, s, f in preds]


def remove(preds, pid):
    return [(p, s, f) for p, s, f in preds if p != pid]


def add(preds, pid, src, test):
    return list(preds) + [(pid, src, test)]


# ---- impact analysis ----

def _profile(inst, allids):
    ids = [p for p, _, _ in inst.predicates]
    col = {p: j for j, p in enumerate(ids)}
    return np.array([[inst.pred[i, col[p]] if p in col else 0 for p in allids] for i in range(inst.n)])


def impact_set(inst_old, inst_new):
    """Candidates whose predicate truth values differ between the old and new predicate lists."""
    allids = sorted({p for p, _, _ in inst_old.predicates} | {p for p, _, _ in inst_new.predicates})
    changed = (_profile(inst_old, allids) != _profile(inst_new, allids)).any(axis=1)
    return set(np.where(changed)[0].tolist())


def obligations(inst):
    """Clause predicates that at least one candidate in the pool can exercise, with their sets."""
    out = {}
    for j, (p, _, _) in enumerate(inst.predicates):
        s = set(np.where(inst.pred[:, j])[0].tolist())
        if s:
            out[p] = s
    return out


def unmet(inst, sel):
    return {p: s for p, s in obligations(inst).items() if not (s & set(sel))}


def feasible(inst, sel):
    return len(unmet(inst, sel)) == 0


def best_feasible(inst):
    """Reference: maximum pairwise coverage over all size-k selections that exercise every
    exercisable clause predicate (exhaustive enumeration)."""
    obl = list(obligations(inst).values())
    best, arg = -1.0, None
    for sel in itertools.combinations(range(inst.n), inst.k):
        ss = set(sel)
        if all(o & ss for o in obl):
            c = inst.pairwise_coverage(sel)
            if c > best:
                best, arg = c, list(sel)
    return arg, best


# ---- QUBO with obligation and stability terms ----

def change_qubo(inst_new, old_sel, mu, R=None):
    Q, const = build_qubo_v2(inst_new)
    Q = Q.copy()
    R = R if R is not None else 2.0 * max(len(p) for p in inst_new.pairs)
    for p, S in unmet(inst_new, old_sel).items():
        S = sorted(S)
        for i in S:
            Q[i, i] += -R                      # R(1 - sum x)^2 = R - R sum x + 2R sum_{i<j} x_i x_j
        for a, b in itertools.combinations(S, 2):
            Q[min(a, b), max(a, b)] += 2 * R
        const += R
    for i in old_sel:
        Q[i, i] -= mu
    return Q, const


def _solve(Qs, method, seed):
    if method == "exact":
        v = int(np.argmin(all_energies(Qs)))
        return [(v >> i) & 1 for i in range(Qs.shape[0])]
    from .solvers import qaoa
    x, _, _ = qaoa(Qs, 0.0, seed, p=2, restarts=3)
    return x


def change_aware(inst_old, inst_new, old_sel, mu=1.0, m=12, method="exact", seed=0):
    imp = impact_set(inst_old, inst_new)
    Q, _ = change_qubo(inst_new, old_sel, mu)
    Qsym = np.triu(Q) + np.triu(Q, 1).T
    marg = lambda i: Q[i, i] + sum(Qsym[i, j] for j in old_sel)
    need = set().union(*unmet(inst_new, old_sel).values()) if unmet(inst_new, old_sel) else set()
    # priority: candidates that can meet an unmet obligation, then other impacted, then the rest
    pri = [sorted([i for i in need if i not in old_sel], key=marg),
           sorted([i for i in imp if i not in old_sel and i not in need], key=marg),
           sorted([i for i in range(inst_new.n) if i not in old_sel and i not in imp and i not in need], key=marg)]
    extra = []
    for group in pri:
        for i in group:
            if len(extra) < m - len(old_sel):
                extra.append(i)
    free = sorted(set(old_sel) | set(extra))
    xs = _solve(np.triu(Q[np.ix_(free, free)]), method, seed)   # all other variables fixed at 0
    sel = sorted(free[i] for i, b in enumerate(xs) if b)
    return sel, dict(impact=len(imp), unmet=len(unmet(inst_new, old_sel)), variables=len(free))


def full_resolve(inst_old, inst_new, old_sel, method="exact", seed=0):
    Q, const = change_qubo(inst_new, old_sel, mu=0.0)
    xs = _solve(np.triu(Q), method, seed)
    return [i for i, b in enumerate(xs) if b], dict(variables=inst_new.n)
