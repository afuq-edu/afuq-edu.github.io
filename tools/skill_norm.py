"""The Arabic grade 1–4 period preps (four page formats) as one list: [{t, u, sb, tg, p: [{ax, wk, f: [10 fields]}]}] (tools/add_skill_prep.py)."""
import sys,json
import os; R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'; sys.path.insert(0,R+'tools'); import build_quiz as B
def lit(g):
    h=open(R+'%d/arabic/prep/index.html'%g,encoding='utf8').read()
    return {n:o for n,i,e,o in B.literals(h)}
def txt(x):
    if isinstance(x,str): return x
    if isinstance(x,dict): return x.get('t') or x.get('text') or ''
    if isinstance(x,list) and len(x)==2 and all(isinstance(y,str) for y in x): return x[1]
    return json.dumps(x,ensure_ascii=False)
def norm(g):
    d=lit(g); out=[]
    if g==1:
        for L in d['D']['lessons']:
            out.append(dict(t=L['title'],u=L['unit'],sb=L.get('sb',''),tg=L.get('tg',''),p=[dict(ax=p['axis'],wk=p['week'],f=[txt(x) for x in p['f']]) for p in L['periods']]))
    elif g==2:
        for L in d['D']:
            out.append(dict(t=L['t'],u=L['u'],sb='',tg='',p=[dict(ax=p['focus'],wk=p['week'],sb=p.get('book',''),tg=p.get('tg',''),f=[txt(x) for x in p['f']]) for p in L['p']]))
    elif g==3:
        for L in d['DATA']['lessons']:
            out.append(dict(t=L['name'],u=L['unit'],sb='',tg='',p=[dict(ax=p['topic'],wk=p['week'],f=[txt(x) for x in p['fields']]) for p in L['periods']]))
    else:
        for L in d['D']:
            out.append(dict(t=L['t'],u=L['u'],sb=L.get('sb',''),tg=L.get('tg',''),p=[dict(ax=p['ax'],wk=p['wk'],sb=p.get('pg',''),f=[txt(x) for x in p['f']]) for p in L['p']]))
    return out
