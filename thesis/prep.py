import json, re, importlib.util
spec=importlib.util.spec_from_file_location('c','content.py'); c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
refs=json.load(open('refs.json'))
order=[]; num={}
def cite(m):
    keys=[k.strip() for k in m.group(1).split(',')]
    out=[]
    for k in keys:
        if k not in refs: raise SystemExit('missing ref '+k)
        if k not in num: order.append(k); num[k]=len(order)
        out.append(num[k])
    out=sorted(set(out)); groups=[]; 
    for n in out:
        if groups and n==groups[-1][1]+1: groups[-1][1]=n
        else: groups.append([n,n])
    parts=[]
    for a,b in groups:
        if b-a>=2: parts.append(f'[{a}]\u2013[{b}]')
        elif b==a+1: parts += [f'[{a}]',f'[{b}]']
        else: parts.append(f'[{a}]')
    return ', '.join(parts)
def runs(t):
    t=re.sub(r'\{([A-Za-z0-9_, ]+)\}',cite,t)
    parts=[]; 
    for seg in re.split(r'(\^\^.*?\^\^|\*\*.*?\*\*)',t):
        if not seg: continue
        if seg.startswith('^^'): parts.append({'text':seg[2:-2],'hl':True})
        elif seg.startswith('**'): parts.append({'text':seg[2:-2],'bold':True})
        else: parts.append({'text':seg})
    return parts
out=[]
for b in c.B:
    k=b[0]
    if k in('p','meta','title','h1','h2','h3','note'): out.append({'t':k,'runs':runs(b[1])})
    elif k in('bullets','numbered'): out.append({'t':k,'items':[runs(x) for x in b[1]]})
    elif k in('table','table_land'): out.append({'t':k,'caption':runs(b[1]),'header':[runs(x) for x in b[2]],'rows':[[runs(x) for x in r] for r in b[3]],'widths':b[4]})
    elif k=='pagebreak': out.append({'t':'pagebreak'})
reflist=[{'n':i+1,'key':k,'ieee':refs[k]['ieee'],'st':refs[k]['st']} for i,k in enumerate(order)]
json.dump({'title':c.TITLE,'blocks':out,'refs':reflist},open('doc.json','w'),ensure_ascii=False)
hl=sum(1 for b in out for r in (b.get('runs') or []) if r.get('hl'))
from collections import Counter
print(len(reflist),'refs cited;',Counter(r['st'] for r in reflist),'; highlighted runs:',hl)
print('Found-status refs:',[ (r['n'],r['key']) for r in reflist if r['st']!='Checked'])
