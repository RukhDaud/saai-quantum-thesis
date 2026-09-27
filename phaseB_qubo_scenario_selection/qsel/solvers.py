import time, numpy as np
from scipy.optimize import minimize
from .qubo import energy, all_energies

def bits_to_sel(x):
    return [i for i, b in enumerate(x) if b]

def int_to_bits(v, n):
    return [(int(v) >> i) & 1 for i in range(n)]

# ---------------- classical baselines ----------------
def random_selection(inst, rng):
    return sorted(rng.choice(inst.n, size=inst.k, replace=False).tolist())

def greedy_coverage(inst, rng=None):
    """Classical combinatorial-coverage greedy: add the scenario that covers most new
    2-way interactions (ties broken by new predicates, then index)."""
    sel, covered, preds = [], set(), set()
    for _ in range(inst.k):
        best = None
        for i in range(inst.n):
            if i in sel: continue
            gain = (len(inst.pairs[i] - covered), len(set(np.where(inst.pred[i])[0]) - preds), -i)
            if best is None or gain > best[0]: best = (gain, i)
        i = best[1]; sel.append(i); covered |= inst.pairs[i]; preds |= set(np.where(inst.pred[i])[0])
    return sorted(sel)

def exhaustive(Q, const, E_all=None):
    E = all_energies(Q, const) if E_all is None else E_all
    v = int(np.argmin(E)); return int_to_bits(v, Q.shape[0]), float(E[v])

def simulated_annealing(Q, const, seed, num_reads=100):
    import dimod, neal
    n = Q.shape[0]
    qd = {(i, j): Q[i, j] for i in range(n) for j in range(i, n) if Q[i, j] != 0}
    bqm = dimod.BinaryQuadraticModel.from_qubo(qd, offset=const)
    res = neal.SimulatedAnnealingSampler().sample(bqm, num_reads=num_reads, seed=int(seed))
    best = res.first
    return [int(best.sample[i]) for i in range(n)], float(best.energy)

def genetic_algorithm(Q, const, seed, pop=50, gens=100):
    from pymoo.algorithms.soo.nonconvex.ga import GA
    from pymoo.core.problem import Problem
    from pymoo.operators.sampling.rnd import BinaryRandomSampling
    from pymoo.operators.crossover.pntx import TwoPointCrossover
    from pymoo.operators.mutation.bitflip import BitflipMutation
    from pymoo.optimize import minimize as pmin
    n = Q.shape[0]
    class P(Problem):
        def __init__(s): super().__init__(n_var=n, n_obj=1, xl=0, xu=1, vtype=bool)
        def _evaluate(s, X, out, *a, **kw):
            Xf = X.astype(float); out['F'] = np.einsum('bi,ij,bj->b', Xf, Q, Xf) + const
    alg = GA(pop_size=pop, sampling=BinaryRandomSampling(), crossover=TwoPointCrossover(),
             mutation=BitflipMutation(), eliminate_duplicates=True)
    r = pmin(P(), alg, ('n_gen', gens), seed=int(seed), verbose=False)
    x = [int(b) for b in np.atleast_2d(r.X)[0]]
    return x, energy(Q, x, const)

# ---------------- QAOA (statevector simulation) ----------------
def qaoa_state(cost, n, gammas, betas):
    """Standard QAOA: |+>^n, then p layers of exp(-i*gamma*C) and exp(-i*beta*sum X).
    Bit q of the basis index corresponds to variable x_q."""
    psi = np.full(2 ** n, 1 / np.sqrt(2 ** n), dtype=np.complex128)
    for g, b in zip(gammas, betas):
        psi = psi * np.exp(-1j * g * cost)
        c, s = np.cos(b), -1j * np.sin(b)
        for q in range(n):
            v = psi.reshape(-1, 2, 2 ** q)
            a0, a1 = v[:, 0, :].copy(), v[:, 1, :].copy()
            v[:, 0, :] = c * a0 + s * a1
            v[:, 1, :] = s * a0 + c * a1
    return psi

def qaoa(Q, const, seed, p=2, restarts=3, maxiter=150, shots=1024, E_all=None):
    n = Q.shape[0]; rng = np.random.default_rng(seed)
    E = all_energies(Q, const) if E_all is None else E_all
    lo, hi = E.min(), E.max(); cost = (E - lo) / (hi - lo)          # normalised cost for stable angles
    f = lambda th: float(np.abs(qaoa_state(cost, n, th[:p], th[p:])) ** 2 @ cost)
    best = None; nfev = 0
    for _ in range(restarts):
        th0 = np.concatenate([rng.uniform(0, 2 * np.pi, p), rng.uniform(0, np.pi, p)])
        r = minimize(f, th0, method='COBYLA', options={'maxiter': maxiter}); nfev += r.nfev
        if best is None or r.fun < best.fun: best = r
    probs = np.abs(qaoa_state(cost, n, best.x[:p], best.x[p:])) ** 2
    probs = probs / probs.sum()
    samples = rng.choice(2 ** n, size=shots, p=probs)
    v = int(samples[np.argmin(E[samples])])
    opt = int(np.argmin(E))
    return int_to_bits(v, n), float(E[v]), {'p_opt': float(probs[opt]), 'exp_cost_norm': float(best.fun), 'nfev': nfev}
