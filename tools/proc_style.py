#!/usr/bin/env python3
"""Lesson procedures («إجراءات سير الدرس / الأنشطة التدريسية») in one style in every prep page (owner, 2026-10-27):
  الحصة الأولى: <focus> — زمن الحصة 40 دقيقة          (only where one field holds several periods)
  1. التهيئة: يعرض المعلم …، ويتأمل الطالب … (5 دقائق)
  الاستراتيجيات: التعلم بالاكتشاف.
  2. …
Each step is one sentence — the teacher's part, then the pupils' («، ويصف الطالب …» / «، والطلبة يجيبون …») — with its time
at the end and its strategy on the line under it (the step's own, else the period's strategies in turn). Steps are
separated by a blank line, so the paste into Noor keeps them apart (assets/copyfix.js). English pages: «1. … (5 minutes)» /
«Strategies: …». Html copies ({h, t}, [html, text], html/plain lists) are redrawn from the text (render_html); grades 2–4 math
keep their {min, text} lists and the page draws them the same way. A text the parser does not understand is left as it is.
tools/twoshift.js reads this style for the two-shift copies and assets/shift.js rescales its times for 35-minute periods.
Usage: python3 tools/proc_style.py [grade/subject ...]   (idempotent; build_quiz.py runs it after proc_list.py)"""
import re, os, sys, json, glob, html as H
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B
B.FIELD.setdefault('proc', (r'إجراءات سير الدرس|الأنشطة التدريسية|إجراءات التنفيذ|Procedures|Lesson procedures|Teaching activities|Lesson steps',
                            {'إجراءات سير الدرس / الأنشطة التدريسية', 'procedures', 'proc', 'steps', 'pr'}, 6))
B.FIELD.setdefault('warm', (r'التهيئة|التمهيد|التعلم القبلي|Warm[- ]?up|Lead[- ]?in|Starter|Prior learning',
                            {'التهيئة / التمهيد / التعلم القبلي', 'warmup', 'warm', 'intro'}, 5))
B.FIELD.setdefault('strat', (r'الاستراتيجيات|استراتيجيات التدريس|Strategies|Teaching strategies',
                             {'الاستراتيجيات', 'strategies', 'strat', 'st'}, 2))

AR = '٠١٢٣٤٥٦٧٨٩'
def toN(x): return int(str(x).translate(str.maketrans(AR, '0123456789')))
D = r'[0-9٠-٩]+'
UNIT = r'(?:دقيقتان|دقيقتين|دقائق|دقيقة|د(?![؀-ۿ])|minutes?|mins?\b|min\b)'
ORD = ['الأولى', 'الثانية', 'الثالثة', 'الرابعة', 'الخامسة', 'السادسة', 'السابعة', 'الثامنة', 'التاسعة', 'العاشرة']
EN_ORD = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']

def minutes(n, en=False):
    if en: return '%d minute%s' % (n, '' if n == 1 else 's')
    return '%d %s' % (n, 'دقيقة' if n == 1 or n > 10 else 'دقيقتان' if n == 2 else 'دقائق')

# ---------------------------------------------------------------- parsing
TEACH = r'(?:دور\s+)?(?:المعلم(?:ة)?|المدرس(?:ة)?)|Teacher'
STUD = r'(?:دور\s+)?(?:الطالب(?:ة)?|الطلبة|الطلاب|الطالبات|التلميذ(?:ة)?|التلاميذ|المتعلم(?:ة|ون|ين)?|المتعلمين|المجموعات)|Pupils?|Students?|Learners?'
STRAT = r'الاستراتيجي(?:ة|ات)|استراتيجية|Strateg(?:y|ies)'
ROLE_LINE = re.compile(r'^\s*(?:[-•–*]\s*)?(' + TEACH + r'|' + STUD + r'|' + STRAT + r')\s*[:：]\s*(.*)$', re.I)
ROLE_IN = re.compile(r'(?:^|\s[—|–-]\s*|\s\|\s*|\.\s+|\s)(' + TEACH + r'|' + STUD + r')\s*[:：]\s*', re.I)
SEG = re.compile(r'^\s*(?:[◆◄►•]\s*)?(?:الحصة|Period|Lesson)\s*(?:' + D + r'|الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة)\b\s*(?:من\s*' + D + r')?\s*[:：.\-–—]?\s*(.*)$', re.I)
TOTAL = re.compile(r'^\s*[-–•(]?\s*(?:إجمالي زمن الحصة|إجمالي الزمن|المجموع|مجموع الزمن|مجموع زمن الحصة|مجموع زمن الأنشطة|الزمن الكلي|زمن الحصة|Total(?: time)?)\b', re.I)
TIMES = [   # (regex, kind) — in the order they are tried on a step's first line
    (re.compile(r'\(\s*(' + D + r')\s*' + UNIT + r'\s*[:،,]\s*(?:من\s+)?(?:الدقيقة\s*)?⁦?(' + D + r')\s*(?:إلى|–|-)\s*(' + D + r')⁩?\s*\)'), 'full'),
    (re.compile(r'(?:من\s+)?الدقيقة\s*⁦?(' + D + r')\s*(?:إلى|حتى|–|-)\s*(' + D + r')⁩?'), 'range'),
    (re.compile(r'\(\s*(' + D + r')\s*[–\-]\s*(' + D + r')\s*' + UNIT + r'\s*\)'), 'range'),
    (re.compile(r'(?<![0-9٠-٩])(' + D + r')\s*[–\-]\s*(' + D + r')\s*' + UNIT), 'range'),
    (re.compile(r'\(\s*(' + D + r')\s*' + UNIT + r'\s*\)'), 'dur'),
    (re.compile(r'(?<![0-9٠-٩])(' + D + r')\s*' + UNIT), 'dur')]
NUMPFX = re.compile(r'^\s*(?:[◆◄►•*-]\s*)?(?:(?:النشاط|نشاط|Activity|Step|الخطوة)\s*' + D + r'\s*|' + D + r'\s*[.)\-–]\s*)')

def time_of(line):
    """(minutes, the line without its time expression) for a step's first line, or None"""
    head = line[:140]
    time_of.rng = None
    for rx, k in TIMES:
        m = rx.search(head)
        if not m: continue
        if k == 'full': d = toN(m.group(1))
        elif k == 'range':
            a, b = toN(m.group(1)), toN(m.group(2)); d = b - a; time_of.rng = (a, b)   # inclusive or not: decided per text in parse()
        else: d = toN(m.group(1))
        if not (0 < d <= 60): continue
        if k == 'dur' and rx is TIMES[-1][0] and m.start() > 30 and not NUMPFX.match(line): continue   # «… وتجري 30 دقيقة» inside a sentence is not a step's time
        rest = (line[:m.start()] + ' ' + line[m.end():])
        rest = re.sub(r'\(\s*\)|\[\s*\]', ' ', rest)
        return d, rest
    return None

def clean(s): return re.sub(r'\s+', ' ', s or '').strip(' \t-–—:：|،,')

def split_roles(text):
    """{'t': teacher text, 's': student text, 'x': text before any role label} from one line with inline role labels"""
    out = {'t': '', 's': '', 'x': ''}; ms = list(ROLE_IN.finditer(text))
    if not ms: out['x'] = text; return out
    out['x'] = text[:ms[0].start()]
    for i, m in enumerate(ms):
        part = text[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(text)]
        k = 't' if re.match(TEACH, m.group(1), re.I) else 's'
        out[k] = (out[k] + ' ' + part).strip()
    return out

def parse(text):
    """[{'head': period heading or None, 'steps': [{min, name, t, s, st}]}], or None when the text is not a timed step list"""
    segs = [{'head': None, 'steps': []}]; cur = None; loose = 0
    for raw in str(text).replace('\r', '').split('\n'):
        l = raw.strip()
        if not l: continue
        if TOTAL.match(l): continue
        m = SEG.match(l)
        if m and not time_of(l) and len(l) < 160:
            segs.append({'head': clean(m.group(1)), 'steps': []}); cur = None; continue
        rm = ROLE_LINE.match(l)
        if rm and cur is not None:
            lab, val = rm.group(1), clean(rm.group(2))
            if re.match(STRAT, lab, re.I): cur['st'] = (cur['st'] + '، ' + val).strip('، ') if cur['st'] else val
            elif re.match(TEACH, lab, re.I): cur['t'] = (cur['t'] + ' ' + val).strip()
            else: cur['s'] = (cur['s'] + ' ' + val).strip()
            continue
        tm = None if rm else time_of(l)
        if tm:
            d, rest = tm; rng = time_of.rng
            rest = NUMPFX.sub('', rest.strip())
            rest = re.sub(r'^\s*(?:Period|Lesson)\s*' + D + r'\s*[:：]?', '', rest)
            for rx, _k in TIMES: rest = rx.sub(' ', rest)   # a second way of writing the same time («التهيئة – 5 دقائق (الدقيقة 0–5)»)
            rest = re.sub(r'\(\s*\)|\[\s*\]|\s[–—-]\s*(?=[:：]|$)', ' ', rest)
            parts = split_roles(rest)
            cur = {'rng': rng, 'min': d, 'name': '', 'hx': clean(parts['x']), 'inline': bool(parts['t'] or parts['s']), 't': clean(parts['t']), 's': clean(parts['s']), 'st': ''}
            segs[-1]['steps'].append(cur); continue
        if cur is not None:
            sp = split_roles(l)
            if sp['t'] or sp['s']:
                cur['t'] = (cur['t'] + ' ' + clean(sp['x'] + ' ' + sp['t'])).strip(); cur['s'] = (cur['s'] + ' ' + clean(sp['s'])).strip()
            elif re.match(r'^[-•–*]\s', l) and cur['t']: cur['t'] = cur['t'].rstrip('.، ') + '؛ ' + clean(l.lstrip('•-–* '))
            else: cur['t'] = (cur['t'] + ' ' + clean(l.lstrip('•-–* '))).strip()
        else: loose += 1
    segs = [s for s in segs if s['steps']]
    if not segs or loose > 2: return None
    for s in segs:   # ranges «من الدقيقة 1 إلى 5، 6 إلى 15…» count both ends when the first starts at 1
        incl = bool(s['steps'] and s['steps'][0]['rng'] and s['steps'][0]['rng'][0] == 1)
        for st in s['steps']:
            r = st.pop('rng')
            if r and incl: st['min'] = r[1] - r[0] + 1
            if not (0 < st['min'] <= 60): return None
            x = st.pop('hx'); inline = st.pop('inline')
            if x:
                if inline or st['t']: st['name'] = x            # «التهيئة (5 دقائق):» + «المعلم: …» lines
                else:                                           # «1. 5 دقائق — التهيئة: <teacher>» / «1. 5 دقائق: <teacher>»
                    c = re.search(r'[:：]', x)
                    if c and c.start() <= 60 and len(x[:c.start()].split()) <= 8 and x[c.end():].strip(): st['name'], st['t'] = clean(x[:c.start()]), clean(x[c.end():])
                    elif st['s']: st['t'] = x
                    else: st['name'] = x
            if not st['name'] and not st['t'] and st['s']: st['t'], st['s'] = st['s'], ''
            if st['name'] and not st['st'] and SNAME.match(st['name']) and st['t']: st['st'], st['name'] = st['name'], ''   # «— العصف الذهني:» names a strategy
            if not (st['t'] or st['name']): return None
    return segs

# ---------------------------------------------------------------- one sentence per step
SUBJ = r'(?:(?:ال)?(?:معلم|طالب|طالبان|طالبة|طلبة|طلاب|تلميذ|تلاميذ|متعلم|مجموع|أزواج|زوج|زميل|فريق|ثنائي)|كل|أحد|بعض|جميع|الجميع)'
SNAME = re.compile(r'^(?:التعلم\s|العصف الذهني|الحوار والمناقشة|المناقشة|الاستقصاء|حل المشكلات|لعب الأدوار|تمثيل الأدوار|الخرائط الذهنية|فكر\s*[-–]\s*زاوج|التدريس التبادلي|الرؤوس المرقمة|Discovery|Collaborative|Cooperative|Game-based|Inquiry)', re.I)
def is_verb(w): return bool(re.match(r'^[يت][\u0600-\u06FF]{2,}[:：،,.]?$', w))
def put(v, who, rest):   # «يقرأ: …» → «يقرأ المعلم: …»
    c = v[-1] if v[-1] in ':：،,.' else ''
    return v[:len(v) - len(c)] + ' ' + who + c + (' ' + rest if rest else '')
def teacher_ar(t, fem):
    w = t.split(' ', 1)
    if len(w) > 1 and is_verb(w[0]) and not re.match(SUBJ, w[1]) and not w[0].rstrip(':：،,.').endswith(('ون', 'ان')):
        if w[0].startswith('ي') and not fem: return put(w[0], 'المعلم', w[1])
        if w[0].startswith('ت') and fem: return put(w[0], 'المعلمة', w[1])
    return t
def student_ar(s, kid):
    w = s.split(' ', 1); who = 'التلميذ' if kid else 'الطالب'
    if not w or not w[0]: return ''
    if is_verb(w[0]):
        v = w[0].rstrip(':：،,.')
        if v.endswith(('ون', 'وا')): return 'و' + ('التلاميذ' if kid else 'الطلبة') + ' ' + s
        if len(w) > 1 and re.match(SUBJ, w[1]): return 'و' + s
        if w[0].startswith('ت'): return 'و' + s
        return 'و' + put(w[0], who, w[1] if len(w) > 1 else '')
    if s.startswith('ال') and len(w) > 1: return 'ويقوم ' + who + ' ب' + s   # «التسميع والتصحيح» → «ويقوم التلميذ بالتسميع والتصحيح»
    return 'و' + who + ': ' + s
def lower1(s): return s[:1].lower() + s[1:] if s[:2] != s[:2].upper() or len(s) < 2 else s
def teacher_en(t):
    w = t.split(' ', 1)
    if re.match(r'^[A-Z][a-z]+s$', w[0]): return 'The teacher ' + w[0].lower() + (' ' + w[1] if len(w) > 1 else '')
    return t
def student_en(s, kid):
    w = s.split(' ', 1)
    if re.match(r'^[A-Z][a-z]+[,.]?$', w[0]):
        sing = w[0].rstrip(',.').endswith('s') and not w[0].rstrip(',.').endswith('ss')
        who = ('the pupil' if kid else 'the student') if sing else ('pupils' if kid else 'students')
        return who + ' ' + w[0].lower() + (' ' + w[1] if len(w) > 1 else '')
    return s
def sentence(st, en, fem, kid):
    t, s, n = st['t'].rstrip('.؛;، '), st['s'].rstrip('.؛;، '), st['name'].rstrip('.:： ')
    if en:
        body = teacher_en(t) if t else ''
        if s: body = (body + '; ' if body else '') + student_en(s, kid)
    else:
        body = teacher_ar(t, fem) if t else ''
        if s: body = (body + (' ' if body.endswith(('؟', '?', '!')) else '، ') if body else '') + (student_ar(s, kid) if body else s)
    if n and body and not body.startswith(n): body = n + ': ' + body
    elif n and not body: body = n
    return body

def strat_items(v):
    if isinstance(v, list): v = '\n'.join(x for x in v if isinstance(x, str))
    if not isinstance(v, str): return []
    v = B.strip_html(v)
    out = []
    for x in re.split(r'\n|،|؛|;|\s-\s|•', v):
        x = re.sub(r'^\s*(?:[-•*]|[0-9٠-٩]+[.)-])\s*', '', x).strip(' .')
        x = re.sub(r'^(?:استراتيجيات\s+)?أخرى\s*[:：]\s*|^Other\s*[:：]\s*', '', x).strip(' .')
        if 2 < len(x) < 60 and x not in out and not re.match(r'^(?:الحصة|Period)\s', x): out.append(x)
    return out

def render_text(segs, en, fem, kid, strats):
    out, k = [], 0
    for si, sg in enumerate(segs):
        if len(segs) > 1 or sg['head'] and len(segs) > 1:
            tot = sum(x['min'] for x in sg['steps'])
            if en: out.append('Period %d%s — %s' % (si + 1, (': ' + sg['head']) if sg['head'] else '', 'lesson time %d minutes' % tot))
            else: out.append('الحصة %d%s — زمن الحصة %s' % (si + 1, (': ' + sg['head']) if sg['head'] else '', minutes(tot)))   # digits: twoshift.js finds the periods by them
        for i, st in enumerate(sg['steps'], 1):
            line = '%d. %s (%s)' % (i, sentence(st, en, fem, kid), minutes(st['min'], en))
            sv = st['st'] or (strats[k % len(strats)] if strats else ''); k += 1
            out.append(line + ('\n' + ('Strategies: ' if en else 'الاستراتيجيات: ') + sv.rstrip('.') + '.' if sv else ''))
    return '\n\n'.join(out)

ROW = 'margin:0;padding:8px 2px;border-bottom:1px dashed #d8d0bf;line-height:1.9'
def render_html(text):
    """the html copy of a text in this style (same lines; period headings in red, strategies muted)"""
    ps = []
    for b in [x for x in text.split('\n\n') if x.strip()]:
        ls = b.split('\n')
        if re.match(r'^(?:الحصة|Period)\s', ls[0]) and not re.match(r'^[0-9٠-٩]+\.\s', ls[0]):
            ps.append('<p class="phead" style="margin:10px 0 2px;color:#c0392b;font-weight:700">%s</p>' % H.escape(ls[0])); ls = ls[1:]
            if not ls: continue
        m = re.match(r'^([0-9٠-٩]+\.)\s*(.*)$', ls[0])
        first = ('<b>%s</b> %s' % (H.escape(m.group(1)), H.escape(m.group(2)))) if m else H.escape(ls[0])
        rest = ''.join('<br><span style="opacity:.8">%s</span>' % H.escape(x) for x in ls[1:])
        ps.append('<p class="pstep" style="%s">%s%s</p>' % (ROW, first, rest))
    return '<div class="plist">' + ''.join(ps) + '</div>'

# ---------------------------------------------------------------- pages
def is_new(t): return bool(re.search(r'^[0-9٠-٩]+\.\s.*\((?:[0-9٠-٩]+) (?:دقيقة|دقيقتان|دقائق|minutes?)\)\s*$', t, re.M)) and \
    not re.search(r'^\s*[-•]?\s*(?:' + TEACH + r'|' + STUD + r')\s*[:：]', t, re.M | re.I)

def convert(text, en, fem, kid, strats):
    if not isinstance(text, str) or len(text) < 40 or is_new(text) or (text.lstrip().startswith('<') and is_new(B.strip_html(text))): return None
    segs = parse(B.strip_html(text) if text.lstrip().startswith('<') else text)
    if not segs or sum(len(s['steps']) for s in segs) < 2: return None
    return render_text(segs, en, fem, kid, strats)

def flavour(gs, sample):
    en = gs.endswith('/english')
    fem = bool(re.search(r'المعلمة\s*[:：]', sample))
    kid = gs.split('/')[0] in ('1', '2', '3', '4')
    return en, fem, kid

def strategies_of(cont, lits_strat):
    if isinstance(cont, dict):
        for k, v in cont.items():
            if re.search(r'استراتيج|strateg', str(k), re.I): return strat_items(v)
    return lits_strat.get(id(cont), [])

# ---------------------------------------------------------------- a period is 40 minutes (owner, 2026-10-27)
TEND = re.compile(r'\((' + D + r') (دقيقة|دقيقتان|دقائق|minutes?)\)\s*$')
def scale_to(ds, T):
    tot = sum(ds) or 1; raw = [x * T / tot for x in ds]; r = [max(1, int(x)) for x in raw]; left = T - sum(r)
    order = sorted(range(len(ds)), key=lambda i: -(raw[i] - int(raw[i])))
    k = 0
    while left > 0: r[order[k % len(order)]] += 1; left -= 1; k += 1
    while left < 0: j = r.index(max(r)); r[j] -= 1; left += 1
    return r
def fix_times(text, T):
    """the steps of each period in a text of this style made to add up to T minutes (their proportions kept)"""
    blocks = text.split('\n\n'); segs = [[]]
    for i, b in enumerate(blocks):
        if re.match(r'^(?:الحصة|Period)\s', b) and not re.match(r'^[0-9٠-٩]+\.\s', b): segs.append([i])
        else: segs[-1].append(i)
    changed = False
    for sg in segs:
        st = [(i, TEND.search(blocks[i].split('\n')[0])) for i in sg if re.match(r'^[0-9٠-٩]+\.\s', blocks[i])]
        st = [(i, m) for i, m in st if m]
        if len(st) < 2: continue
        ds = [toN(m.group(1)) for i, m in st]; tot = sum(ds)
        if tot == T or not (T * 0.55 <= tot <= T * 1.3): continue   # 22–52: an author's slip or a dropped step; 20 is a part of a period (grade 6)
        new = scale_to(ds, T); en = bool(re.search(r'minute', st[0][1].group(2)))
        for (i, m), d in zip(st, new):
            ls = blocks[i].split('\n'); ls[0] = ls[0][:m.start()] + '(' + minutes(d, en) + ')'; blocks[i] = '\n'.join(ls)
        if sg and re.match(r'^(?:الحصة|Period)\s', blocks[sg[0]]):
            blocks[sg[0]] = re.sub(r'(زمن الحصة|lesson time) ' + D + r' (?:دقيقة|دقائق|minutes)', lambda mm: mm.group(1) + ' ' + (('%d minutes' % T) if mm.group(1) == 'lesson time' else minutes(T)), blocks[sg[0]])
        changed = True
    return '\n\n'.join(blocks) if changed else None

# ---------------------------------------------------------------- no group contest in the preps (owner, 2026-10-27)
# «مسابقة المجموعات» needs a file not every teacher has, and the same closing step in every period is a pattern to avoid:
# a step that is only the contest goes (its minutes go to the other steps); a closing step that also does the final
# assessment keeps that part.
CONTEST = re.compile(r'مسابقة|المسابقة|سباق المجموعات|كاهوت|Kahoot|group quiz|group contest', re.I)
COMPETE = re.compile(r'تتنافس|يتنافس|متنافس|التنافس|الفائز|الفائزة|مخطط النقاط|صاحبة الدور|جولة|نقاط المجموعات|للنقاط|compete|winning team', re.I)
def _strip_contest(body):
    names, rest = [], body
    while True:
        m = re.match(r'^([^:،؟?]{2,45}?)\s*[:：]\s+(.*)$', rest)
        if not m or is_verb(m.group(1).split(' ')[0]): break
        names.append(m.group(1)); rest = m.group(2)
    names = [re.sub(r'\s+', ' ', re.sub(r'\(?ختام الحصة\)?|و?(?:ال)?مسابقة(?: المجموعات)?(?: التفاعلية)?(?: الختامية)?', '', n)).strip(' و،-–') for n in names]
    names = [n for n in names if n]
    parts = [x.strip() for x in re.split(r'،\s*|؛\s*|\s+ثم\s+', rest) if x.strip()]
    keep = [x for x in parts if not CONTEST.search(x) and not COMPETE.search(x)]
    if not keep: return None
    first = re.sub(r'^(?:ثم|و)\s*', '', keep[0])
    if first.startswith('و') and is_verb(first[1:].split(' ')[0]): first = first[1:]
    first = teacher_ar(first, False) if is_verb(first.split(' ')[0]) and first.split(' ')[0].startswith('ي') else first
    text = '، '.join([first] + keep[1:])
    if len(re.sub(r'^\S+\s+\S+\s*', '', text)) < 12: return None      # nothing left but a verb and its subject
    return (names[0] + ': ' if names else '') + text
def drop_contest(text):
    if not CONTEST.search(text): return None
    blocks = text.split('\n\n'); out = []; changed = False
    for b in blocks:
        ls = b.split('\n'); m = re.match(r'^([0-9٠-٩]+\.)\s*(.*?)\s*(\([^()]*\))\s*$', ls[0])
        if not m or not CONTEST.search(ls[0]): out.append(b); continue
        changed = True
        body = _strip_contest(m.group(2))
        if body is None: continue                                   # the step was only the contest
        out.append('\n'.join([m.group(1) + ' ' + body + ' ' + m.group(3)] + [x for x in ls[1:] if not CONTEST.search(x)]))
    if not changed: return None
    k = 0; res = []                                                  # renumber within each period
    for b in out:
        if re.match(r'^(?:الحصة|Period)\s', b) and not re.match(r'^[0-9٠-٩]+\.\s', b): k = 0; res.append(b); continue
        mm = re.match(r'^[0-9٠-٩]+\.', b)
        if mm: k += 1; b = '%d.' % k + b[mm.end():]
        res.append(b)
    return '\n\n'.join(res)

# ---------------------------------------------------------------- the warm-up field in the same style
WROLE = re.compile(r'^\s*(?:[-•–*]\s*)?(' + TEACH + r'|' + STUD + r'|' + STRAT + r')\s*[:：]\s*(.*)$', re.I)
def warm_convert(text, en, fem, kid):
    """«- المعلم: … / - الطالب: …» → one sentence «يعرض المعلم …، ويتأمل الطالب …» (other lines kept), per period"""
    if not isinstance(text, str) or not re.search(r'^\s*[-•–*]?\s*(?:' + TEACH + r'|' + STUD + r')\s*[:：]', text, re.M | re.I): return None
    out, cur, loose = [], None, []
    def flush():
        nonlocal cur, loose
        if cur and (cur['t'] or cur['s']):
            if not cur['t'] and loose: cur['t'] = clean(' '.join(loose)); loose = []
            out.extend(loose); loose = []
            tm = ''
            if cur['hx']:
                m = re.search(r'\((' + D + r')\s*' + UNIT + r'\)', cur['hx'])
                if m: tm = ' (' + minutes(toN(m.group(1)), en) + ')'
            line = sentence({'t': cur['t'], 's': cur['s'], 'name': ''}, en, fem, kid).rstrip('.؛، ') + tm + ('' if tm else '.')
            out.append(line + ('\n' + ('Strategies: ' if en else 'الاستراتيجيات: ') + cur['st'].rstrip('.') + '.' if cur['st'] else ''))
        else: out.extend(loose); loose = []
        cur = None
    for raw in text.replace('\r', '').split('\n'):
        l = raw.strip()
        if not l: continue
        m = WROLE.match(l)
        if m:
            if cur is None: cur = {'t': '', 's': '', 'st': '', 'hx': ''}
            lab, val = m.group(1), clean(m.group(2))
            if re.match(STRAT, lab, re.I): cur['st'] = val
            elif re.match(TEACH, lab, re.I):
                if cur['t'] or cur['s']: flush(); cur = {'t': '', 's': '', 'st': '', 'hx': ''}
                cur['t'] = val
            else: cur['s'] = (cur['s'] + ' ' + val).strip()
            continue
        if cur is not None and (cur['t'] or cur['s']): flush()
        if SEG.match(l):
            if out or loose: out.extend(loose); loose = []; out.append('')
            out.append(l); continue
        if re.match(r'^(?:التهيئة|التمهيد|Warm[- ]?up|Lead[- ]?in)[^:：]{0,40}[:：]\s*$', l, re.I) or re.match(r'^(?:التهيئة|التمهيد)\s*\(' + D, l):
            cur = {'t': '', 's': '', 'st': '', 'hx': l}; continue      # «التهيئة (5 دقائق):» heads the roles under it
        loose.append(l)
    flush(); out.extend(loose)
    res = '\n'.join(out).strip()
    return res if res and res != text.strip() else None

def fix_page(p, gs):
    h = open(p, encoding='utf8').read(); lits = B.literals(h)
    try: les, kmap = B.page_lessons(lits)
    except Exception: return 0, 0, h
    st_by = {}
    for name, i, e, o in lits:   # the period's strategies, for each field container of the period
        for path, x, anc in B.nodes(o):
            if isinstance(x, list) and len(x) >= 6 and all(isinstance(y, list) and len(y) in (2, 3) and isinstance(y[-2], str) for y in x):
                sv = next((y[-1] for y in x if re.search(r'استراتيج|Strateg', y[-2], re.I)), None)
                if sv is not None:
                    for y in x: st_by[id(y)] = strat_items(sv)
            elif isinstance(x, list) and 9 <= len(x) <= 11 and all(isinstance(y, (str, dict, list)) for y in x):
                st_by[id(x)] = strat_items(x[2] if isinstance(x[2], (str, list)) else x[2].get('t', '') if isinstance(x[2], dict) else '')
    before = [json.dumps(x[3], ensure_ascii=False) for x in lits]
    en, fem, kid = flavour(gs, h[:200000])
    done = skip = 0
    for li, cont, k in B.field_targets(lits, kmap, 'proc'):
        v = cont[k]; strats = strategies_of(cont, st_by)
        if isinstance(v, str):
            new = convert(v, en, fem, kid, strats)
            if new is None: skip += 1 if len(v) > 80 and not is_new(v) and not is_new(B.strip_html(v)) else 0; continue
            cont[k] = render_html(new) if v.lstrip().startswith('<') else new; done += 1
        elif isinstance(v, dict) and isinstance(v.get('t'), str) and isinstance(v.get('h'), str):
            new = convert(v['t'], en, fem, kid, strats)
            if new is None: skip += 1 if not is_new(v['t']) else 0; continue
            v['t'], v['h'] = new, render_html(new); done += 1
        elif isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v):
            new = convert(v[1], en, fem, kid, strats)
            if new is None: skip += 1 if not is_new(v[1]) else 0; continue
            v[0], v[1] = render_html(new), new; done += 1
    for li, cont, k in B.field_targets(lits, kmap, 'warm'):
        v = cont[k]
        if isinstance(v, str) and not v.lstrip().startswith('<'):
            new = warm_convert(v, en, fem, kid)
            if new: cont[k] = new; done += 1
        elif isinstance(v, dict) and isinstance(v.get('t'), str) and isinstance(v.get('h'), str):
            new = warm_convert(v['t'], en, fem, kid)
            if new: v['t'], v['h'] = new, ''.join('<p>%s</p>' % H.escape(x) for x in new.split('\n') if x.strip()); done += 1
        elif isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v):
            new = warm_convert(v[1], en, fem, kid)
            if new: v[0], v[1] = ''.join('<p>%s</p>' % H.escape(x) for x in new.split('\n') if x.strip()), new; done += 1
    T = 35 if '/prep35/' in p else 40
    def fx(x):
        nonlocal done
        if isinstance(x, str) and is_new(x):
            n0 = drop_contest(x); y = n0 or x
            n = fix_times(y, T) or n0
            if n: done += 1; return n
        return None
    for name, i, e, o in lits:
        for path, x, anc in list(B.nodes(o)):
            if isinstance(x, dict) and isinstance(x.get('procedures'), list) and x['procedures'] and all(isinstance(y, dict) and isinstance(y.get('min'), int) and isinstance(y.get('text'), str) for y in x['procedures']):
                pr = x['procedures']; new = []
                for y in pr:
                    if CONTEST.search(y['text']):
                        t2 = _strip_contest(y['text'])
                        if t2 is None: continue
                        y = dict(y, text=t2)
                    new.append(y)
                if new != pr and len(new) >= 2:
                    tot = sum(y['min'] for y in pr); ms = scale_to([y['min'] for y in new], tot)
                    x['procedures'] = [dict(y, min=mn) for y, mn in zip(new, ms)]; done += 1
            if isinstance(x, dict):
                for kk in list(x.keys()):
                    n = fx(x[kk])
                    if n:
                        x[kk] = n
                        if kk == 't' and isinstance(x.get('h'), str): x['h'] = render_html(n)
            elif isinstance(x, list):
                for j in range(len(x)):
                    n = fx(x[j])
                    if n:
                        x[j] = n
                        if len(x) == 2 and j == 1 and isinstance(x[0], str) and x[0].lstrip().startswith('<'): x[0] = render_html(n)
    # parallel html / plain (or h / t) lists of the procedures: redraw the html from the converted text
    for name, i, e, o in lits:
        for path, x, anc in B.nodes(o):
            if not isinstance(x, dict): continue
            for a, b in (('html', 'plain'), ('h', 't'), ('html', 'txt'), ('html', 'text')):
                if isinstance(x.get(a), list) and isinstance(x.get(b), list) and len(x[a]) == len(x[b]):
                    for j, t in enumerate(x[b]):
                        if isinstance(t, str) and is_new(t) and isinstance(x[a][j], str) and x[a][j] != render_html(t) and \
                           ('class="plist"' in x[a][j] or B.strip_html(x[a][j]).count('(') < t.count('(') or '<table' in x[a][j]):
                            x[a][j] = render_html(t)
    t = h
    for (name, i, e, o), b0 in sorted(zip(lits, before), key=lambda z: -z[0][1]):
        if json.dumps(o, ensure_ascii=False) != b0:
            compact = '", "' not in h[i:i + 3000] and '":"' in h[i:i + 3000]
            t = t[:i] + json.dumps(o, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': ')).replace('</', '<\\/') + t[e:]
    return done, skip, t

# grades 2–4 math draw {min, text} lists themselves
JS_OLD = "if(k==='procedures'){let t=0;return s.procedures.map(p=>{const r='('+t+'–'+(t+p.min)+' د) '+p.text;t+=p.min;return r}).join('\\n')}"
JS_ITEMS_OLD = "if(k==='procedures'){let t=0;return s.procedures.map(p=>{const r={lab:t+'–'+(t+p.min),t:p.text,tm:1};t+=p.min;return r})}"
JS_ITEMS_NEW = ("if(k==='procedures'){const st=(s.strategies||[]).map(x=>String(x).replace(/^(?:استراتيجيات\\s+)?أخرى\\s*[:：]\\s*/,''));return s.procedures.map((p,i)=>({lab:String(i+1),t:p.text+' ('+p.min+' '"
                "+(p.min===1||p.min>10?'دقيقة':p.min===2?'دقيقتان':'دقائق')+')'+(st.length?' — الاستراتيجيات: '+(p.strategy||st[i%st.length]):'')}))}")
JS_NEW = ("if(k==='procedures'){const st=(s.strategies||[]).map(x=>String(x).replace(/^(?:استراتيجيات\\s+)?أخرى\\s*[:：]\\s*/,''));return s.procedures.map((p,i)=>(i+1)+'. '+p.text+' ('+p.min+' '"
          "+(p.min===1||p.min>10?'دقيقة':p.min===2?'دقيقتان':'دقائق')+')'+(st.length?'\\nالاستراتيجيات: '+(p.strategy||st[i%st.length])+'.':'')).join('\\n\\n')}")

def main(only=None):
    only = [a.strip('/') for a in (sys.argv[1:] if only is None else only)]
    pages = sorted(set(glob.glob(R + '[0-9]*/*/prep*/index.html') + glob.glob(R + '[0-9]*/*/prep/u*/index.html')))
    tot = tsk = 0
    for p in pages:
        rel = p[len(R):]; gs = '/'.join(rel.split('/')[:2])
        if only and gs not in only: continue
        done, skip, t = fix_page(p, gs)
        if JS_OLD in t: t = t.replace(JS_OLD, JS_NEW); done += 1
        if JS_ITEMS_OLD in t: t = t.replace(JS_ITEMS_OLD, JS_ITEMS_NEW)
        if t != open(p, encoding='utf8').read(): open(p, 'w', encoding='utf8').write(t)
        if done or skip: print('%-22s %4d converted %4d left' % (rel[:-11], done, skip))
        tot += done; tsk += skip
    print('done', tot, 'converted,', tsk, 'not understood')

if __name__ == '__main__': main()
