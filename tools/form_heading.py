#!/usr/bin/env python3
"""Headings of the assessment fields (owner, 2026-10-28): «التقويم التكويني» starts with «تفريد التعليم (5 دقائق):» and its
questions under it (English: «Formative questions (5 minutes):» — no «تفريد التعليم» in English), «التقويم الختامي» with
«أسئلة التقويم الختامي (5 دقائق):» («Summative questions (5 minutes):»); a field of several periods: under each period's heading.
Html copies start with <p class="tfrd">تفريد التعليم:</p>; grades 2–4 math draw it themselves (plain text and the item rows).
build_quiz.py's parser skips the line (HDR), so the lesson games are unchanged. Rerunning changes nothing (idempotent).
Usage: python3 tools/form_heading.py [grade/subject ...]   (build_quiz.py runs it after add_support.py)"""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B
B.FIELD.setdefault('form', (r'التقويم التكويني|Formative', {'التقويم التكويني', 'formative', 'fa', 'form'}, 7))
B.FIELD.setdefault('summ', (r'التقويم الختامي|Summative|Final assessment', {'التقويم الختامي', 'summative', 'summ', 'final', 'sa'}, 8))
# the stage's own minutes in its heading (owner, 2026-10-28: التهيئة 5 + الإجراءات 25 + التكويني 5 + الختامي 5 = 40, tools/stage_times.py);
# grade 6 fields carry their minutes in their labels, so only «تفريد التعليم:» there
HEADS = {('form', 'ar'): 'تفريد التعليم (5 دقائق):', ('summ', 'ar'): 'أسئلة التقويم الختامي (5 دقائق):',
         ('form', 'en'): 'Formative questions (5 minutes):', ('summ', 'en'): 'Summative questions (5 minutes):',
         ('form', 'lab'): 'تفريد التعليم:', ('summ', 'lab'): None}
OLD = re.compile(r'^[ \t]*(?:تفريد التعليم|أسئلة التقويم الختامي|Formative questions|Summative questions)\b[^\n]*[:：][ \t]*(?:\n|$)', re.M)
OLD_H = re.compile(r'<p class="tfrd"[^>]*>.*?</p>', re.S)
PER = re.compile(r'^((?:◆\s*)?(?:الحصة|Period|Lesson)\s*[0-9٠-٩]+[^\n]*)\n', re.M)
TFRD = '<p class="tfrd" style="margin:0 0 6px;font-weight:700;color:#2E6F73">%s</p>'

def text(t, head):
    t = OLD.sub('', t).lstrip('\n')
    if not head: return t
    return PER.sub(lambda m: m.group(1) + '\n' + head + '\n', t) if PER.search(t) else head + '\n' + t
def html(h, head):
    h = OLD_H.sub('', h)
    if not head: return h
    p = TFRD % head
    return re.sub(r'(<div class="psub">.*?</div>)', lambda m: m.group(1) + p, h) if '<div class="psub">' in h else p + h

JS_P_OLD = "if(k==='formative'||k==='summative')return (k==='formative'?'تفريد التعليم:\\n':'')+s[k].map((x,i)=>(i+1)+'. ['+x.level+'] '+x.q"
JS_P = "if(k==='formative'||k==='summative')return s[k].map((x,i)=>(i+1)+'. ['+x.level+'] '+x.q"
JS_P2 = "if(k==='formative'||k==='summative')return (k==='formative'?'تفريد التعليم (5 دقائق):\\n':'أسئلة التقويم الختامي (5 دقائق):\\n')+s[k].map((x,i)=>(i+1)+'. ['+x.level+'] '+x.q"
JS_I_OLD = "if(k==='formative'||k==='summative')return (k==='formative'?[{lab:'تفريد التعليم',t:'',x:1}]:[]).concat(s[k].map(x=>({lab:x.level,"
JS_I = "if(k==='formative'||k==='summative')return s[k].map(x=>({lab:x.level,"
JS_I2 = "if(k==='formative'||k==='summative')return [{lab:k==='formative'?'تفريد التعليم':'التقويم الختامي',t:'5 دقائق',x:1}].concat(s[k].map(x=>({lab:x.level,"
JS_I_END = "{lab:'إثرائي',t:s.sup.e}]:[]);"
JS_I_END2 = "{lab:'إثرائي',t:s.sup.e}]:[]));"

def fix_page(p, en=False):
    h = open(p, encoding='utf8').read(); lits = B.literals(h)
    les, kmap = B.page_lessons(lits)
    before = [json.dumps(x[3], ensure_ascii=False) for x in lits]
    n = 0
    for which in ('form', 'summ'):
        for li, cont, k in B.field_targets(lits, kmap, which):
            v = cont[k]
            lab = isinstance(cont, list) and len(cont) == 2 and isinstance(cont[0], str) and re.search(r'\([0-9٠-٩]+\s*(?:دقيقة|دقائق)\)', cont[0])
            head = HEADS[(which, 'lab' if lab else 'en' if en else 'ar')]
            if isinstance(v, str) and len(v.strip()) > 20:
                nv = html(v, head) if v.lstrip().startswith('<') else text(v, head)
                if nv != v: cont[k] = nv; n += 1
            elif isinstance(v, dict) and isinstance(v.get('t'), str) and isinstance(v.get('h'), str):
                nt, nh = text(v['t'], head), html(v['h'], head)
                if (nt, nh) != (v['t'], v['h']): v['t'], v['h'] = nt, nh; n += 1
            elif isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v) and len(v[1].strip()) > 20:
                nt, nh = text(v[1], head), html(v[0], head)
                if (nt, nh) != (v[1], v[0]): v[0], v[1] = nh, nt; n += 1
    t = h
    for (name, i, e, o), b0 in sorted(zip(lits, before), key=lambda z: -z[0][1]):
        if json.dumps(o, ensure_ascii=False) != b0:
            compact = '", "' not in h[i:i + 3000] and '":"' in h[i:i + 3000]
            t = t[:i] + json.dumps(o, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': ')).replace('</', '<\\/') + t[e:]
    t = t.replace(JS_P_OLD, JS_P)
    if JS_P in t and JS_P2 not in t: t = t.replace(JS_P, JS_P2); n += 1
    if JS_I_OLD in t:
        a = t.index(JS_I_OLD); b = t.index(JS_I_END2, a)
        t = t[:a] + JS_I + t[a + len(JS_I_OLD):b] + JS_I_END + t[b + len(JS_I_END2):]
    if JS_I in t and JS_I2 not in t:
        a = t.index(JS_I); b = t.index(JS_I_END, a)
        t = t[:a] + JS_I2 + t[a + len(JS_I):b] + JS_I_END2 + t[b + len(JS_I_END):]
    return n, t

def main(only=None):
    only = [a.strip('/') for a in (sys.argv[1:] if only is None else only)]
    pages = sorted(set(glob.glob(R + '[0-9]*/*/prep*/index.html') + glob.glob(R + '[0-9]*/*/prep/u*/index.html')))
    tot = 0
    for p in pages:
        rel = p[len(R):-len('/index.html')]; gs = '/'.join(rel.split('/')[:2])
        if only and gs not in only: continue
        n, t = fix_page(p, gs.endswith('/english'))
        if t != open(p, encoding='utf8').read(): open(p, 'w', encoding='utf8').write(t)
        if n: print('%-22s %4d formative fields' % (rel, n))
        tot += n
    print('done', tot)

if __name__ == '__main__': main()
