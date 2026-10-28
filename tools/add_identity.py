#!/usr/bin/env python3
"""«غلق الدرس» — identity and citizenship (owner, 2026-10-27/28): the lesson's procedures end (its last period) with a
fun closing step — a short group activity or game that ties the lesson's own content to Omani identity and citizenship (a value, a place,
heritage, a national symbol or occasion, the economy, Oman Vision 2040). It takes 5 minutes of the period: the period's
other steps are scaled to the rest (40 − 5 = 35; prep35 30; grade 6 Arabic/Islamic 20 − 5 = 15), so the period still adds up.
  N. غلق الدرس (نشاط ممتع مع المواطنة) – <name>: <activity> (5 دقائق)
  الاستراتيجيات: <strategy>.
(English pages: «N. Finishing stage (fun activity with citizenship) – <name>: … (5 minutes)» / «Strategies: …», the last stage after
Presentation / Practice / Production, tools/english_stages.py.) Only in the procedures, not in the final assessment (owner, 2026-10-28).
tools/identity_items.json: {"<grade>/<subject>/prep[/uN]": [{"title", "n", "a", "s"} per lesson in page order]};
prep35 pages use their prep page's items (matched by title). Text fields in the procedures style (tools/proc_style.py) get the
step in their last period (a field holding several periods: its last «الحصة N» part), html copies are redrawn, grades 2–4 math
get a {min, text, strategy} entry in the last session's procedures. Rerunning replaces the step (idempotent).
Usage: python3 tools/add_identity.py [grade/subject ...]   (build_quiz.py runs it after proc_style.py)"""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B
import proc_style as P
MIN = 5
IDRX = re.compile(r'^[0-9٠-٩]+\.\s*(?:غلق الدرس|Finishing stage|ختام الدرس|Lesson closing)\b[^–\n]*– ')   # the old labels too
STEP = re.compile(r'^[0-9٠-٩]+\.\s')
HEAD = lambda b: bool(re.match(r'^(?:الحصة|Period)\s', b)) and not STEP.match(b)

def block(k, it, en):
    a = it['a'].strip().rstrip('.')
    if en: return '%d. Finishing stage (fun activity with citizenship) – %s: %s (%s)\nStrategies: %s.' % (k, it['n'], a, P.minutes(MIN, True), it['s'].rstrip('.'))
    return '%d. غلق الدرس (نشاط ممتع مع المواطنة) – %s: %s (%s)\nالاستراتيجيات: %s.' % (k, it['n'], a, P.minutes(MIN), it['s'].rstrip('.'))

def with_identity(text, it, en):
    """text (procedures style) with the closing step at the end of its last period, or None"""
    blocks = [b for b in text.split('\n\n') if b.strip()]
    start = max([i for i, b in enumerate(blocks) if HEAD(b)] + [0])
    seg = list(range(start, len(blocks)))
    timed = [(i, P.TEND.search(blocks[i].split('\n')[0])) for i in seg if STEP.match(blocks[i])]
    timed = [(i, m) for i, m in timed if m]
    if not timed: return None
    S = sum(P.toN(m.group(1)) for i, m in timed)
    old = [i for i, m in timed if IDRX.match(blocks[i])]
    rest = [(i, m) for i, m in timed if i not in old]
    if len(rest) < 2 or S - MIN < 2 * len(rest) or S < 15: return None
    new = P.scale_to([P.toN(m.group(1)) for i, m in rest], S - MIN)
    for (i, m), d in zip(rest, new):
        ls = blocks[i].split('\n'); m2 = P.TEND.search(ls[0])
        ls[0] = ls[0][:m2.start()] + '(' + P.minutes(d, bool(re.search('minute', m2.group(2)))) + ')'; blocks[i] = '\n'.join(ls)
    blocks = [b for i, b in enumerate(blocks) if i not in old]
    last = max(i for i, m in rest) - sum(1 for o in old if o < max(i for i, m in rest))
    k = sum(1 for b in blocks[start:last + 1] if STEP.match(b))
    blocks.insert(last + 1, block(k + 1, it, en))
    out = '\n\n'.join(blocks)
    return out if out != text else None

def items_for(rel, data):
    if rel in data: return data[rel]
    if '/prep35' in rel and rel.replace('/prep35', '/prep') in data:
        return {'by_title': {B.norm(x['title']): x for x in data[rel.replace('/prep35', '/prep')]}}
    return None

def fix_page(p, rel, items):
    h = open(p, encoding='utf8').read(); lits = B.literals(h)
    les, kmap = B.page_lessons(lits)
    if isinstance(items, dict): items = [items['by_title'].get(B.norm(l['title'])) for l in les]
    if len(items) != len(les): print('  lessons differ', rel, len(les), len(items)); return 0, h
    en = rel.split('/')[1] == 'english'
    before = [json.dumps(x[3], ensure_ascii=False) for x in lits]
    # the last period of each lesson, per kind of copy (plain text / html / {h, t} / [html, text] / merged periods / sessions)
    last = {}
    for li, cont, k in B.field_targets(lits, kmap, 'proc'):
        if li is None or not items[li]: continue
        v = cont[k]
        if isinstance(v, list) and v and all(isinstance(y, dict) and isinstance(y.get('min'), int) and isinstance(y.get('text'), str) for y in v): kind = 'sessions'
        elif isinstance(v, str): kind = 'html' if v.lstrip().startswith('<') else 'text'
        elif isinstance(v, dict) and isinstance(v.get('t'), str) and isinstance(v.get('h'), str): kind = 'ht'
        elif isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v): kind = 'pair'
        else: continue
        t = v if kind == 'text' else B.strip_html(v) if kind == 'html' else v['t'] if kind == 'ht' else v[1] if kind == 'pair' else ''
        if kind != 'sessions' and not P.is_new(t): continue
        comb = kind != 'sessions' and any(HEAD(b) for b in t.split('\n\n'))
        last[(li, kind, comb)] = (cont, k, kind)
    n = 0
    for (li, _, _), (cont, k, kind) in last.items():
        it = items[li]; v = cont[k]
        if kind == 'sessions':
            pr = [y for y in v if not y.get('id')]
            S = sum(y['min'] for y in v)
            if len(pr) < 2 or S < 15: continue
            ms = P.scale_to([y['min'] for y in pr], S - MIN)
            nv = [dict(y, min=m) for y, m in zip(pr, ms)] + [{'min': MIN, 'text': 'غلق الدرس (نشاط ممتع مع المواطنة) – %s: %s' % (it['n'], it['a'].strip().rstrip('.')), 'strategy': it['s'].rstrip('.'), 'id': 1}]
            if nv != v: cont[k] = nv; n += 1
            continue
        t = v if kind == 'text' else B.strip_html(v) if kind == 'html' else v['t'] if kind == 'ht' else v[1]
        new = with_identity(t, it, en)
        if new is None: continue
        if kind == 'text': cont[k] = new
        elif kind == 'html': cont[k] = P.render_html(new)
        elif kind == 'ht': v['t'], v['h'] = new, P.render_html(new)
        else: v[0], v[1] = P.render_html(new), new
        n += 1
    # parallel html lists (html / txt …) follow their text
    for name, i, e, o in lits:
        for path, x, anc in B.nodes(o):
            if not isinstance(x, dict): continue
            for a, b in (('html', 'plain'), ('h', 't'), ('html', 'txt'), ('html', 'text')):
                if isinstance(x.get(a), list) and isinstance(x.get(b), list) and len(x[a]) == len(x[b]):
                    for j, t in enumerate(x[b]):
                        if isinstance(t, str) and P.is_new(t) and isinstance(x[a][j], str) and 'class="plist"' in x[a][j] and x[a][j] != P.render_html(t):
                            x[a][j] = P.render_html(t)
    t = h
    for (name, i, e, o), b0 in sorted(zip(lits, before), key=lambda z: -z[0][1]):
        if json.dumps(o, ensure_ascii=False) != b0:
            compact = '", "' not in h[i:i + 3000] and '":"' in h[i:i + 3000]
            t = t[:i] + json.dumps(o, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': ')).replace('</', '<\\/') + t[e:]
    return n, t

def main(only=None):
    only = [a.strip('/') for a in (sys.argv[1:] if only is None else only)]
    data = json.load(open(R + 'tools/identity_items.json', encoding='utf8'))
    pages = sorted(set(glob.glob(R + '[0-9]*/*/prep*/index.html') + glob.glob(R + '[0-9]*/*/prep/u*/index.html')))
    tot = 0
    for p in pages:
        rel = p[len(R):-len('/index.html')]; gs = '/'.join(rel.split('/')[:2])
        if only and gs not in only: continue
        items = items_for(rel, data)
        if not items: continue
        n, t = fix_page(p, rel, items)
        if t != open(p, encoding='utf8').read(): open(p, 'w', encoding='utf8').write(t)
        print('%-22s %4d closing steps' % (rel, n)); tot += n
    print('done', tot)

if __name__ == '__main__': main()
