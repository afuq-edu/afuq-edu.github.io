#!/usr/bin/env python3
"""Every stage of a period with its time, adding up to the period (owner, 2026-10-28, as in grade 6):
  التهيئة (5 دقائق) + إجراءات سير الدرس (25 دقيقة) + التقويم التكويني (5 دقائق) + التقويم الختامي (5 دقائق) = 40
(prep35: 5 + 20 + 5 + 5 = 35; in the 35-minute view assets/shift.js turns the procedures' 25 into 20).
  • the procedures: the warm-up step (the first one, named so — or a short first step of a period of four steps or more), and the
    steps named «التقويم الختامي» / «التقويم التكويني» (their own fields hold them now) leave; the other steps share 25 minutes, the
    closing «غلق الدرس» / Finishing stage keeps its 5; steps renumbered. Grades 2–4 math {min, text} lists the same.
  • the warm-up field ends with «(5 دقائق)» / «(5 minutes)»; the formative and final-assessment headings carry theirs
    (tools/form_heading.py).
Grade 6 Arabic and Islamic (fields labelled with their own minutes) are left as they are. Rerunning changes nothing: a period
whose steps already add up to 25 (20) is done.
Usage: python3 tools/stage_times.py [grade/subject ...]   (build_quiz.py runs it after add_identity.py)"""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B
import proc_style as P
STAGE = 5
SPFX = r'(?:(?:Presentation|Practice|Production) stage – )?'
WARM = re.compile(r'^' + SPFX + r'(?:التهيئة|التمهيد|تهيئة|تمهيد|Warm[- ]?up|Lead[- ]?in|Starter)', re.I)
ASSESS = re.compile(r'^' + SPFX + r'(?:التقويم الختامي|تقويم ختامي|التقويم التكويني|تقويم تكويني|Final assessment|Summative|Formative)', re.I)
CLOSE = re.compile(r'^(?:غلق الدرس|Finishing stage)\b')
STEP = re.compile(r'^([0-9٠-٩]+)\.\s')
HEADB = lambda b: bool(re.match(r'^(?:الحصة|Period|Lesson)\s', b)) and not STEP.match(b)

def body(line): return STEP.sub('', line, count=1)

def split_text(text, T, en):
    """the procedures text with the warm-up / assessment steps out and the rest in T - 15 minutes, or None"""
    blocks = [b for b in text.split('\n\n') if b.strip()]
    starts = [i for i, b in enumerate(blocks) if HEADB(b)]
    bounds = list(zip([0] + [s + 1 for s in starts], starts + [len(blocks)])) if starts else [(0, len(blocks))]
    P2 = T - 3 * STAGE; drop = set(); changed = False
    for a, z in bounds:
        st = [(i, P.TEND.search(blocks[i].split('\n')[0])) for i in range(a, z) if STEP.match(blocks[i])]
        st = [(i, m) for i, m in st if m]
        if len(st) < 2: continue
        ds = [P.toN(m.group(1)) for i, m in st]
        if sum(ds) != T: continue                                   # done already (25), or not a whole period
        out = set()
        b0 = body(blocks[st[0][0]].split('\n')[0])
        if WARM.match(b0) or (len(st) >= 4 and ds[0] <= 7): out.add(st[0][0])
        out |= {i for i, m in st if ASSESS.match(body(blocks[i].split('\n')[0]))}
        keep = [(i, m) for i, m in st if i not in out]
        close = [(i, m) for i, m in keep if CLOSE.match(body(blocks[i].split('\n')[0]))]
        rest = [(i, m) for i, m in keep if (i, m) not in close]
        if len(rest) < 1 or P2 - STAGE * len(close) < 2 * len(rest): continue
        new = P.scale_to([P.toN(m.group(1)) for i, m in rest], P2 - STAGE * len(close)) if len(rest) > 1 else [P2 - STAGE * len(close)]
        for (i, m), d in list(zip(rest, new)) + [(c, STAGE) for c in close]:
            ls = blocks[i].split('\n'); m2 = P.TEND.search(ls[0])
            ls[0] = ls[0][:m2.start()] + '(' + P.minutes(d, en) + ')'; blocks[i] = '\n'.join(ls)
        drop |= out; changed = True
    if not changed: return None
    res, k = [], 0
    for i, b in enumerate(blocks):                                   # renumber within each period
        if i in drop: continue
        if HEADB(b): k = 0; res.append(b); continue
        m = STEP.match(b)
        if m: k += 1; b = '%d.' % k + b[len(m.group(1)) + 1:]
        res.append(b)
    return '\n\n'.join(res)

def split_sessions(v, T):
    if sum(y['min'] for y in v) != T: return None
    out = [j for j, y in enumerate(v) if (j == 0 and (WARM.match(y['text']) or (len(v) >= 4 and y['min'] <= 7))) or ASSESS.match(y['text'])]
    keep = [y for j, y in enumerate(v) if j not in out]
    close = [y for y in keep if y.get('id')]; rest = [y for y in keep if not y.get('id')]
    P2 = T - 3 * STAGE - STAGE * len(close)
    if not rest or P2 < 2 * len(rest): return None
    ms = P.scale_to([y['min'] for y in rest], P2) if len(rest) > 1 else [P2]
    it = iter(ms)
    return [dict(y, min=STAGE) if y.get('id') else dict(y, min=next(it)) for y in keep]

WT = re.compile(r'\s*\((?:[0-9٠-٩]+)\s*(?:دقيقة|دقائق|دقيقتان|minutes?)\)\s*$')
def warm_time(t, en):
    """«… (5 دقائق)» at the end of the warm-up text (of each period part in a merged field)"""
    tag = ' (' + P.minutes(STAGE, en) + ')'
    parts = re.split(r'(\n\n(?=(?:الحصة|Period|Lesson)\s*[0-9٠-٩]))', t)
    out = []
    for p in parts:
        if not p.strip() or p.startswith('\n\n'): out.append(p); continue
        q = WT.sub('', p.rstrip()); out.append(q + tag)
    return ''.join(out)
def warm_html(h, en):
    tag = ' (' + P.minutes(STAGE, en) + ')'
    h = re.sub(r'\s*\((?:[0-9٠-٩]+)\s*(?:دقيقة|دقائق|دقيقتان|minutes?)\)(?=\s*(?:</[a-z]+>\s*)*$)', '', h.rstrip())
    m = re.search(r'((?:</[a-z]+>\s*)*)$', h)
    return h[:m.start()] + tag + h[m.start():]

def labelled(cont):
    return isinstance(cont, list) and len(cont) == 2 and isinstance(cont[0], str) and re.search(r'\([0-9٠-٩]+\s*(?:دقيقة|دقائق)\)', cont[0])

def fix_page(p, rel):
    h = open(p, encoding='utf8').read(); lits = B.literals(h)
    les, kmap = B.page_lessons(lits)
    en = rel.split('/')[1] == 'english'; T = 35 if '/prep35' in rel else 40
    before = [json.dumps(x[3], ensure_ascii=False) for x in lits]
    n = 0
    for li, cont, k in B.field_targets(lits, kmap, 'proc'):
        v = cont[k]
        if labelled(cont): continue
        if isinstance(v, list) and v and all(isinstance(y, dict) and isinstance(y.get('min'), int) and isinstance(y.get('text'), str) for y in v):
            nv = split_sessions(v, T)
            if nv and nv != v: cont[k] = nv; n += 1
            continue
        t = v if isinstance(v, str) and not v.lstrip().startswith('<') else v.get('t') if isinstance(v, dict) and isinstance(v.get('h'), str) else \
            v[1] if isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v) else None
        if not isinstance(t, str) or not P.is_new(t): continue
        new = split_text(t, T, en)
        if not new: continue
        if isinstance(v, str): cont[k] = new
        elif isinstance(v, dict): v['t'], v['h'] = new, P.render_html(new)
        else: v[0], v[1] = P.render_html(new), new
        n += 1
    for li, cont, k in B.field_targets(lits, kmap, 'warm'):
        v = cont[k]
        if li is None or labelled(cont): continue
        if isinstance(v, str) and len(v.strip()) > 10:
            nv = warm_html(v, en) if v.lstrip().startswith('<') else warm_time(v, en)
            if nv != v: cont[k] = nv; n += 1
        elif isinstance(v, dict) and isinstance(v.get('t'), str) and isinstance(v.get('h'), str):
            v['t'], v['h'] = warm_time(v['t'], en), warm_html(v['h'], en)
        elif isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v):
            v[0], v[1] = warm_html(v[0], en), warm_time(v[1], en)
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
    pages = sorted(set(glob.glob(R + '[0-9]*/*/prep*/index.html') + glob.glob(R + '[0-9]*/*/prep/u*/index.html')))
    tot = 0
    for p in pages:
        rel = p[len(R):-len('/index.html')]; gs = '/'.join(rel.split('/')[:2])
        if only and gs not in only: continue
        try: n, t = fix_page(p, rel)
        except Exception as ex: print('  skipped', rel, ex); continue
        if t != open(p, encoding='utf8').read(): open(p, 'w', encoding='utf8').write(t)
        if n: print('%-22s %4d fields' % (rel, n))
        tot += n
    print('done', tot)

if __name__ == '__main__': main()
