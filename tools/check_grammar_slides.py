#!/usr/bin/env python3
"""Limits for added grammar slides (uncrowded, big text — owner 2026-10-25): python3 tools/check_grammar_slides.py [tools/grammar_slides.json]. Prints every problem, or OK."""
import json,re,sys,glob
import os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
DIA=re.compile('[ً-ْٰـ]')
def n(t): return len(re.sub(r'\[\[|\]\]','',DIA.sub('',str(t))).strip())
LIM={'q':70,'a':90,'opt':22,'tf':48,'fix':60,'fill':95,'chip':16,'card':55,'head':22,'cmp':28,'word':5,'hint':45,'sortc':26,'enter':26,'pair':26,'step':60,'line':70,'rule':90,'title':40,'mem':22}
bad=[]
def need(c,msg):
    if not c: bad.append(msg)
spec=json.load(open(sys.argv[1] if len(sys.argv)>1 else R+'tools/grammar_slides.json'))
for deck,lessons in spec.items():
    if deck=='_': continue
    f=R+deck+'/index.html'; h=open(f).read(); m=re.search(r'window\.DECK=',h); d,e=json.JSONDecoder().raw_decode(h,m.end())
    P=json.load(open(R+'tools/lesson_parts.json')).get(deck,{})
    for lid,sp in lessons.items():
        Ls=[x for x in d['lessons'] if x['id']==lid]; need(Ls,'%s: no lesson %s'%(deck,lid))
        if not Ls: continue
        own=[s for s in Ls[0]['slides'] if 'add' not in s]
        need(isinstance(sp.get('part'),str) and sp['part'],'%s: part title missing'%lid)
        if lid in P and P[lid]:
            pr=[x for x in P[lid] if x[2]==sp.get('part')]
            need(pr,'%s: part «%s» not in lesson_parts.json %s'%(lid,sp.get('part'),[x[2] for x in P[lid]]))
        tot=0
        for at,new in sp['insert']:
            need(isinstance(at,int) and 1<=at<=len(own),'%s: bad index %r'%(lid,at))
            if lid in P and P[lid] and pr: a,b,_=pr[0]; need(a<=at<=b+1,'%s: index %d outside part [%d,%d+1]'%(lid,at,a,b))
            for s in new:
                tot+=1; t=s.get('type'); W='%s %s «%s»: '%(lid,t,s.get('title',''))
                need(s.get('title') and n(s['title'])<=LIM['title'],W+'title missing/too long')
                need(isinstance(s.get('note'),str) and s['note'],W+'note (teacher tip) missing')
                if t=='ask':
                    need(1<=len(s.get('qs',[]))<=3,W+'1-3 qs'); [need(n(q['q'])<=LIM['q'] and n(q.get('a',''))<=LIM['a'],W+'q/a too long: '+q['q'][:30]) for q in s.get('qs',[])]
                elif t=='explain':
                    ls=s.get('lines',[]); need(1<=len(ls)<=3,W+'1-3 lines'); [need(n(x)<=LIM['line'],W+'line too long') for x in ls]
                    need(n(s.get('rule',''))<=LIM['rule'],W+'rule too long'); need(sum(map(n,ls))+n(s.get('rule',''))<=150,W+'total text >150 (font gets small)')
                elif t=='concept':
                    cs=s.get('cards',[]); need(2<=len(cs)<=3,W+'2-3 cards'); [need(n(c['head'])<=LIM['head'] and n(c.get('text',''))<=LIM['card'],W+'card too long') for c in cs]
                elif t=='compare':
                    for k in ('right','left'):
                        sd=s.get(k); need(sd and sd.get('head') and 2<=len(sd.get('items',[]))<=4,W+k+' head + 2-4 items'); [need(n(x)<=LIM['cmp'],W+'item too long') for x in (sd or {}).get('items',[])]
                elif t=='flip':
                    cs=s.get('cards',[]); need(2<=len(cs)<=3,W+'2-3 cards'); [need(n(c['front'])<=40 and n(c.get('back',''))<=70,W+'card too long') for c in cs]
                elif t=='fill':
                    k=s.get('text','').count('____'); need(1<=k<=2,W+'1-2 blanks ____'); need(n(s.get('text','').replace('____',''))<=LIM['fill'],W+'text too long')
                    need(len(s.get('a',[]))==k,W+'a must list one answer per blank'); bk=s.get('bank',[]); need(2<=len(bk)<=4 and all(x in bk for x in s.get('a',[])) and len(set(bk))==len(bk),W+'bank 2-4 distinct chips containing all answers')
                    [need(n(x)<=LIM['chip'],W+'chip too long') for x in bk]
                elif t=='build':
                    need(s.get('mode')=='words',W+'mode words'); its=s.get('items',[]); need(1<=len(its)<=3,W+'1-3 items')
                    [need(2<=len(i['a'].split())<=LIM['word'] and n(i.get('hint',''))<=LIM['hint'],W+'item: 2-5 words, short hint') for i in its]
                elif t=='sort':
                    need(len(s.get('bins',[]))==2,W+'2 bins'); cs=s.get('cards',[]); need(4<=len(cs)<=6,W+'4-6 cards'); [need(n(c['text'])<=LIM['sortc'] and c.get('bin') in (0,1),W+'card too long/bad bin') for c in cs]
                elif t=='tf':
                    its=s.get('items',[]); need(2<=len(its)<=3,W+'2-3 items'); [need(n(i['text'])<=LIM['tf'] and isinstance(i.get('a'),bool) and (i['a'] or i.get('fix')) and n(i.get('fix',''))<=LIM['fix'],W+'item too long / false needs fix: '+i['text'][:25]) for i in its]
                elif t=='quiz':
                    qs=s.get('qs',[]); need(2<=len(qs)<=4,W+'2-4 qs'); [need(n(q['q'])<=LIM['q'] and 2<=len(q['o'])<=3 and all(n(o)<=LIM['opt'] for o in q['o']) and 0<=q['a']<len(q['o']),W+'q too long / 2-3 short options: '+q['q'][:25]) for q in qs]
                elif t=='balloons':
                    rs=s.get('rounds',[]); need(3<=len(rs)<=4,W+'3-4 rounds'); [need(n(r['q'])<=55 and len(r['o'])==3 and all(n(o)<=18 for o in r['o']) and 0<=r['a']<3,W+'round too long: '+r['q'][:25]) for r in rs]
                elif t=='race':
                    qs=s.get('qs',[]); need(3<=len(qs)<=5,W+'3-5 qs'); [need(n(q['q'])<=55 and 2<=len(q['options'])<=3 and all(n(o)<=18 for o in q['options']) and 0<=q['a']<len(q['options']),W+'q too long: '+q['q'][:25]) for q in qs]
                elif t=='enter':
                    its=s.get('items',[]); need(4<=len(its)<=6 and s.get('gate'),W+'4-6 items + gate'); [need(n(i['text'])<=LIM['enter'] and isinstance(i.get('in'),bool),W+'item too long') for i in its]
                elif t=='match' or t=='memory':
                    ps=s.get('pairs',[]); need(3<=len(ps)<=4,W+'3-4 pairs'); [need(n(p[0])<=LIM['pair'] and n(p[1])<=LIM['pair'],W+'pair too long') for p in ps]
                elif t=='steps':
                    st=s.get('steps',[]); need(2<=len(st)<=4,W+'2-4 steps'); [need(n(x)<=LIM['step'],W+'step too long') for x in st]
                elif t=='wheel':
                    its=s.get('items',[]); need(4<=len(its)<=6,W+'4-6 items'); [need(n(i['q'])<=55 and n(i.get('a',''))<=70,W+'item too long') for i in its]
                elif t=='boxes':
                    bx=s.get('boxes',[]); need(4<=len(bx)<=6,W+'4-6 boxes'); [need(n(b['q'])<=55 and n(b.get('a',''))<=70,W+'box too long') for b in bx]
                else: bad.append(W+'type not allowed')
        print('%-24s %s: %d slides'%(deck,lid,tot))
print('\n'.join(bad) if bad else 'OK')
