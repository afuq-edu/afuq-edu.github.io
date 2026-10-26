#!/usr/bin/env python3
"""Remedial and enrichment activities in the formative assessment, grades 1–4 (owner, 2026-10-26).
tools/support_items.json holds, for every prep page «<grade>/<subject>», one entry per lesson in page order:
  {"title": <lesson title, for checking>, "r": <remedial activity>, "e": <enrichment activity>}
and this tool appends them under the formative questions («التقويم التكويني») of every period of the lesson (and its merged field):
  • نشاط علاجي (لمن لم يتقن): …
  • نشاط إثرائي (للمتقنين): …
(English pages: «• Remedial (pupils who need support): …» / «• Enrichment (pupils who mastered it): …»), after a blank line so the
quiz builder (tools/build_quiz.py) still reads the questions' answers as before. Grades 2–4 math store the questions as
{level, q, a} lists: the activities go in the period's "sup" and the page's renderer shows and copies them.
Rerunning replaces the lines (idempotent); the two-shift copies are rebuilt (add_twoshift.py).
Usage: python3 tools/add_support.py [grade/subject ...]"""
import re, os, sys, json
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B
B.FIELD.setdefault('form', (r'التقويم التكويني|Formative', {'التقويم التكويني', 'formative', 'fa', 'form'}, 7))
LAB = {'ar': ('• نشاط علاجي (لمن لم يتقن): ', '• نشاط إثرائي (للمتقنين): '),
       'en': ('• Remedial (pupils who need support): ', '• Enrichment (pupils who mastered it): ')}
OLD = re.compile(r'\n*(?:^• (?:نشاط علاجي|نشاط إثرائي|Remedial|Enrichment) \(.*$\n?)+', re.M)

# grades 2–4 math: the renderer builds the field text from the {level, q, a} list
JS_PLAIN = "if(k==='formative'||k==='summative')return s[k].map((x,i)=>(i+1)+'. ['+x.level+'] '+x.q+'\\n   الإجابة: '+x.a).join('\\n');"
JS_PLAIN2 = ("if(k==='formative'||k==='summative')return s[k].map((x,i)=>(i+1)+'. ['+x.level+'] '+x.q+'\\n   الإجابة: '+x.a).join('\\n')"
             "+(k==='formative'&&s.sup?'\\n\\n%s'+s.sup.r+'\\n%s'+s.sup.e:'');" % LAB['ar'])
JS_ITEMS = "if(k==='formative'||k==='summative')return s[k].map(x=>({lab:x.level,t:x.q+'\\nالإجابة: '+x.a,q:x.q,a:x.a,lvl:x.level}));"
JS_ITEMS2 = ("if(k==='formative'||k==='summative')return s[k].map(x=>({lab:x.level,t:x.q+'\\nالإجابة: '+x.a,q:x.q,a:x.a,lvl:x.level}))"
             ".concat(k==='formative'&&s.sup?[{lab:'علاجي',t:s.sup.r},{lab:'إثرائي',t:s.sup.e}]:[]);")

def js_like(o, orig):
    compact = '", "' not in orig[:3000] and '":"' in orig[:3000]
    return json.dumps(o, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': ')).replace('</', '<\\/')

def with_sup(text, r, e, lang):
    t = OLD.sub('', text.rstrip()).rstrip()
    a, b = LAB[lang]
    return t + '\n\n' + a + r + '\n' + b + e

def main(only=None):
    only = [a.strip('/') for a in (sys.argv[1:] if only is None else only)]
    data = json.load(open(R + 'tools/support_items.json', encoding='utf8'))
    done = []
    for gs, items in sorted(data.items()):
        if only and gs not in only: continue
        p = R + gs + '/prep/index.html'; h = open(p, encoding='utf8').read()
        lits = B.literals(h); les, kmap = B.page_lessons(lits)
        assert len(les) == len(items), (gs, len(les), len(items))
        for i, (l, it) in enumerate(zip(les, items)):
            if B.norm(l['title']) != B.norm(it['title']): print('  title differs', gs, i, l['title'], '|', it['title'])
        lang = 'en' if gs.endswith('/english') else 'ar'
        before = [json.dumps(x[3], ensure_ascii=False) for x in lits]
        n = 0
        for li, cont, k in B.field_targets(lits, kmap, 'form'):
            if li is None: continue
            v = cont[k]; it = items[li]
            if isinstance(v, str) and len(v.strip()) > 20:
                cont[k] = with_sup(v, it['r'], it['e'], lang); n += 1
            elif isinstance(v, list) and v and all(isinstance(x, dict) and 'q' in x for x in v) and isinstance(cont, dict):
                cont['sup'] = {'r': it['r'], 'e': it['e']}; n += 1
        t = h
        for (name, i, e, o), b in sorted(zip(lits, before), key=lambda x: -x[0][1]):
            if json.dumps(o, ensure_ascii=False) != b: t = t[:i] + js_like(o, h[i:e]) + t[e:]
        if JS_PLAIN in t: t = t.replace(JS_PLAIN, JS_PLAIN2)
        if JS_ITEMS in t: t = t.replace(JS_ITEMS, JS_ITEMS2)
        if t != h: open(p, 'w', encoding='utf8').write(t)
        print('%-14s %d formative fields' % (gs, n)); done.append(gs)
    if done:
        import add_twoshift
        sys.argv = [sys.argv[0]] + done; add_twoshift.main()

if __name__ == '__main__': main()
