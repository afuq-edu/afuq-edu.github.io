#!/usr/bin/env python3
"""The time of every learning outcome (owner, 2026-10-27: «الأهداف تذكر كل هدف ومن وقته من زمن الحصة، اذكر جنب الهدف الوقت
بين قوسين»): each outcome of a period ends with its share of the period, «… (10 دقائق)» / «… (10 minutes)», the shares adding
up to the period (40 minutes; prep35 35). The share comes from the period's procedures: the warm-up goes to the first outcome,
the closing steps (final assessment, «ختام الدرس») to the last one, every other step to the outcome it shares the most words
with, else to the outcomes in turn; an outcome no step went to still gets a few minutes. A field holding several periods
(«Period 1:» / «الحصة 1» parts) is timed part by part. Html copies (<li> items, the «مخرج تعليمي آخر» box) get the same times;
grades 2–4 math keep them in the session's "omins" ([{min}] for outcomes + the other outcome) and the page draws them.
assets/shift.js rescales them for 35-minute periods (the times close their lines) and tools/twoshift.js for merged periods.
Rerunning recomputes them (idempotent).
Usage: python3 tools/outcome_times.py [grade/subject ...]   (build_quiz.py runs it after add_identity.py)"""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B
import proc_style as P
OT = re.compile(r'\s*\((?:[0-9٠-٩]+) (?:دقيقة|دقيقتان|دقائق|minutes?)\)(?=\s*$|\s*<)')
OTHER = re.compile(r'^\s*[-•]?\s*(?:(?:ال)?مخرج(?:ات)?\s+(?:تعليمي(?:ة)?\s+)?(?:ال)?آخر|(?:another|other|additional)\s+(?:learning\s+)?outcome)', re.I)
SEGH = re.compile(r'^\s*(?:Period|Lesson|الحصة|حصة)\s*[0-9٠-٩]+\b', re.I)
WARM = re.compile(r'التهيئة|التمهيد|warm|lead[- ]?in|starter|opening', re.I)
CLOSE = re.compile(r'ختام الدرس|Lesson closing|التقويم الختامي|الختام|الغلق|غلق الدرس|خاتمة|plenary|closing|wrap[- ]?up|final assessment|exit ticket|بطاقة الخروج', re.I)
STOP = set('يذكر يتعرف يوضح يبين يحدد يميز يستنتج يقارن يصف يشرح يطبق يكتب يقرأ يحل يجد يستخدم الطالب الطلبة المعلم التلميذ'
           ' على إلى في من عن مع بين التي الذي ذلك هذه هذا كل بعض أو ثم حول عند خلال the and with from that this pupils students teacher will able'.split())
TASH = re.compile(r'[ً-ْٰـ]')

def words(s):
    s = TASH.sub('', B.strip_html(s) if '<' in s else s).lower()
    out = set()
    for w in re.findall(r'[ء-يa-z]{3,}', s):
        if w in STOP: continue
        w = re.sub(r'^(?:وال|بال|فال|كال|لل|ال|و)(?=[ء-ي]{3})', '', w)
        w = re.sub(r'(?:ات|ون|ين|ة|ه|ها|ية|s)$', '', w) if len(w) > 4 else w
        if len(w) >= 3 and w not in STOP: out.add(w[:6])
    return out

def steps_of_html(h):
    segs = [[]]
    for m in re.finditer(r'<p class="(pstep|phead)"[^>]*>(.*?)</p>', h, re.S):
        if m.group(1) == 'phead': segs.append([]); continue
        line = B.strip_html(re.split(r'<br\s*/?>', m.group(2))[0]).strip(); mm = P.TEND.search(line)
        if mm: segs[-1].append((line, P.toN(mm.group(1))))
    return [s for s in segs if s]

def steps_of(t):
    """[(first line, minutes)] per period of a procedures text in the style of tools/proc_style.py"""
    segs = [[]]
    for b in [x for x in t.split('\n\n') if x.strip()]:
        if re.match(r'^(?:الحصة|Period)\s', b) and not re.match(r'^[0-9٠-٩]+\.\s', b): segs.append([]); continue
        m = re.match(r'^[0-9٠-٩]+\.\s', b) and P.TEND.search(b.split('\n')[0])
        if m: segs[-1].append((b.split('\n')[0], P.toN(m.group(1))))
    return [s for s in segs if s]

def allocate(outs, steps, T):
    """minutes for each outcome (texts) from the period's steps [(line, minutes)], adding up to T"""
    k = len(outs)
    if not k: return []
    if not steps or k == 1: return P.scale_to([1] * k, T) if k > 1 else [T]
    ow = [words(o) for o in outs]; w = [0] * k
    mid = [i for i in range(len(steps)) if not (i == 0 and WARM.search(steps[i][0][:60])) and not CLOSE.search(steps[i][0][:60])]
    for i, (line, d) in enumerate(steps):
        if i not in mid: w[0 if i == 0 and WARM.search(line[:60]) else k - 1] += d; continue
        sw = words(line); sc = [len(sw & x) for x in ow]; best = max(sc)
        if best >= 2 and sc.count(best) == 1: w[sc.index(best)] += d
        else: w[min(k - 1, mid.index(i) * k // max(1, len(mid)))] += d
    even = sum(w) / k
    w = [0.5 * x + 0.5 * even for x in w]          # the steps lean the shares, every outcome keeps a fair part
    if k * 5 <= T:                                  # whole fives (5, 10, 15 …) when there is room
        r = [5 * x for x in P.scale_to(w, T // 5)]; r[-1] += T - sum(r); return r      # 35: the last share takes the odd minutes
    return P.scale_to(w, T)

def text_items(t):
    """[[line indices of the outcomes] per period part] of an outcomes text"""
    ls = t.split('\n'); parts = [[]]; seen_head = False
    for i, l in enumerate(ls):
        s = l.strip()
        if not s: continue
        if SEGH.match(s) and not re.match(r'^[0-9٠-٩]+\s*[.)\-–]', s):
            if parts[-1] or seen_head: parts.append([])
            seen_head = True; continue
        if OTHER.match(s) and not re.sub(r'^[^:：]*[:：]', '', s).strip(): continue      # «مخرج تعليمي آخر:» heading alone
        if s.endswith(':') and len(s) < 40: continue
        parts[-1].append(i)
    return [p for p in parts if p]

def time_text(t, segsteps, T, en):
    ls = t.split('\n')
    for i in range(len(ls)): ls[i] = OT.sub('', ls[i]).rstrip()
    parts = text_items('\n'.join(ls))
    if not parts: return None
    for pi, part in enumerate(parts):
        st = segsteps[pi] if len(segsteps) == len(parts) else (sum(segsteps, []) if len(parts) == 1 else [])
        ms = allocate([ls[i] for i in part], st, T)
        for i, m in zip(part, ms):
            ls[i] = re.sub(r'[.。]\s*$', '', ls[i]) + ' (' + P.minutes(m, en) + ')'
    return '\n'.join(ls)

ITEM_END = re.compile(r'</li>|(?=<br\s*/?>)|</div>|</p>')
def time_html(h, steps, T, en):
    h = OT.sub('', h)
    # items: every <li>, and the text after «مخرج … آخر:» up to its <br>/</div>/</p>
    spans = []
    for m in re.finditer(r'<li\b[^>]*>(.*?)</li>', h, re.S): spans.append((m.end() - 5, m.group(1)))
    for m in re.finditer(r'<(div|p)\b[^>]*>(?:(?!</\1>).)*?(?:مخرج|outcome)[^<]*?(?:</b>|</strong>)?(.*?)</\1>', h, re.S | re.I):
        body, base = m.group(2), m.start(2)
        pieces = re.split(r'(<br\s*/?>)', body); off = base
        for pc in pieces:
            if re.match(r'<br', pc or ''): off += len(pc); continue
            if B.strip_html(pc).strip(' :-•'): spans.append((off + len(pc.rstrip()), pc))
            off += len(pc)
    if not spans: return None
    spans.sort()
    ms = allocate([B.strip_html(x) for _, x in spans], steps, T)
    out = h
    for (pos, x), m in sorted(zip(spans, ms), key=lambda z: -z[0][0]):
        out = out[:pos].rstrip().rstrip('.') + ' (' + P.minutes(m, en) + ')' + out[pos:]
    return out

def fix_page(p, rel):
    h = open(p, encoding='utf8').read(); lits = B.literals(h)
    les, kmap = B.page_lessons(lits)
    en = rel.split('/')[1] == 'english'; T = 35 if '/prep35' in rel else 40
    parent = {}
    for name, i, e, o in lits:
        for path, x, anc in B.nodes(o):
            if isinstance(x, list) and all(isinstance(y, list) for y in x) and x:
                for y in x: parent[id(y)] = id(x)
    key = lambda c: parent.get(id(c), id(c))
    procs = {}
    for li, cont, k in B.field_targets(lits, kmap, 'proc'):
        v = cont[k]
        if isinstance(v, list) and v and all(isinstance(y, dict) and isinstance(y.get('min'), int) for y in v):
            procs.setdefault(key(cont), {})['s'] = [[(y['text'], y['min']) for y in v]]; continue
        t = v if isinstance(v, str) else v.get('t') if isinstance(v, dict) else v[1] if isinstance(v, list) and len(v) == 2 and isinstance(v[1], str) else None
        if not isinstance(t, str): continue
        html = t.lstrip().startswith('<')
        procs.setdefault(key(cont), {})['h' if html and isinstance(v, str) else 't'] = steps_of_html(t) if html else steps_of(t)
    before = [json.dumps(x[3], ensure_ascii=False) for x in lits]
    n = 0
    for li, cont, k in B.field_targets(lits, kmap, 'out'):
        if li is None: continue
        v = cont[k]; pr = procs.get(key(cont), {})
        segs = pr.get('t') or pr.get('h') or pr.get('s') or []
        flat = sum(segs, []) if segs else []
        if isinstance(v, list) and v and all(isinstance(y, dict) and isinstance(y.get('text'), str) for y in v) and isinstance(cont, dict):
            outs = [y['text'] for y in v] + ([cont['extra_outcome']['text']] if isinstance(cont.get('extra_outcome'), dict) else [])
            om = [{'min': m} for m in allocate(outs, flat, T)]
            if cont.get('omins') != om: cont['omins'] = om; n += 1
            continue
        if isinstance(v, str):
            new = time_html(v, flat, T, en) if v.lstrip().startswith('<') else time_text(v, segs, T, en)
            if new and new != v: cont[k] = new; n += 1
        elif isinstance(v, dict) and isinstance(v.get('t'), str) and isinstance(v.get('h'), str):
            nt, nh = time_text(v['t'], segs, T, en), time_html(v['h'], flat, T, en)
            if nt and nt != v['t']: v['t'] = nt; n += 1
            if nh: v['h'] = nh
        elif isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v):
            nt, nh = time_text(v[1], segs, T, en), time_html(v[0], flat, T, en)
            if nt and nt != v[1]: v[1] = nt; n += 1
            if nh: v[0] = nh
    t = h
    for (name, i, e, o), b0 in sorted(zip(lits, before), key=lambda z: -z[0][1]):
        if json.dumps(o, ensure_ascii=False) != b0:
            compact = '", "' not in h[i:i + 3000] and '":"' in h[i:i + 3000]
            t = t[:i] + json.dumps(o, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': ')).replace('</', '<\\/') + t[e:]
    return n, t

# grades 2–4 math draw the outcomes from {text, level} lists: the times come from the session's "omins"
JS_OM = "function plain(s,k){"
JS_OM2 = ("function OM(s,i){const m=s.omins&&s.omins[i]&&s.omins[i].min;return m?' ('+m+' '+(m===1||m>10?'دقيقة':m===2?'دقيقتان':'دقائق')+')':''}\n"
          "function plain(s,k){")
JS_P = "if(k==='outcomes')return s.outcomes.map((o,i)=>(i+1)+'. '+o.text).join('\\n')+'\\nمخرج تعليمي آخر: '+s.extra_outcome.text;"
JS_P2 = "if(k==='outcomes')return s.outcomes.map((o,i)=>(i+1)+'. '+o.text+OM(s,i)).join('\\n')+'\\nمخرج تعليمي آخر: '+s.extra_outcome.text+OM(s,s.outcomes.length);"
JS_I = "if(k==='outcomes')return s.outcomes.map((o,i)=>({lab:'المخرج '+(i+1),t:o.text})).concat([{lab:'مخرج آخر',t:s.extra_outcome.text,x:1}]);"
JS_I2 = "if(k==='outcomes')return s.outcomes.map((o,i)=>({lab:'المخرج '+(i+1),t:o.text+OM(s,i)})).concat([{lab:'مخرج آخر',t:s.extra_outcome.text+OM(s,s.outcomes.length),x:1}]);"

def main(only=None):
    only = [a.strip('/') for a in (sys.argv[1:] if only is None else only)]
    pages = sorted(set(glob.glob(R + '[0-9]*/*/prep*/index.html') + glob.glob(R + '[0-9]*/*/prep/u*/index.html')))
    tot = 0
    for p in pages:
        rel = p[len(R):-len('/index.html')]; gs = '/'.join(rel.split('/')[:2])
        if only and gs not in only: continue
        try: n, t = fix_page(p, rel)
        except Exception as ex: print('  skipped', rel, ex); continue
        if JS_P in t:
            t = t.replace(JS_P, JS_P2).replace(JS_I, JS_I2)
            if 'function OM(s,i)' not in t: t = t.replace(JS_OM, JS_OM2, 1)
        if t != open(p, encoding='utf8').read(): open(p, 'w', encoding='utf8').write(t)
        if n: print('%-22s %4d outcome fields timed' % (rel, n))
        tot += n
    print('done', tot)

if __name__ == '__main__': main()
