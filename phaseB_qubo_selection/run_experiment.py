"""Phase B experiment: QUBO scenario selection at ODD boundaries on simulators.
Usage: python run_experiment.py --sizes 12 16 20 --instances 30 --k 5 --out results/runs.csv
Every instance uses its own seed; all solvers see the same instance and QUBO."""
import argparse, csv, time, json, platform, numpy as np
from qsel.instance import sample_pool, Instance
from qsel.qubo import build_qubo, all_energies, energy
from qsel import solvers as S

def run_one(n, k, seed, writer, qaoa_p, qaoa_restarts):
    rng = np.random.default_rng(seed)
    inst = Instance(sample_pool(n, rng), k)
    Q, const = build_qubo(inst)
    t = time.perf_counter(); E = all_energies(Q, const); t_enum = time.perf_counter() - t
    x_opt, e_opt = S.exhaustive(Q, const, E)
    methods = {
        'random':     lambda: (S.random_selection(inst, np.random.default_rng(seed + 1)), None),
        'greedy':     lambda: (S.greedy_coverage(inst), None),
        'exhaustive': lambda: (S.bits_to_sel(x_opt), e_opt),
        'sa':         lambda: (lambda r: (S.bits_to_sel(r[0]), r[1]))(S.simulated_annealing(Q, const, seed)),
        'ga':         lambda: (lambda r: (S.bits_to_sel(r[0]), r[1]))(S.genetic_algorithm(Q, const, seed)),
        'qaoa':       lambda: (lambda r: (S.bits_to_sel(r[0]), r[1], r[2]))(S.qaoa(Q, const, seed, p=qaoa_p, restarts=qaoa_restarts, E_all=E)),
    }
    for name, fn in methods.items():
        t = time.perf_counter(); out = fn(); dt = time.perf_counter() - t
        if name == 'exhaustive': dt += t_enum
        sel = out[0]; x = [1 if i in sel else 0 for i in range(n)]
        row = {'n': n, 'k': k, 'seed': seed, 'method': name, 'seconds': round(dt, 4),
               'qubo_energy': energy(Q, x, const), 'qubo_opt': e_opt,
               'energy_gap': energy(Q, x, const) - e_opt, **inst.evaluate(sel),
               'selected': ' '.join(map(str, sel))}
        if name == 'qaoa': row.update({'qaoa_p_opt': out[2]['p_opt'], 'qaoa_nfev': out[2]['nfev']})
        writer.writerow(row)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sizes', type=int, nargs='+', default=[12, 16, 20])
    ap.add_argument('--instances', type=int, default=30)
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--qaoa_p', type=int, default=2)
    ap.add_argument('--qaoa_restarts', type=int, default=3)
    ap.add_argument('--base_seed', type=int, default=20260927)
    ap.add_argument('--out', default='results/runs.csv')
    a = ap.parse_args()
    fields = ['n','k','seed','method','seconds','qubo_energy','qubo_opt','energy_gap','size','size_ok',
              'pairwise_cov','predicate_cov','boundary_cov','traced_frac','qaoa_p_opt','qaoa_nfev','selected']
    with open(a.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for n in a.sizes:
            for i in range(a.instances):
                run_one(n, a.k, a.base_seed + 1000 * n + i, w, a.qaoa_p, a.qaoa_restarts); f.flush()
                print(f'n={n} instance {i+1}/{a.instances} done', flush=True)
    json.dump({'args': vars(a), 'python': platform.python_version(), 'machine': platform.machine()},
              open(a.out.replace('.csv', '_meta.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
