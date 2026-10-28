#!/usr/bin/env python3
"""No separate «الغلق» field (owner, 2026-10-28: «الغلق يكون في سير الدرس وليس بندًا منفصلًا»). Grade 6 Arabic and Islamic
periods are flat lists of [label, text] fields, among them «الغلق (3 دقائق)»: its minutes join «إجراءات التنفيذ» (20 → 23 دقيقة)
and the field is removed.
  • the lesson's last period already ends with «غلق الدرس (نشاط ممتع مع المواطنة)» (tools/add_identity.py): the old closing text
    is dropped and the other steps share the minutes (18 + 5);
  • any other period: the old closing becomes the procedures' last step «N. الغلق: … (3 دقائق)».
Run before add_identity.py; a page without the field is left as it is (idempotent).
Usage: python3 tools/fold_closing.py [grade/subject ...]"""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B
import proc_style as P
IDRX = re.compile(r'^[0-9٠-٩]+\.\s*(?:غلق الدرس|ختام الدرس)\b', re.M)
LAB = lambda f, pat: next((i for i, x in enumerate(f) if isinstance(x, list) and len(x) == 2 and re.match(pat, str(x[0]))), None)
mins = lambda s: P.toN((re.search(r'\(([0-9٠-٩]+)\s*(?:دقيقة|دقائق|دقيقتان)\)', s) or [0, '0'])[1])

def fold(e):
    f = e['f']; ci = LAB(f, r'\s*الغلق'); pi = LAB(f, r'\s*إجراءات')
    if ci is None or pi is None: return False
    cm, pm = mins(f[ci][0]), mins(f[pi][0]); t = f[pi][1]; c = f[ci][1].strip()
    blocks = [b for b in t.split('\n\n') if b.strip()]
    steps = [i for i, b in enumerate(blocks) if re.match(r'^[0-9٠-٩]+\.\s', b) and P.TEND.search(b.split('\n')[0])]
    if not cm or not pm or not steps: return False
    if IDRX.search(t):                       # the fun closing is there: the old closing text goes, its minutes to the other steps
        rest = [i for i in steps if not IDRX.match(blocks[i])]
        ds = P.scale_to([P.toN(P.TEND.search(blocks[i].split('\n')[0]).group(1)) for i in rest], pm + cm - 5)
        for i, d in zip(rest, ds):
            ls = blocks[i].split('\n'); m = P.TEND.search(ls[0]); ls[0] = ls[0][:m.start()] + '(' + P.minutes(d) + ')'; blocks[i] = '\n'.join(ls)
    elif c:
        body = '، '.join(re.sub(r'^\s*[-•]\s*', '', x).strip().rstrip('.،') for x in c.split('\n') if x.strip())
        si = LAB(f, r'\s*الاستراتيجيات'); st = P.strat_items(f[si][1]) if si is not None else []
        sv = st[len(steps) % len(st)] if st else ''
        blocks.append('%d. الغلق: %s (%s)' % (len(steps) + 1, body, P.minutes(cm)) + ('\nالاستراتيجيات: ' + sv.rstrip('.') + '.' if sv else ''))
    f[pi] = [re.sub(r'\(([0-9٠-٩]+)\s*(?:دقيقة|دقائق|دقيقتان)\)', '(' + P.minutes(pm + cm) + ')', f[pi][0]), '\n\n'.join(blocks)]
    del f[ci]
    return True

def main(only=None):
    only = [a.strip('/') for a in (sys.argv[1:] if only is None else only)]
    tot = 0
    for p in sorted(glob.glob(R + '[0-9]*/*/prep*/index.html')):
        rel = p[len(R):-len('/index.html')]; gs = '/'.join(rel.split('/')[:2])
        if only and gs not in only: continue
        h = open(p, encoding='utf8').read()
        if '"الغلق (' not in h: continue
        lits = B.literals(h); n = 0; t = h
        for name, i, e, o in sorted(lits, key=lambda z: -z[1]):
            if isinstance(o, list) and o and all(isinstance(x, dict) and isinstance(x.get('f'), list) for x in o):
                k = sum(fold(x) for x in o)
                if k:
                    n += k; compact = '", "' not in h[i:i + 3000] and '":"' in h[i:i + 3000]
                    t = t[:i] + json.dumps(o, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': ')).replace('</', '<\\/') + t[e:]
        if t != h: open(p, 'w', encoding='utf8').write(t)
        print('%-20s %4d periods: «الغلق» folded into the procedures' % (rel, n)); tot += n
    print('done', tot)

if __name__ == '__main__': main()
