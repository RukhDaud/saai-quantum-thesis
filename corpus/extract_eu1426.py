"""Extract normative statements from the EUR-Lex text of Commission Implementing
Regulation (EU) 2022/1426 (original act, OJ L 221, 26.8.2022).
Input : EU_2022_1426_EURLex_page.txt (EUR-Lex HTML page saved as text by the user)
Output: eu1426_statements.csv  (verbatim text; annotation columns left empty)
Rules : Annex III: numbered paragraphs (or list items) containing shall/must.
        Annex II: ALL numbered paragraphs, flagged normative yes/no, so that
        context lists (e.g. 3.1.4.1 ODD conditions) are kept.
        Earlier rule: a statement is a numbered paragraph (or list item under it) whose text
        contains 'shall' or 'must'. List items (a), (b)... are recorded with their
        stem so the obligation is complete; stem and item are kept verbatim and
        joined with ' [...] '. Nothing is paraphrased."""
import re, csv
lines=[l.rstrip('\r\n') for l in open('EU_2022_1426_EURLex_page.txt',encoding='utf-8')]
def find(pat,start=0):
    for i in range(start,len(lines)):
        if re.fullmatch(pat,lines[i].strip()): return i
    raise SystemExit('not found: '+pat)
sections=[('Annex II',find(r'ANNEX II'),find(r'ANNEX III')),
          ('Annex III',find(r'ANNEX III'),find(r'ANNEX IV'))]
num=re.compile(r'^(\d+(?:\.\d+)*)\.?(?:\s{2,}(.*))?$')
item=re.compile(r'^\(([a-z]|[ivx]+)\)$')
rows=[]
for name,a,b in sections:
    cur=None; stem=None; buf=[]; pend_item=None
    def flush():
        global_rows=rows
        if cur is None: return
        text=' '.join(t for t in buf if t).strip()
        if text: rows.append({'section':name,'para':cur,'text':text})
    for i in range(a+1,b):
        s=lines[i].strip()
        if not s: continue
        m=num.match(s)
        if m and len(m.group(1))<=12:
            if pend_item: rows.append(pend_item); pend_item=None
            flush(); cur=m.group(1); buf=[m.group(2)] if m.group(2) else []; stem=None; continue
        mi=item.match(s)
        if mi and cur:
            if pend_item: rows.append(pend_item)
            if stem is None: stem=' '.join(t for t in buf if t).strip(); buf=[]
            pend_item={'section':name,'para':f'{cur}({mi.group(1)})','text':None,'stem':stem}
            continue
        if pend_item and pend_item['text'] is None:
            pend_item['text']=s; continue
        buf.append(s)
    if pend_item: rows.append(pend_item)
    flush()
out=[]; n=0
for r in rows:
    t=r['text'] or ''
    full = (r.get('stem','')+' [...] '+t) if r.get('stem') else t
    norm=bool(re.search(r'\b(shall|must)\b',full,re.I))
    if norm or r['section']=='Annex II':
        n+=1
        out.append({'req_id':f'EU1426-{n:03d}','normative':'yes' if norm else 'no (context only)','source':f"EU 2022/1426 (original, OJ L 221 26.8.2022), {r['section']}, point {r['para']}",
                    'text':full,'has_odd_condition':'','odd_dimension':'','variable':'','operator':'','threshold':'','unit':'','response':'','annotator':'','notes':''})
with open('eu1426_statements.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
from collections import Counter
print(len(out), Counter((o['source'].split(', ')[2],o['normative']) for o in out))
