"""Inter-annotator agreement for the Phase A requirements corpus.

Usage:
    python tools/agreement.py A1.xlsx A2.xlsx --out agreement_report.xlsx

Each input is an annotator's copy of the annotation template (sheet 'Corpus'),
or a CSV with the same columns. Rows are matched on req_id.

Reports:
  * Cohen's kappa for the categorical fields (has_odd_condition, odd_dimension, operator)
  * exact-match agreement for variable, threshold, unit (after trimming and lower-casing)
  * observed agreement for every field
  * a disagreement sheet listing every req_id/field where the annotators differ
Rows where either annotator left the field blank are excluded for that field and counted.
"""
import argparse, sys
import pandas as pd
from sklearn.metrics import cohen_kappa_score

CATEGORICAL = ['has_odd_condition', 'odd_dimension', 'operator']
TEXTUAL = ['variable', 'threshold', 'unit']

def load(path):
    if str(path).lower().endswith(('.xlsx', '.xlsm')):
        df = pd.read_excel(path, sheet_name='Corpus', dtype=str)
    else:
        df = pd.read_csv(path, dtype=str)
    df = df.fillna('')
    if 'req_id' not in df.columns:
        sys.exit(f'{path}: no req_id column')
    return df.set_index('req_id')

def norm(v):
    return ' '.join(str(v).strip().lower().split())

def compare(a, b):
    common = a.index.intersection(b.index)
    rows, dis = [], []
    for field in CATEGORICAL + TEXTUAL:
        x = a.loc[common, field].map(norm); y = b.loc[common, field].map(norm)
        both = (x != '') & (y != '')
        xs, ys = x[both], y[both]
        n = int(both.sum()); agree = int((xs == ys).sum())
        kappa = None
        if field in CATEGORICAL and n > 0:
            kappa = 1.0 if len(set(xs) | set(ys)) == 1 else cohen_kappa_score(xs, ys)
        rows.append({'field': field, 'items_compared': n, 'items_blank_in_either': int(len(common) - n),
                     'observed_agreement': (agree / n) if n else None,
                     'cohens_kappa': kappa})
        for rid in xs.index[xs != ys]:
            dis.append({'req_id': rid, 'field': field, 'A1': a.at[rid, field], 'A2': b.at[rid, field],
                        'text': a.at[rid, 'text'] if 'text' in a.columns else ''})
    summary = pd.DataFrame(rows)
    meta = {'rows_A1': len(a), 'rows_A2': len(b), 'rows_matched': len(common),
            'only_in_A1': len(a.index.difference(b.index)), 'only_in_A2': len(b.index.difference(a.index))}
    return summary, pd.DataFrame(dis, columns=['req_id', 'field', 'A1', 'A2', 'text']), meta

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a1'); ap.add_argument('a2'); ap.add_argument('--out', default='agreement_report.xlsx')
    args = ap.parse_args()
    summary, dis, meta = compare(load(args.a1), load(args.a2))
    with pd.ExcelWriter(args.out) as w:
        pd.DataFrame([meta]).to_excel(w, sheet_name='Matching', index=False)
        summary.to_excel(w, sheet_name='Agreement', index=False)
        dis.to_excel(w, sheet_name='Disagreements', index=False)
    print(pd.DataFrame([meta]).to_string(index=False)); print(summary.to_string(index=False))
    print(f'{len(dis)} disagreements written to {args.out}')

if __name__ == '__main__':
    main()
