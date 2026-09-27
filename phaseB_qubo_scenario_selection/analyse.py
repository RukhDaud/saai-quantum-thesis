"""Summarise Phase B runs: medians/IQR per method and size, and paired Wilcoxon
signed-rank tests with Vargha-Delaney A12 effect sizes against the greedy baseline."""
import sys, numpy as np, pandas as pd
from scipy.stats import wilcoxon
d = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else 'results/runs.csv')
metrics = ['pairwise_cov', 'boundary_cov', 'predicate_cov', 'traced_frac', 'size_ok', 'energy_gap', 'seconds']
order = ['random', 'greedy', 'ga', 'sa', 'qaoa', 'exhaustive']

def a12(x, y):
    x, y = np.asarray(x), np.asarray(y)
    gt = (x[:, None] > y[None, :]).sum(); eq = (x[:, None] == y[None, :]).sum()
    return (gt + 0.5 * eq) / (len(x) * len(y))

rows = []
for n, g in d.groupby('n'):
    for m in order:
        s = g[g.method == m]
        if s.empty: continue
        r = {'n': n, 'method': m, 'instances': len(s)}
        for k in metrics:
            r[f'{k}_median'] = s[k].median()
            r[f'{k}_q1'] = s[k].quantile(.25); r[f'{k}_q3'] = s[k].quantile(.75)
        r['energy_gap_zero_share'] = (s['energy_gap'].abs() < 1e-3).mean()
        rows.append(r)
summary = pd.DataFrame(rows)

tests = []
for n, g in d.groupby('n'):
    base = g[g.method == 'greedy'].set_index('seed')
    for m in ['random', 'ga', 'sa', 'qaoa', 'exhaustive']:
        s = g[g.method == m].set_index('seed').loc[base.index]
        for k in ['pairwise_cov', 'boundary_cov']:
            diff = s[k] - base[k]
            p = wilcoxon(s[k], base[k]).pvalue if (diff != 0).any() else 1.0
            tests.append({'n': n, 'method': m, 'metric': k, 'median_method': s[k].median(),
                          'median_greedy': base[k].median(), 'wilcoxon_p': p, 'A12_vs_greedy': a12(s[k], base[k]),
                          'wins': int((diff > 0).sum()), 'ties': int((diff == 0).sum()), 'losses': int((diff < 0).sum())})
tests = pd.DataFrame(tests)
with pd.ExcelWriter('results/phaseB_summary.xlsx') as w:
    summary.to_excel(w, sheet_name='Summary', index=False)
    tests.to_excel(w, sheet_name='Tests_vs_greedy', index=False)
    d.to_excel(w, sheet_name='All_runs', index=False)
pd.set_option('display.width', 200)
print(summary[['n','method','instances','pairwise_cov_median','boundary_cov_median','predicate_cov_median','traced_frac_median','size_ok_median','energy_gap_zero_share','seconds_median']].round(4).to_string(index=False))
print(); print(tests.round(4).to_string(index=False))
