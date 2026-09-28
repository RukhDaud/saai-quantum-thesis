"""Descriptive statistics of the corpus, the condition library and the boundary predicates (Chapter 5, RQ1).

    python corpus/corpus_statistics.py      (writes corpus/corpus_statistics.txt)
"""
import itertools
import os
import re
import sys
from collections import Counter

import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(H, "..", "phaseB_qubo_scenario_selection"))
from qsel.odd_space import DIMENSIONS, DIM_NAMES, PREDICATES  # noqa: E402

L = []
eu = pd.read_csv(os.path.join(H, "eu1426_statements.csv"))
r1 = pd.read_csv(os.path.join(H, "r157_statements.csv"))
lib = pd.read_csv(os.path.join(H, "odd_condition_library.csv"))
tm = pd.read_csv(os.path.join(H, "traceability_matrix.csv"))


def part(src):
    m = re.search(r"Annex (III|II)", src)
    return "Annex " + m.group(1) if m else "other"


L.append(f"Statements: EU 2022/1426 {len(eu)}, UN R157 {len(r1)}, total {len(eu) + len(r1)}")
L.append("EU by annex: " + str(dict(Counter(eu.source.map(part)))))
L.append("EU normative: " + str(dict(Counter(eu.normative.fillna('').str.split(' ').str[0]))))
L.append("R157 normative: " + str(dict(Counter(r1.normative.fillna('').str.split(' ').str[0]))))
L.append("R157 by paragraph: " + str(dict(Counter(r1.source.str.extract(r"paragraph (\d+)")[0]))))
L.append("R157 verified: " + str(dict(Counter(r1.verified))))
src_ids = set(tm.statement_id)
L.append(f"Statements yielding at least one condition: {len(src_ids)} "
         f"(EU {sum(s.startswith('EU') for s in src_ids)}, R157 {sum(s.startswith('R157') for s in src_ids)})")
L.append("Conditions by kind: " + str(dict(Counter(lib.kind))))
L.append("Conditions with a stated threshold: " + str(dict(Counter((lib.threshold.fillna('unspecified') != 'unspecified')))))
th = lib.assign(stated=lib.threshold.fillna("unspecified") != "unspecified").groupby("kind").stated.agg(["sum", "count"])
L.append("Stated threshold by kind:\n" + th.to_string())
lib["nstat"] = lib.statement_ids.str.split(";").map(len)
L.append("Source statements per condition: " + str(dict(Counter(lib.nstat))) + f"; mean {lib.nstat.mean():.2f}")
L.append("Conditions by source regulation: " + str(dict(Counter(lib.statement_ids.map(
    lambda s: "+".join(sorted({x.strip()[:3] for x in s.split(';')})))))))
L.append("Trace-matrix rows: " + str(len(tm)) + "; status " + str(dict(Counter(tm.status))))
L.append("Conditions by dimension: " + str(dict(Counter(lib.odd_dimension.fillna('none')))))
L.append("")
space = [dict(zip(DIM_NAMES, v)) for v in itertools.product(*DIMENSIONS.values())]
L.append(f"Scenario space: {len(space)} scenarios; levels " + str({d: len(v) for d, v in DIMENSIONS.items()}))
for pid, src, f in PREDICATES:
    k = sum(f(s) for s in space)
    L.append(f"{pid} {src}: {k} scenarios ({100 * k / len(space):.1f}%)")
cnt = Counter(sum(f(s) for _, _, f in PREDICATES) for s in space)
L.append("Scenarios by number of predicates exercised: " + str(dict(sorted(cnt.items()))))
L.append("Pairwise co-occurrence of predicates (scenarios exercising both):")
for (a, _, fa), (b, _, fb) in itertools.combinations(PREDICATES, 2):
    L.append(f"  {a}-{b}: {sum(fa(s) and fb(s) for s in space)}")
open(os.path.join(H, "corpus_statistics.txt"), "w").write("\n".join(L) + "\n")
print("\n".join(L))
