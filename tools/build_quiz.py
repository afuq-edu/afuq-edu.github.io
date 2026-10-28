#!/usr/bin/env python3
"""Lesson games + activity («ألعاب ونشاط الدرس») built from the prep pages (*/*/prep[/uN]/index.html).

For every subject with a prep page:
  * reads each lesson's formative/summative questions and model answers out of the page's JSON data,
  * writes afuq-edu/afuq q/<grade>/<subject>/index.html (data inline; shared engine q/engine.js + q/engine.css from tools/quiz/),
    opened by students at https://afuq-edu.github.io/afuq/q/<grade>/<subject>/?l=<lesson number> (open, no subscription),
  * appends that lesson's permanent link as a new last line of the field «ملاحظات ضمن خطة الدراسة الأسبوعية» of every period
    (the existing notes are kept; rerunning replaces only the link line), and makes it clickable via /assets/qlink.js,
  * renames the question levels دعم / متوقع / متقدم to معرفة / تطبيق / استدلال (Support/Expected/Advanced → Knowledge/Application/Reasoning).
Usage: python3 tools/build_quiz.py [grade/subject ...]   (default: all).  Rerun after adding or replacing a prep page,
then push the files repo first and wait for its deploy before pushing this repo."""
import re, os, sys, json, html, glob, collections
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
FILES = os.environ.get('AFUQ_FILES', '/home/user/afuq').rstrip('/') + '/'
BASE = 'https://afuq-edu.github.io/afuq/q/'
LINE = '🎮 رابط ألعاب ونشاط الدرس التفاعلي للطالب: '
GRADE = {1:'الأول',2:'الثاني',3:'الثالث',4:'الرابع',5:'الخامس',6:'السادس',7:'السابع',8:'الثامن',9:'التاسع',10:'العاشر',11:'الحادي عشر',12:'الثاني عشر'}
DEC = json.JSONDecoder()

# ---------------------------------------------------------------- page data
def literals(s):
    """JSON data literals in a page: [name, start, end, obj]; start/end span exactly the JSON text."""
    out = []
    for m in re.finditer(r'<script[^>]*type="application/json"[^>]*>', s):
        i = m.end()
        while s[i].isspace(): i += 1
        try: o, e = DEC.raw_decode(s, i); out.append(['#json', i, e, o])
        except Exception: pass
    for m in re.finditer(r'(?:(?:const|var|let)\s+|,\s*)([A-Za-z_$][\w$]*)\s*=\s*(?:\(window\.AFUQ35\|\|function\(x\)\{return x\}\)\()?(?=[\[{"])', s):
        i = m.end()
        try: o, e = DEC.raw_decode(s, i)
        except Exception: continue
        if isinstance(o, (list, dict)) and e - i > 200: out.append([m.group(1), i, e, o])
    return out

def nodes(o, path=(), anc=()):
    yield path, o, anc
    if isinstance(o, dict):
        for k, v in o.items(): yield from nodes(v, path + (k,), anc + ((path, o),))
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from nodes(v, path + (i,), anc + ((path, o),))

PK = {'periods','p','per','ps','sep','sessions','fields','f','F','T','h','t','items','qs','formative','summative','fa','sa',
      'merged','comb','combined','c','C','html','txt','plain','html2'}
def lesson_key(path, anc, root, pid):
    """(key, lesson object or None) of the lesson a value at `path` belongs to."""
    for j in range(len(path) - 1):
        if path[j] in ('lessons', 'periods') and isinstance(path[j + 1], str):
            if path[j] == 'periods' and path[j + 1] in pid: return pid[path[j + 1]]
            obj = root
            for x in path[1:j + 2]: obj = obj[x]
            return ('K', path[j + 1].split('.')[0]), (obj if path[j] == 'lessons' else None)
    for j in range(len(anc) - 1, -1, -1):
        p, o = anc[j]
        if isinstance(o, dict) and p and isinstance(p[-1], int):
            parent = next((x for x in reversed(p[:-1]) if not isinstance(x, int)), None)
            if parent in PK: continue
            return p, o
    return None, None

# ---------------------------------------------------------------- questions
LVPAT = [(r'دعم|Support|معرفة|Knowledge|سهل', 0), (r'متوقع|Expected|تطبيق|Application|متوسط', 1),
         (r'متقدم|Advanced|استدلال|Reasoning|تحليل|صعب|إثرائي', 2)]
def level(t):
    for pat, i in LVPAT:
        if re.search(pat, t, re.I): return i
    return -1
ANS = re.compile(r'^\s*(?:[-–•*]\s*)?(?:الإجابة النموذجية|الإجابة المتوقعة|الإجابة الصحيحة|الإجابة|الجواب|Model answer|Suggested answer|'
                 r'Expected answer|Possible answer|Sample answer|Answer|Ans\.?)\s*[:：]\s*', re.I | re.M)
QSTART = re.compile(r'\s*(?:س\s*[\d٠-٩]+|Q\s*\d+|Question\s*\d+|[\d٠-٩]+\s*[).\-–]|[(\[](?:ال)?مستوى|[(\[](?:Support|Expected|Advanced))', re.I)
HDR = re.compile(r'^\s*(?:الحصة|Period|Lesson|الدرس)\s*[\d٠-٩]+.*?[:：]\s*$|^\s*(?:الحصة|Period)\s*[\d٠-٩]+\s*[:：].*$|^\s*تفريد التعليم\s*[:：]?\s*$', re.M)   # tools/form_heading.py
def strip_html(s):
    if '<' not in s: return s
    s = re.sub(r'<br\s*/?>|</(?:li|p|div|tr)>', '\n', s)
    s = re.sub(r'<span class="tier[^"]*">([^<]*)</span>', r'[\1] ', s)
    s = re.sub(r'<div class="ans">', '\n', s)
    return html.unescape(re.sub(r'<[^>]+>', '', s))
def parse(text):
    """[(question, answer, level)] from one assessment text."""
    t = strip_html(text).replace('\r', '')
    t = re.sub(r'\s*[—–]\s*(?=(?:الإجابة|Model answer|Answer)\s*(?:النموذجية\s*)?[:：])', '\n', t)
    t = re.sub(r'(?<=[.؟?!)])[ \t]+(?=(?:الإجابة النموذجية|Model answer)\s*[:：])', '\n', t)
    out = []; ms = list(ANS.finditer(t)); prev = 0
    for k, m in enumerate(ms):
        qblock = t[prev:m.start()]
        end = ms[k + 1].start() if k + 1 < len(ms) else len(t)
        lines = t[m.end():end].split('\n'); a = lines[0]; used = len(lines[0]) + 1
        for ln in lines[1:]:
            if not ln.strip() or QSTART.match(ln): break
            a += ' ' + ln.strip(); used += len(ln) + 1
        prev = m.end() + min(used, end - m.end())
        ql = [x for x in qblock.split('\n') if x.strip() and not HDR.match(x)]
        if not ql: continue
        st = 0
        for i, x in enumerate(ql):
            if QSTART.match(x): st = i
        q = ' '.join(x.strip() for x in ql[st:]); lv = -1
        q = re.sub(r'^\s*(?:س|Q|Question\s*)\s*[\d٠-٩]+\s*(?=[(\[:：.)\-–\s])[:：.)\-–]?\s*|^\s*[\d٠-٩]+\s*[).\-–]\s*', '', q, flags=re.I)
        m2 = re.match(r'\s*[(\[]\s*([^)\]]{1,30})\s*[)\]]\s*[:：.\-–]?\s*', q)
        if m2 and level(m2.group(1)) >= 0: lv = level(m2.group(1)); q = q[m2.end():]
        q = re.sub(r'^\s*(?:السؤال|Question)\s*[:：]\s*', '', q.strip())
        out.append((q.strip(), a.strip(), lv))
    return out

OPEN_A = re.compile(r'^\s*(?:e\.\s?g\.|Example|Model\s*:|For example|Possible|مثل\s*:|مثال|مثلًا|مثلا|نحو\s*:|Open|Any\b|Various|Answers? (?:will )?vary|'
                    r'Own\b|Pupils|Pupil.s own|Students?\b|Student.s|Learners?|The pupil|إجابات|إجابة\s|أي إجابة|أي مثال|تقبل|يقبل|يُقبل|تُقبل|تتنوع|تختلف|حسب|متروك|مفتوح)', re.I)
DOER_A = re.compile(r'^\s*(?:يذكر|تذكر|يؤدي|يؤديه|يؤدّي|تؤدي|يقرأ|تقرأ|يتلو|يسمّع|يسمع|يرسم|ترسم|يلون|يلوّن|ينفذ|ينفّذ|يعبر|يعبّر|يجيب|ينطق|يقف|يرفع|يمثل|يمثّل|يكتب|يصمم|يصمّم)(?=[\s.،]|$)'
                    r'|^\s*\S+\s+(?:الطالب|التلميذ|المتعلم|الطلبة|التلاميذ|الطالبة)\b'
                    r'|^\s*(?:تلاوة|قراءة|تسميع|إنشاد|أداء|رسم|كتابة|تمثيل|بطاقة|فقرة|جملة|عمل|تصميم|نطق|إنتاج)\s[^.]{0,40}(?:صحيح|سليم|جيد|مناسب|متقن)')
PERF_Q = re.compile(r'^\s*(?:صوّب|صوب|اركض|اقفز|ارمِ|ارم\s|مرّر|مرر|اجرِ|اجر\s|نطّ|تمرّن|حاور|ناقش|اقرأ|اقرئي|سمّع|سمِّع|سمع|اتلُ|اتل|أنشد|أدِّ|أدّ|أد\s|نفّذ|نفذ|مثّل|لوّن|لون|ارسم|ارسمي|صمّم|صمم|قف|اعرض|طبّق عمليًا|'
                    r'Sing|Clap|Mime|Act\b|Show|Wave|Touch|Draw|Colou?r|Trace|Ask\b|Tell me|Do the|Point to|Read aloud|Talk|Role.?play)', re.I)
WRITE_Q = re.compile(r'^\s*(?:اكتب جملة|اكتب جملتين|اكتب فقرة|اكتب نصًا|اكتب رسالة|اكتب قصة|عبّر بجملة|Write (?:a|an|one|two|three|your|about|sentences)|'
                     r'Make (?:a|two|three) sentence|Describe your|Say (?:a|two|three|one)|Say something)', re.I)
VIS_Q = re.compile(r'الصورة|صورة|البطاقة|بطاقة|المعروض|المعروضة|السبورة|المجسم|المرسوم|الشكل المقابل|الشكل التالي|الجدول المقابل|اللوحة|الفيديو|'
                   r'picture|photo|flashcard|Pointing|Hold(?:s|ing)? up|this\?$|these\?$', re.I)
def clean_a(a):
    a = re.sub(r'^\s*(?:\(?[أبجده]\)|[أبجد][.)-])\s*', '', a)
    a = re.sub(r'^\s*\(?[a-dA-D]\)\s+', '', a)
    return a.strip().rstrip('.').strip()
TFQ = re.compile(r'صواب أم خطأ|صح أم خطأ|\(صح\)\s*أو\s*\(خطأ\)|صح أو خطأ|ضع علامة|True or False|True/False|Right or wrong', re.I)
TFA = re.compile(r'^\s*\(?(صح|صحيح|صحيحة|صواب|خطأ|خاطئة|خاطئ|True|False)\)?(?![\w\u0600-\u06FF])', re.I)
def item(q, a, lv):
    """[q, a, lv, extra] for the games, or None when the question cannot be checked by choosing (performance, open, visual)."""
    q = re.sub(r'\s+', ' ', q).strip(); a = re.sub(r'\s+', ' ', a).strip()
    if not a or len(q) < 6 or len(q) > 260: return None
    if OPEN_A.match(a) or DOER_A.match(a) or PERF_Q.match(q) or WRITE_Q.match(q) or VIS_Q.search(q): return None
    if re.fullmatch(r'\s*ي[\u0600-\u06FF]{2,}[.،]?\s*', a): return None   # a bare verb («يصوب»): a performance, not an answer
    m = TFA.match(a)
    if m and (TFQ.search(q) or len(a) < 60):
        w = m.group(1); en = w.lower() in ('true', 'false')
        v = (w.lower() == 'true') if en else w.startswith(('صح', 'صواب'))
        q = re.sub(r'^\s*(?:ضع كلمة\s*\(صح\)\s*أو\s*\(خطأ\)\s*[:：]?|(?:صح|صواب) أم خطأ\s*[:：؟?]?|True or False\s*[:：?]?|True/False\s*[:：]?)\s*', '', q, flags=re.I)
        return [q, ('True' if v else 'False') if en else ('صح' if v else 'خطأ'), lv, 1]
    a = clean_a(a)
    if not a or len(a) > 150: return None
    opts = None
    m = re.search(r'\(\s*أ\s*\)(.+?)\(\s*ب\s*\)(.+?)(?:\(\s*ج\s*\)(.+?))?(?:\(\s*د\s*\)(.+?))?$', q)
    if m:
        o = [x.strip(' ،,؟?') for x in m.groups() if x and x.strip()]
        if any(norm(x) == norm(a) for x in o): opts = [x for x in o if norm(x) != norm(a)]; q = q[:m.start()].strip(' :：')
    if not opts:
        m = re.search(r'[(:：]\s*(?:Choose\s*:?\s*|اختر\s*:?\s*)?([^()]{2,140}?/[^()]{2,140}?)\)?\s*[؟?.]?$', q)
        if m:
            o = [x.strip(' ،,؟?.') for x in m.group(1).split('/')]
            if 2 <= len(o) <= 5 and any(norm(x) == norm(a) for x in o):
                opts = [x for x in o if norm(x) != norm(a)]
                q = (q[:m.start()] + ('؟' if '؟' in q[m.start():] else '?' if '?' in q[m.start():] else '')).strip(' :：')
    return [q, a, lv] + ([opts] if opts else [])
def norm(s): return re.sub(r'[\W_]+', '', s.lower())[:80]

TK = ['title', 'label', 'lessonTitle', 'name', 't', 'ti', 'lesson', 'les', 'head', 'topic']
def title_of(o):
    for k in TK:
        if isinstance(o.get(k), str) and 1 < len(o[k]) < 160: return o[k]
    return ''
def unit_of(o):
    u = o.get('unit') or o.get('u') or o.get('unitName') or ''
    if isinstance(u, dict): u = u.get('t') or u.get('name') or u.get('title') or ''
    return u if isinstance(u, str) else ''

def page_lessons(lits):
    """[{'title','unit','items','keys'}] in page order, plus {group key: lesson index}."""
    groups = collections.OrderedDict()
    for lit in lits:
        n, _, _, o = lit; pid = {}
        for p, v, anc in nodes(o, (n,)):
            if isinstance(v, dict) and isinstance(v.get('pids'), list):
                for x in v['pids']: pid[x] = (p, v)
        for p, v, anc in nodes(o, (n,)):
            if isinstance(v, str): its = parse(v)
            elif isinstance(v, dict) and isinstance(v.get('q'), str) and isinstance(v.get('a'), str):
                its = [(v['q'], v['a'], level(str(v.get('level', v.get('lvl', '')))))]
            else: continue
            if not its: continue
            key, lo = lesson_key(p, anc, o, pid)
            key = (n,) + (key if isinstance(key, tuple) else (key,))
            g = groups.setdefault(key, {'title': '', 'unit': '', 'items': [], 'seen': set()})
            if lo is not None and not g['title']: g['title'] = title_of(lo); g['unit'] = unit_of(lo)
            for q, a, lv in its:
                k = norm(q)
                if k and k not in g['seen']: g['seen'].add(k); g['items'].append((q, a, lv))
    out, kmap = [], {}
    for k, g in groups.items():
        if out and g['title'] and out[-1]['title'] == g['title'] and out[-1]['unit'] == g['unit']:
            seen = {norm(x[0]) for x in out[-1]['items']}
            out[-1]['items'] += [x for x in g['items'] if norm(x[0]) not in seen]; kmap[k] = len(out) - 1; continue
        if not g['title'] and out and not g['items']: kmap[k] = len(out) - 1; continue
        kmap[k] = len(out); out.append({'title': g['title'] or g['unit'] or ('الدرس %d' % (len(out) + 1)), 'unit': g['unit'], 'items': g['items']})
    return out, kmap

# ---------------------------------------------------------------- notes field
NOTE_AR = 'ملاحظات ضمن خطة الدراسة الأسبوعية'
FIELD = {   # which field: (label pattern, data keys, position in the standard 10-field Noor list)
    'notes': (r'ملاحظات|Notes|Weekly', {NOTE_AR, 'notes', 'note', 'nt', 'notesWeekly', 'weekly'}, 9),
    'out': (r'المخرجات التعليمية|نواتج التعلم|Learning Outcomes|^Outcomes', {'المخرجات التعليمية', 'outcomes', 'out', 'lo'}, 0)}
def field_names(lits, which):
    """How this page names a field: (index in its field list, list length, data keys)."""
    pat, keys, _ = FIELD[which]; idx, nlen, keys = None, None, set(keys)
    for _, _, _, o in lits:
        for p, v, anc in nodes(o):
            if isinstance(v, list) and 6 <= len(v) <= 14:
                labels = [str(x) if not isinstance(x, (list, dict)) else x for x in v]
                labels = [x if isinstance(x, str) else (x[1] if isinstance(x, list) and len(x) == 2 and isinstance(x[1], str) else (x.get('label') or x.get('name') or x.get('t') or '' if isinstance(x, dict) else '')) for x in labels]
                labels = [l if isinstance(l, str) else '' for l in labels]
                if max(len(l) for l in labels) > 70: continue   # field names are short; a period's field values are not
                if any(re.search(pat, l) for l in labels) and any(re.search(r'الختامي|Summative', l) for l in labels):
                    i = next(i for i, l in enumerate(labels) if re.search(pat, l))
                    idx = i; nlen = len(v); x = v[i]
                    if isinstance(x, list): keys.add(x[0])
                    if isinstance(x, dict):
                        for kk in ('key', 'k', 'id'):
                            if isinstance(x.get(kk), str): keys.add(x[kk])
            if isinstance(v, dict) and len(v) >= 8 and all(isinstance(x, str) and len(x) <= 70 for x in v.values()):
                if any(re.search(r'الختامي|Summative', x) for x in v.values()):
                    for k2, l in v.items():
                        if re.search(pat, l): keys.add(k2)
    return idx, nlen, keys

LABEL = re.compile(r'^\s*(?:ملاحظات|Notes|الواجب المنزلي)')
def with_link(text, url):
    """The notes text with the lesson link as its new last line (an older link line is replaced; nothing else changes)."""
    if re.search(r'<br\s*/?>|</(?:p|div|li)>', text):
        t = re.sub(r'(?:<p>[^<]*/afuq/q/[^<]*</p>|(?:<br\s*/?>\s*)*[^<>]*/afuq/q/[^<]*)$', '', text.rstrip()).rstrip()
        return t + ('<p>%s%s</p>' % (LINE, url) if t.endswith('</p>') else '<br>' + LINE + url)
    t = '\n'.join(l for l in text.split('\n') if '/afuq/q/' not in l).rstrip()
    return (t + '\n' if t else '') + LINE + url
def link_value(v, url):
    """Add the link inside one notes value: a string, an {h,t}-style dict, a [html, text] pair or a [n, label, text] triple."""
    if isinstance(v, str): return with_link(v, url) if not LABEL.match(v) else v
    if isinstance(v, list): return [link_value(x, url) for x in v]
    if isinstance(v, dict): return {k: (link_value(x, url) if isinstance(x, (str, list)) else x) for k, x in v.items()}
    return v

def fieldish(x):
    """One field value: text, an {h,t}-style dict of texts, or a short list of texts/numbers (not a period or a lesson)."""
    if isinstance(x, str): return True
    if isinstance(x, dict): return len(x) <= 4 and all(isinstance(y, str) for y in x.values())
    if isinstance(x, list): return len(x) <= 4 and all(isinstance(y, (str, int)) for y in x)
    return False

def field_targets(lits, kmap, which):
    """Every value of one field (per period and merged): yields (lesson index or None, container, key)."""
    idx, nlen, keys = field_names(lits, which); pat, _, std = FIELD[which]
    for lit in lits:
        n, _, _, o = lit; pid = {}
        for p, v, anc in nodes(o, (n,)):
            if isinstance(v, dict) and isinstance(v.get('pids'), list):
                for x in v['pids']: pid[x] = (p, v)
        ten = idx is None and any(isinstance(v, list) and len(v) == 10 and all(isinstance(x, str) for x in v) and parse(v[7] + '\n' + v[8])
                                  for p, v, anc in nodes(o, (n,)))
        targets = []
        for p, v, anc in nodes(o, (n,)):
            if not isinstance(v, (list, dict)): continue
            if isinstance(v, list) and idx is not None and len(v) == nlen and all(fieldish(x) for x in v) \
               and not any(isinstance(x, str) and (x == NOTE_AR or x == 'المخرجات التعليمية') for x in v):
                x = v[idx]
                if isinstance(x, (str, list, dict)) and not (isinstance(x, str) and LABEL.match(x)): targets.append((p, v, idx, anc))
            elif isinstance(v, list) and ten and len(v) == 10 and all(isinstance(x, str) for x in v) and len(v[std]) > 20:
                targets.append((p, v, std, anc))
            elif isinstance(v, list) and len(v) >= 6 and all(isinstance(x, list) and len(x) in (2, 3) and isinstance(x[len(x) - 2], str) for x in v):
                labs = [x[len(x) - 2] for x in v]   # [[label, value], ...] or [[n, label, value], ...] (notes: or homework when there is none)
                k = next((i for i, l in enumerate(labs) if re.search(pat, l)), None)
                if k is None and which == 'notes': k = next((i for i, l in enumerate(labs) if re.match(r'الواجب', l)), None)
                if k is not None and isinstance(v[k][-1], str): targets.append((p + (k,), v[k], len(v[k]) - 1, anc + ((p, v),)))
            elif isinstance(v, dict):
                for k in keys:
                    if isinstance(v.get(k), (str, list)) and len(v[k]) > (20 if isinstance(v[k], str) else 0): targets.append((p, v, k, anc))
        for p, cont, k, anc in targets:
            key, _ = lesson_key(p + (k,), anc + ((p, cont),), o, pid)
            key = (n,) + (key if isinstance(key, tuple) else (key,))
            yield kmap.get(key), cont, k

def unlink(v):
    """v without any lesson-link line (anywhere in the data)."""
    if isinstance(v, str):
        if '/afuq/q/' not in v: return v
        v = re.sub(r'<p>[^<]*/afuq/q/[^<]*</p>|(?:<br\s*/?>\s*)+[^<>]*/afuq/q/[^<\n]*', '', v)
        return '\n'.join(l for l in v.split('\n') if '/afuq/q/' not in l).rstrip()
    if isinstance(v, list):
        for i in range(len(v)): v[i] = unlink(v[i])
    elif isinstance(v, dict):
        for k in v: v[k] = unlink(v[k])
    return v

def add_links(lits, kmap, urls):
    """Append the lesson link to every notes value (per period and merged). Returns (changed count, unmatched count)."""
    for lit in lits: lit[3] = unlink(lit[3])
    done = miss = 0
    for li, cont, k in list(field_targets(lits, kmap, 'notes')):
        if li is None or urls[li] is None: miss += 1; continue
        new = link_value(cont[k], urls[li])
        if new != cont[k]: cont[k] = new
        done += 1
    return done, miss

def outcomes(lits, kmap, n):
    """Up to four learning outcomes per lesson (from its first period), for the students' start screen."""
    out = [None] * n
    for li, cont, k in field_targets(lits, kmap, 'out'):
        if li is None or li >= n or out[li]: continue
        v = cont[k]
        if isinstance(v, dict): v = v.get('t') or v.get('text') or next((x for x in v.values() if isinstance(x, str)), '')
        if isinstance(v, list): v = '\n'.join(x if isinstance(x, str) else (x.get('text') or x.get('t') or '' if isinstance(x, dict) else '') for x in v)
        if not isinstance(v, str): continue
        lines = []
        for l in strip_html(v).split('\n'):
            l = re.sub(r'^\s*(?:[-•*]|[\d٠-٩]+\s*[.)\-–]|مخرج(?: تعليمي)? آخر\s*[:：]|المخرج(?: الآخر| [\d٠-٩]+)?\s*[:：]|Other outcome\s*:)\s*', '', l).strip()
            if 8 <= len(l) <= 170 and not re.match(r'(?:المخرجات|Learning Outcomes|(?:الحصة|Period|Lesson|الدرس)\s*[\d٠-٩])', l): lines.append(l)
        if lines: out[li] = lines[:4]
    return out

# ---------------------------------------------------------------- level names
LEVEL_SUBS = [
    ('مستوى الدعم', 'مستوى المعرفة'), ('المستوى المتوقع', 'مستوى التطبيق'), ('المستوى المتقدم', 'مستوى الاستدلال'),
    ('مستوى متوقع', 'مستوى التطبيق'), ('مستوى متقدم', 'مستوى الاستدلال'), ('مستوى دعم', 'مستوى المعرفة'),
    ('مستوى المتوقع', 'مستوى التطبيق'), ('مستوى المتقدم', 'مستوى الاستدلال'),
    ('سؤال الدعم', 'سؤال المعرفة'), ('السؤال المتوقع', 'سؤال التطبيق'), ('السؤال المتقدم', 'سؤال الاستدلال'),
    ('التقويم الختامي المتقدم', 'التقويم الختامي (الاستدلال)'), ('أسئلة الدعم', 'أسئلة المعرفة'), ('الأسئلة المتقدمة', 'أسئلة الاستدلال'),
    ('Support level', 'Knowledge level'), ('Expected level', 'Application level'), ('Advanced level', 'Reasoning level'),
]
TOK = {'دعم': 'معرفة', 'متوقع': 'تطبيق', 'متقدم': 'استدلال', 'الدعم': 'المعرفة', 'المتوقع': 'التطبيق', 'المتقدم': 'الاستدلال'}
TOK_EN = {'Support': 'Knowledge', 'Expected': 'Application', 'Advanced': 'Reasoning'}
def rename_levels(s):
    for a, b in LEVEL_SUBS: s = s.replace(a, b)
    w = '|'.join(sorted(TOK, key=len, reverse=True))
    # bracketed / quoted / tagged level words: [دعم] (متوقع) "متقدم" 'دعم' >دعم< «دعم» and the chain دعم ← متوقع ← متقدم
    s = re.sub(r'(?:(?<=[\[("\'>«])|(?<=[،,] )|(?<=[،,]))\s*(%s)\s*(?=[\])"\'<»:،])' % w, lambda m: TOK[m.group(1)], s)
    s = re.sub(r'(?<![\w\u0600-\u06FF])(دعم|الدعم)(\s*[←→/–\-،,]\s*)(متوقع|المتوقع)(\s*[←→/–\-،,]\s*)(متقدم|المتقدم)(?![\w\u0600-\u06FF])',
               lambda m: TOK[m.group(1)] + m.group(2) + TOK[m.group(3)] + m.group(4) + TOK[m.group(5)], s)
    s = re.sub(r'(?<=[\[(])\s*(Support|Expected|Advanced)\s*(?=[\])])', lambda m: TOK_EN[m.group(1)], s)
    s = re.sub(r'\b(Support|Expected|Advanced)(\s*[→/–\-,]\s*)(Expected)(\s*[→/–\-,]\s*)(Advanced)\b',
               lambda m: 'Knowledge' + m.group(2) + 'Application' + m.group(4) + 'Reasoning', s)
    return s

# ---------------------------------------------------------------- pages
QLINK = '<script src="/assets/qlink.js" defer></script>'
def dump(o):
    return json.dumps(o, ensure_ascii=False).replace('</', '<\\/').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')

def subject_name(g, s):
    try:
        t = re.search(r'<title>([^<]*)', open('%s%s/%s/index.html' % (R, g, s), encoding='utf8').read()).group(1)
        n = re.sub(r'\s*الصف .*$', '', [x.strip() for x in t.split('–')][1]).strip()
        return {'علوم': 'العلوم', 'رياضيات': 'الرياضيات', 'أحياء': 'الأحياء', 'كيمياء': 'الكيمياء', 'فيزياء': 'الفيزياء', 'لغة عربية': 'اللغة العربية', 'تربية إسلامية': 'التربية الإسلامية'}.get(n, n) or s
    except Exception: pass
    return s

def stub(g, s, data):
    return ('<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '<title>ألعاب ونشاط الدرس – %s – الصف %s</title>\n<meta name="robots" content="noindex">\n'
            '<link rel="stylesheet" href="../../engine.css?v=%s"></head><body><div id="app"></div>\n'
            '<script>window.QZ=%s;</script>\n<script src="../../engine.js?v=%s"></script></body></html>\n'
            % (data['sn'], data['gn'], VER, dump(data), VER))

VER = '1'
def main():
    global VER
    only = [a.strip('/') for a in sys.argv[1:]]
    eng = open(R + 'tools/quiz/engine.js', encoding='utf8').read() + open(R + 'tools/quiz/engine.css', encoding='utf8').read()
    import hashlib; VER = hashlib.sha1(eng.encode()).hexdigest()[:8]
    pages = sorted(glob.glob(R + '[0-9]*/*/prep/index.html') + glob.glob(R + '[0-9]*/*/prep/u*/index.html') + glob.glob(R + '[0-9]*/*/prep[0-9]*/index.html'))
    subj = collections.OrderedDict()
    for f in pages:
        rel = f[len(R):]; g, s = rel.split('/')[:2]
        if only and '%s/%s' % (g, s) not in only: continue
        subj.setdefault((int(g), s), []).append(rel)
    report = []
    for (g, s), rels in sorted(subj.items()):
        rels.sort(key=lambda r: (not r.endswith('/prep/index.html'), not re.search(r'/prep/u\d', r), r))
        primary = [r for r in rels if re.search(r'/prep/(?:u\d+/)?index\.html$', r)]
        lessons, per_page = [], {}
        for rel in rels:
            src = open(R + rel, encoding='utf8').read(); lits = literals(src)
            pl, kmap = page_lessons(lits); per_page[rel] = (src, lits, pl, kmap)
            for L, o in zip(pl, outcomes(lits, kmap, len(pl))): L['out'] = o
            if rel in primary:
                for L in pl: L['page'] = rel; lessons.append(L)
        data_L, url_of = [], {}
        for i, L in enumerate(lessons):
            its, seen = [], set()
            for q, a, lv in L['items']:
                it = item(q, a, lv)
                if it and norm(it[0]) not in seen: seen.add(norm(it[0])); its.append(it)
            L['n'] = len(its)
            data_L.append(dict({'t': L['title'], 'u': L['unit'], 'q': its}, **({'o': L['out']} if L.get('out') else {})))
        data = {'g': str(g), 'gn': GRADE[g], 's': s, 'sn': subject_name(g, s), 'L': data_L}
        usable = sum(1 for L in data_L if L['q'])
        if not usable: report.append('%d/%s: no usable questions – skipped' % (g, s)); continue
        out = '%sq/%d/%s/index.html' % (FILES, g, s); os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf8').write(stub(g, s, data))
        # a lesson without its own usable questions still gets a link: the page borrows its unit neighbours' questions
        urls_all = ['%s%d/%s/?l=%d' % (BASE, g, s, i + 1) for i in range(len(data_L))]
        for rel in rels:
            src, lits, pl, kmap = per_page[rel]
            before = [dump(l[3]) for l in lits]
            if rel in primary:
                off = next((i for i, L in enumerate(lessons) if L['page'] == rel), None)
                urls = urls_all[off:off + len(pl)] if off is not None else [None] * len(pl)
            else:   # alias page (e.g. prep35): same lessons by title
                idx = {L['title']: i for i, L in enumerate(lessons)}; urls = [urls_all[idx[L['title']]] if L['title'] in idx else None for L in pl]
            done, miss = add_links(lits, kmap, urls)
            t = src
            for k in sorted(range(len(lits)), key=lambda k: -lits[k][1]):
                lit = lits[k]; d = dump(lit[3])
                if d != before[k]: t = t[:lit[1]] + d + t[lit[2]:]
            t = rename_levels(t)
            if QLINK not in t: t = t.replace('</body>', QLINK + '\n</body>', 1)
            if t != src: open(R + rel, 'w', encoding='utf8').write(t)
            report.append('%-28s lessons %3d  notes+link %4d  unmatched %d' % (rel[:-11], len(pl), done, miss))
        nq = sum(len(L['q']) for L in data_L)
        report.append('  → q/%d/%s: %d lessons (%d with games), %d questions' % (g, s, len(data_L), usable, nq))
    os.makedirs(FILES + 'q', exist_ok=True)
    open(FILES + 'q/engine.js', 'w', encoding='utf8').write(open(R + 'tools/quiz/engine.js', encoding='utf8').read())
    open(FILES + 'q/engine.css', 'w', encoding='utf8').write(open(R + 'tools/quiz/engine.css', encoding='utf8').read())
    print('\n'.join(report))
    import proc_list; proc_list.main()   # lesson procedures as numbered steps, never a table (owner 2026-10-25)
    import proc_style; proc_style.main([])   # one procedures style (owner, 2026-10-27)
    import add_identity; add_identity.main([])   # «غلق الدرس»: a fun closing step with citizenship, 5 minutes of the last period (owner, 2026-10-27/28)
    import english_stages; english_stages.main([])   # English: Presentation / Practice / Production, then Finishing (owner, 2026-10-28)
    import outcome_times; outcome_times.main([])
    import form_heading; form_heading.main([])   # «تفريد التعليم:» heading on the formative assessment, not English (owner, 2026-10-28)   # every outcome with its share of the period (owner, 2026-10-27)
    import add_shift; add_shift.main()   # the 40/35-minute switch on every prep page
    import add_twoshift; add_twoshift.main()   # two-shift preps (fewer periods, per the 2026/27 bulletins)

if __name__ == '__main__': main()
