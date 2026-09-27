import itertools, numpy as np
from .odd_space import DIMENSIONS, DIM_NAMES, PREDICATES

def sample_pool(n, rng):
    """n distinct concrete scenarios drawn uniformly from the full ODD grid."""
    grid = list(itertools.product(*DIMENSIONS.values()))
    idx = rng.choice(len(grid), size=n, replace=False)
    return [dict(zip(DIM_NAMES, grid[i])) for i in idx]

def pairs_of(s):
    """All 2-way (dimension=level, dimension=level) interactions in one scenario."""
    items = [(d, s[d]) for d in DIM_NAMES]
    return set(itertools.combinations(items, 2))

class Instance:
    def __init__(self, pool, k):
        self.pool, self.k, self.n = pool, k, len(pool)
        self.pairs = [pairs_of(s) for s in pool]
        self.pool_pairs = set().union(*self.pairs)
        self.pred = np.array([[1 if f(s) else 0 for (_, _, f) in PREDICATES] for s in pool])  # n x P
        self.pool_preds = set(np.where(self.pred.any(axis=0))[0])
        # boundary levels: (dimension, level) values that make at least one predicate true on their own
        self.boundary_levels = set()
        for d, levels in DIMENSIONS.items():
            for lv in levels:
                base = {dd: DIMENSIONS[dd][0] for dd in DIM_NAMES}; base[d] = lv
                if any(f(base) for (_, _, f) in PREDICATES): self.boundary_levels.add((d, lv))
        self.pool_boundary = {(d, s[d]) for s in pool for d in DIM_NAMES} & self.boundary_levels

    # ---- true evaluation metrics (independent of the QUBO) ----
    def pairwise_coverage(self, sel):
        cov = set().union(*[self.pairs[i] for i in sel]) if len(sel) else set()
        return len(cov) / len(self.pool_pairs)
    def predicate_coverage(self, sel):
        if not len(sel): return 0.0
        return len(set(np.where(self.pred[list(sel)].any(axis=0))[0])) / len(self.pool_preds)
    def traced_fraction(self, sel):
        if not len(sel): return 0.0
        return float((self.pred[list(sel)].sum(axis=1) > 0).mean())
    def boundary_coverage(self, sel):
        got = {(d, self.pool[i][d]) for i in sel for d in DIM_NAMES} & self.pool_boundary
        return len(got) / len(self.pool_boundary) if self.pool_boundary else 0.0
    def evaluate(self, sel):
        sel = sorted(set(int(i) for i in sel))
        return {'size': len(sel), 'size_ok': int(len(sel) == self.k),
                'pairwise_cov': self.pairwise_coverage(sel),
                'predicate_cov': self.predicate_coverage(sel),
                'boundary_cov': self.boundary_coverage(sel),
                'traced_frac': self.traced_fraction(sel)}
