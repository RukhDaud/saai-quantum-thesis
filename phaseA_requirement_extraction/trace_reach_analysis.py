"""Trace-reach analysis from regulatory clauses to boundary predicates and scenarios.

Computes, from the condition library, the traceability matrix and the boundary
predicates of the scenario space:
  1. forward reach: for every source statement, the predicates and scenarios it reaches;
  2. backward reach: for every scenario, the predicates, conditions, statements and
     regulations to which it traces;
  3. clause anchoring: how many scenarios trace to a clause through a level that the
     clause itself states (rather than a level decided in the test design);
  4. hub statements that serve several conditions.
Writes results/trace_reach.txt and results/trace_reach_per_statement.csv.
"""
import itertools, os, re, sys
from collections import Counter
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'phaseB_qubo_scenario_selection'))
from qsel.odd_space import DIMENSIONS, DIM_NAMES, PREDICATES  # noqa: E402

lib = pd.read_csv(os.path.join(ROOT, 'corpus', 'odd_condition_library.csv'))
mat = pd.read_csv(os.path.join(ROOT, 'corpus', 'traceability_matrix.csv'))
OUT = os.path.join(ROOT, 'phaseA_requirement_extraction', 'results'); os.makedirs(OUT, exist_ok=True)

def preds_of(rep):
    rep = str(rep)
    if 'P1-P6' in rep:
        return {f'P{i}' for i in range(1, 7)}
    return set(re.findall(r'\bP\d\b', rep))

cond_preds = {r.condition_id: preds_of(r.represented_in) for r in lib.itertuples()}
cond_stmts = {r.condition_id: [s.strip() for s in r.statement_ids.split(';')] for r in lib.itertuples()}
pred_conds = {p: {c for c, ps in cond_preds.items() if p in ps} for p, _, _ in PREDICATES}

scen = [dict(zip(DIM_NAMES, v)) for v in itertools.product(*DIMENSIONS.values())]
truth = [{p for p, _, f in PREDICATES if f(s)} for s in scen]

# clause-anchored levels: levels named by the clause, or numeric levels at/beyond a stated limit
ANCHOR = {
    'P1': lambda s: s['precipitation'] in ('rain', 'snow'),   # clause names rain, snow
    'P4': lambda s: s['visibility'] in ('mist', 'fog'),        # clause names fog, mist
    'P7': lambda s: s['speed_kmh'] in ('60', '70'),           # at or beyond the stated 60 km/h
}

L = []
L.append(f"Scenarios: {len(scen)}")
# backward reach
n_st, n_reg, n_cond = [], Counter(), []
for t in truth:
    conds = set().union(*[pred_conds[p] for p in t]) if t else set()
    st = set().union(*[set(cond_stmts[c]) for c in conds]) if conds else set()
    n_cond.append(len(conds)); n_st.append(len(st))
    regs = {s.split('-')[0] for s in st}
    n_reg['none' if not regs else ('both' if len(regs) == 2 else regs.pop())] += 1
traced = sum(1 for t in truth if t)
L.append(f"Scenarios tracing to at least one clause: {traced} of {len(scen)} ({100*traced/len(scen):.1f}%)")
L.append(f"Regulations reached per scenario: {dict(n_reg)}")
s = pd.Series(n_st); c = pd.Series(n_cond)
L.append(f"Source statements per scenario: median {s.median():.0f}, min {s.min()}, max {s.max()}, mean {s.mean():.2f}")
L.append(f"Conditions per scenario: median {c.median():.0f}, min {c.min()}, max {c.max()}, mean {c.mean():.2f}")
# anchoring
anch = sum(1 for sc in scen if any(f(sc) for f in ANCHOR.values()))
only_design = sum(1 for sc, t in zip(scen, truth) if t and not any(f(sc) for f in ANCHOR.values()))
L.append(f"Scenarios tracing through a clause-anchored level (P1, P4 or P7): {anch} of {len(scen)} ({100*anch/len(scen):.1f}%)")
L.append(f"Traced scenarios whose trace rests only on design-decided levels: {only_design} ({100*only_design/len(scen):.1f}%)")
# forward reach
rows = []
for sid, g in mat.groupby('statement_id'):
    conds = sorted(set(g.condition_id))
    ps = sorted(set().union(*[cond_preds[x] for x in conds]))
    reach = sum(1 for t in truth if t & set(ps))
    rows.append([sid, len(conds), ';'.join(conds), ';'.join(ps), reach, g.status.iloc[0]])
fw = pd.DataFrame(rows, columns=['statement_id', 'conditions', 'condition_ids', 'predicates', 'scenarios_reached', 'status'])
fw.to_csv(os.path.join(OUT, 'trace_reach_per_statement.csv'), index=False)
L.append(f"Source statements: {len(fw)}; reaching at least one scenario: {(fw.scenarios_reached > 0).sum()}; reaching none: {(fw.scenarios_reached == 0).sum()}")
L.append("Statements serving more than one condition: " + str(fw[fw.conditions > 1][['statement_id', 'conditions', 'scenarios_reached']].values.tolist()))
L.append("Scenarios reached per statement (descending): " + str(fw.sort_values('scenarios_reached', ascending=False)[['statement_id', 'scenarios_reached']].values.tolist()))
L.append("Conditions per predicate: " + str({p: sorted(v) for p, v in pred_conds.items()}))
open(os.path.join(OUT, 'trace_reach.txt'), 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
