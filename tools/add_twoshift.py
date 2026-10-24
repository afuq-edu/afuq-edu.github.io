#!/usr/bin/env python3
"""Two-shift preps (النشرة التوجيهية 2026/2027): for every prep page whose subject has fewer weekly periods in two-shift
schools (tools/bulletin/periods_2026.json), tools/twoshift.js builds the page's data with the lessons' periods merged down to
the bulletin's term-1 total, and this tool stores it next to the one-shift data:
  NAME=(window.AFUQ35||function(x){return x})(<one shift>,<two shifts>)
  <script type="application/json">…</script><script>window.AFUQ35&&AFUQ35.el(…previousElementSibling,<two shifts>)</script>
assets/shift.js shows the second one when «فترتان» is chosen. The two-shift data is always rebuilt from the one-shift data,
so rerun this after any change to a prep (build_quiz.py runs it after add_shift.py).
Usage: python3 tools/add_twoshift.py [grade/subject ...]"""
import re, os, sys, json, subprocess, tempfile
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B, add_shift as S
BUL = json.load(open(R + 'tools/bulletin/periods_2026.json', encoding='utf8'))
HOOK = re.compile(r'<script>window\.AFUQ35&&AFUQ35\.el\(document\.currentScript\.previousElementSibling(,.*?)?\)</script>', re.S)
DEC = json.JSONDecoder()

def js(o): return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')

def counts(rel):
    g, s = rel.split('/')[:2]
    v = BUL.get(s, {}).get(g)
    return (v[2], v[3]) if v and v[3] < v[2] else None

def write(h, lits, outs):
    """h with each literal's two-shift copy stored (or removed when there is none), last literal first."""
    for (name, i, e, o), o2 in sorted(zip(lits, outs), key=lambda x: -x[0][1]):
        if name == '#json':
            close = h.find('</script>', e) + len('</script>')
            m = HOOK.match(h, close)
            if not m: continue
            new = '<script>window.AFUQ35&&AFUQ35.el(document.currentScript.previousElementSibling%s)</script>' % (',' + js(o2) if o2 is not None else '')
            h = h[:close] + new + h[m.end():]
            continue
        if not h[:i].endswith(S.WRAP): continue
        j = e
        if h[j] == ',':   # an older two-shift copy
            _, j2 = DEC.raw_decode(h, j + 1); j = j2
        if h[j] != ')': continue
        h = h[:e] + (',' + js(o2) if o2 is not None else '') + h[j:]
    return h

def main():
    only = [a.strip('/') for a in sys.argv[1:]]
    jobs, pages = [], []
    for p in S.pages():
        rel = p[len(R):]
        if only and '/'.join(rel.split('/')[:2]) not in only: continue
        h = open(p, encoding='utf8').read()
        if S.TAG not in h: continue
        c = counts(rel)
        lits = B.literals(h)
        pages.append((p, rel, h, lits, c))
        if c: jobs.append({'rel': rel, 't1': c[0], 't2': c[1], 'lits': [o for _, _, _, o in lits]})
    res = {}
    if jobs:
        with tempfile.TemporaryDirectory() as d:
            json.dump({'pages': jobs}, open(d + '/in.json', 'w'), ensure_ascii=False)
            subprocess.run(['node', R + 'tools/twoshift.js', d + '/in.json', d + '/out.json'], check=True)
            res = {x['rel']: x for x in json.load(open(d + '/out.json'))['pages']}
    n = 0
    for p, rel, h, lits, c in pages:
        r = res.get(rel)
        outs = r['lits'] if r else [None] * len(lits)
        t = write(h, lits, outs)
        if t != h: open(p, 'w', encoding='utf8').write(t); n += 1
        if r: print('%-24s %s' % (rel[:-11], r['report']))
    print('two-shift data written to %d prep pages' % n)

if __name__ == '__main__': main()
