#!/usr/bin/env python3
"""«تفريد التعليم» heading on the formative assessment (owner, 2026-10-28): every «التقويم التكويني» field starts with the line
«تفريد التعليم:» and its questions follow under it — every subject except English (owner: «اللغة الإنجليزية لا تكتب هذا»).
Html copies start with <p class="tfrd">تفريد التعليم:</p>; grades 2–4 math draw it themselves (plain text and the item rows).
build_quiz.py's parser skips the line (HDR), so the lesson games are unchanged. Rerunning changes nothing (idempotent).
Usage: python3 tools/form_heading.py [grade/subject ...]   (build_quiz.py runs it after add_support.py)"""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B
B.FIELD.setdefault('form', (r'التقويم التكويني|Formative', {'التقويم التكويني', 'formative', 'fa', 'form'}, 7))
HEAD = 'تفريد التعليم:'
OLD = re.compile(r'^\s*تفريد التعليم\s*[:：]?[ \t]*\n')
HTML = '<p class="tfrd" style="margin:0 0 6px;font-weight:700;color:#2E6F73">تفريد التعليم:</p>'
OLD_H = re.compile(r'^\s*<p class="tfrd"[^>]*>.*?</p>', re.S)

def text(t): return HEAD + '\n' + OLD.sub('', t).lstrip('\n')
def html(h): return HTML + OLD_H.sub('', h)

JS_P = "if(k==='formative'||k==='summative')return s[k].map((x,i)=>(i+1)+'. ['+x.level+'] '+x.q"
JS_P2 = "if(k==='formative'||k==='summative')return (k==='formative'?'تفريد التعليم:\\n':'')+s[k].map((x,i)=>(i+1)+'. ['+x.level+'] '+x.q"
JS_I = "if(k==='formative'||k==='summative')return s[k].map(x=>({lab:x.level,"
JS_I2 = "if(k==='formative'||k==='summative')return (k==='formative'?[{lab:'تفريد التعليم',t:'',x:1}]:[]).concat(s[k].map(x=>({lab:x.level,"
JS_I_END = "{lab:'إثرائي',t:s.sup.e}]:[]);"
JS_I_END2 = "{lab:'إثرائي',t:s.sup.e}]:[]));"

def fix_page(p):
    h = open(p, encoding='utf8').read(); lits = B.literals(h)
    les, kmap = B.page_lessons(lits)
    before = [json.dumps(x[3], ensure_ascii=False) for x in lits]
    n = 0
    for li, cont, k in B.field_targets(lits, kmap, 'form'):
        v = cont[k]
        if isinstance(v, str) and len(v.strip()) > 20:
            nv = html(v) if v.lstrip().startswith('<') else text(v)
            if nv != v: cont[k] = nv; n += 1
        elif isinstance(v, dict) and isinstance(v.get('t'), str) and isinstance(v.get('h'), str):
            if text(v['t']) != v['t'] or html(v['h']) != v['h']: v['t'], v['h'] = text(v['t']), html(v['h']); n += 1
        elif isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v) and len(v[1].strip()) > 20:
            if text(v[1]) != v[1] or html(v[0]) != v[0]: v[0], v[1] = html(v[0]), text(v[1]); n += 1
    t = h
    for (name, i, e, o), b0 in sorted(zip(lits, before), key=lambda z: -z[0][1]):
        if json.dumps(o, ensure_ascii=False) != b0:
            compact = '", "' not in h[i:i + 3000] and '":"' in h[i:i + 3000]
            t = t[:i] + json.dumps(o, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': ')).replace('</', '<\\/') + t[e:]
    if JS_P in t and JS_P2 not in t: t = t.replace(JS_P, JS_P2); n += 1
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
        if gs.endswith('/english') or (only and gs not in only): continue
        n, t = fix_page(p)
        if t != open(p, encoding='utf8').read(): open(p, 'w', encoding='utf8').write(t)
        if n: print('%-22s %4d formative fields' % (rel, n))
        tot += n
    print('done', tot)

if __name__ == '__main__': main()
