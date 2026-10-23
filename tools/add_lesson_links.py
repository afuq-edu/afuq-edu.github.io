#!/usr/bin/env python3
"""Lesson links for the interactive decks (window.DECK): one permanent student link per lesson, for Noor.
 * Teacher deck (this repo, <g>/<s>/<interactive|lessons|slides>/): opens on the list of lessons (assets/lessonidx.js) with
   «دخول» (?l=<id>: that lesson only, with the teacher notes) and «نشر لنور»; ?all=1 shows every slide. A lesson's parts that are
   lessons of their own (grammar, spelling, writing… — tools/lesson_parts.json; grades 1–4: one per period) are listed under
   it with their own «دخول» / «نشر لنور» (?l=<id>&p=<part>: the cover, then that part's slides only).
 * Student page (files repo, <g>/<s>/view/<sec>/): the same deck without the teacher notes and without the gold guard;
   https://afuq-edu.github.io/afuq/<g>/<s>/view/<sec>/?l=<id> shows that lesson's slides only.
The deck images are files in /assets/img (tools/extract_imgs.py), shared by both pages.
Usage: python3 tools/add_lesson_links.py [grade/subject ...]   Rerun after adding or replacing a deck (add_interactive /
add_local_pack do it); then push the files repo first, wait for its deploy, then push this repo."""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
F = os.environ.get('AFUQ_FILES', '/home/user/afuq').rstrip('/') + '/'
sys.path.insert(0, R + 'tools')
DEC = json.JSONDecoder()
MARK = '/*afuq-lesson-filter*/'
FILTER_END = '/*afuq-lesson-filter-end*/'
# ?l=<lessonId> keeps only that lesson (own saved position); with &p=<partId> only that part's slides (behind the lesson's
# cover, which then shows the part's title). Runs right after the DECK data, before the deck engine reads it.
FILTER = (MARK + ';(function(){var s=new URLSearchParams(location.search),q=s.get("l"),p=s.get("p");if(!q)return;var D=window.DECK,'
          'L=D.lessons.filter(function(x){return x.id===q});if(!L.length)return;var P=p&&(L[0].parts||[]).filter(function(x){return x.id===p})[0];'
          'if(P){var o=L[0],sl=o.slides;L=[Object.assign({},o,{title:P.t,unitName:(o.unitName?o.unitName+" – ":"")+o.title,'
          'slides:[sl[0]].concat(sl.slice(P.a,P.b+1))})]}D.lessons=L;D.units=(D.units||[]).filter(function(u){return u.id===L[0].unit});'
          'D.store+="-"+q+(P?"-"+p:"")})();' + FILTER_END)
OLD_FILTER = re.compile(re.escape(MARK) + r';\(function\(\)\{.*?(?:\}\)\(\);' + re.escape(FILTER_END) + r'|\}\)\(\);)', re.S)
PARTS = json.load(open(R + 'tools/lesson_parts.json', encoding='utf8'))
ORD = ['', 'الأولى', 'الثانية', 'الثالثة', 'الرابعة', 'الخامسة', 'السادسة', 'السابعة', 'الثامنة', 'التاسعة', 'العاشرة',
       'الحادية عشرة', 'الثانية عشرة', 'الثالثة عشرة', 'الرابعة عشرة', 'الخامسة عشرة']
TAG = re.compile(r'<script src="/assets/lessonidx\.js"[^>]*></script>\n?')
GUARD_RE = re.compile(r'<script>\(function\(\)\{var k=.*?</script><script src="/assets/pkgmode.js" data-role="page"></script>', re.S)
NOTE_KEYS = ('note', 'tip')

def deck_of(h):
    for m in re.finditer(r'window\.DECK=', h):
        try: d, e = DEC.raw_decode(h, m.end())
        except Exception: continue
        if isinstance(d, dict) and isinstance(d.get('lessons'), list) and d['lessons']: return d, m.end(), e
    return None, 0, 0

def js(o): return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')

def plain(t): return re.sub(r'\s+', ' ', re.sub(r'[\u064B-\u0652\u0670\u0640]', '', str(t or ''))).strip()

def parts_of(deck, L):
    """[{id, t, a, b}]: the lesson's parts that are lessons of their own (tools/lesson_parts.json), or one per «period» slide."""
    sl = L.get('slides') or []
    if deck in PARTS:
        return [{'id': 'p%d' % (k + 1), 't': t, 'a': a, 'b': b} for k, (a, b, t) in enumerate(PARTS[deck].get(L.get('id'), [])) if 0 < a <= b < len(sl)]
    per = [i for i, x in enumerate(sl) if x.get('type') == 'period']
    if len(per) < 2: return []
    end = next((i for i, x in enumerate(sl) if x.get('type') in ('summary', 'exit', 'homework') or plain(x.get('title')).startswith('خلاصة')), len(sl))
    out = []
    for k, i in enumerate(per):
        b = (per[k + 1] if k + 1 < len(per) else end) - 1
        if b < i: continue
        t = plain(sl[i].get('title'))
        if len(re.findall('[A-Za-z]', t)) > len(re.findall('[\u0600-\u06FF]', t)): name = 'Period %d' % (k + 1)   # English decks
        else: name = 'الحصة ' + (ORD[k + 1] if k + 1 < len(ORD) else str(k + 1))
        out.append({'id': 'p%d' % (k + 1), 't': name + ' – ' + t, 'a': 2 if k == 0 else i, 'b': b})
    return out

def with_parts(h, deck):
    d, i, e = deck_of(h)
    if not d: return h
    for L in d['lessons']:
        ps = parts_of(deck, L)
        if ps: L['parts'] = ps
        else: L.pop('parts', None)
    return h[:i] + js(d) + h[e:]

def teacher(h, student_url, deck=''):
    d, i, e = deck_of(h)
    if not d: return None
    h = with_parts(h, deck); d, i, e = deck_of(h)
    # fmt() output in one inline box: inside the decks' flex boxes (goal tickets…) bare text + <mark>/<bdi> became separate
    # flex items and the words of one sentence showed up in scrambled columns
    h = h.replace("return t.replace(/\\u0001/g,'<br>')}", "return '<span class=\"fx\">'+t.replace(/\\u0001/g,'<br>')+'</span>'}", 1)
    h = h[:e] + FILTER + OLD_FILTER.sub('', h[e:], count=1) if MARK in h[e:e + 400] else h[:e] + FILTER + h[e:]
    h = TAG.sub('', h)
    return h.replace('</body>', '<script src="/assets/lessonidx.js" data-mode="teacher" data-student="%s"></script>\n</body>' % student_url, 1)

def student(h, student_url):
    d, i, e = deck_of(h)
    lessons = [dict(L, slides=[{k: v for k, v in sl.items() if k not in NOTE_KEYS} for sl in L.get('slides', [])]) for L in d['lessons']]
    nd = dict(d, lessons=lessons, store=d.get('store', 'deck') + '-view', title=re.sub(r'^العرض التفاعلي', 'شرح الدروس', d.get('title', '')))
    h = h[:i] + js(nd) + h[e:]
    h = GUARD_RE.sub('', h, count=1).replace('<script src="/assets/pkgmode.js" data-role="page"></script>', '')
    h = TAG.sub('', h).replace('</body>', '<script src="/assets/lessonidx.js" data-mode="student" data-student="%s"></script>\n</body>' % student_url, 1)
    h = re.sub(r'<title>[^<]*</title>', '<title>%s</title>' % nd['title'].replace('<', ''), h, count=1)
    return h.replace('<head>', '<head><meta name="robots" content="noindex">', 1) if 'name="robots"' not in h else h

def main():
    only = [a.strip('/') for a in sys.argv[1:]]
    pages = sorted(glob.glob(R + '[0-9]*/*/interactive/index.html') + glob.glob(R + '[0-9]*/*/lessons/index.html') + glob.glob(R + '[0-9]*/*/slides/index.html'))
    n = nl = np_ = 0
    for p in pages:
        rel = p[len(R):]; g, s, sec = rel.split('/')[:3]
        if only and '%s/%s' % (g, s) not in only: continue
        h = open(p, encoding='utf8').read()
        d, _, _ = deck_of(h)
        if not d: continue
        ids = [L.get('id') for L in d['lessons']]
        if len(set(ids)) != len(ids) or not all(ids): print('skip (lesson ids not unique):', rel); continue
        url = '/afuq/%s/%s/view/%s/' % (g, s, sec)
        t = teacher(h, url, '%s/%s/%s' % (g, s, sec))
        if t != h: open(p, 'w', encoding='utf8').write(t)
        out = F + '%s/%s/view/%s/index.html' % (g, s, sec); os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf8').write(student(t, url))
        n += 1; nl += len(ids)
        d2, _, _ = deck_of(t); npt = sum(len(L.get('parts') or []) for L in d2['lessons']); np_ += npt
        print('%-26s %3d lessons%s -> %s' % (rel[:-11], len(ids), ' + %d parts' % npt if npt else '', url))
    print('%d decks, %d lesson links, %d part links' % (n, nl, np_))

if __name__ == '__main__': main()
