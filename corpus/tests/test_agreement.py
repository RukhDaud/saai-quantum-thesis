# Unit test on a hand-made toy example (not corpus data): checks kappa and exact-match logic.
import os, sys, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from agreement import compare
from sklearn.metrics import cohen_kappa_score


def test_agreement_toy():
    a = pd.DataFrame({'req_id':['r1','r2','r3','r4'],'text':['t']*4,
        'has_odd_condition':['yes','yes','no','yes'],'odd_dimension':['speed','visibility','none','speed'],
        'operator':['<=','qualitative','none','<='],'variable':['Speed','visibility','','ego speed'],
        'threshold':['60','unspecified','','60'],'unit':['km/h','none','','km/h']}).set_index('req_id')
    b = a.copy(); b.loc['r2','odd_dimension']='lighting'; b.loc['r4','variable']='speed'; b.loc['r1','variable']='speed '
    s, d, m = compare(a, b)
    row = s.set_index('field')
    exp = cohen_kappa_score(['speed','visibility','none','speed'],['speed','lighting','none','speed'])
    assert abs(row.at['odd_dimension','cohens_kappa']-exp) < 1e-12
    assert row.at['has_odd_condition','cohens_kappa'] == 1.0
    assert row.at['variable','items_compared'] == 3            # r3 blank in both -> excluded
    assert row.at['variable','observed_agreement'] == 2/3      # 'Speed' vs 'speed ' normalise equal; r4 differs
    assert len(d) == 2 and m['rows_matched'] == 4
    print('all agreement tests passed; toy kappa(odd_dimension) =', round(exp,3))


if __name__ == '__main__':
    test_agreement_toy()
