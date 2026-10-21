#!/usr/bin/env python3
"""Lesson links for the interactive decks (window.DECK): one permanent student link per lesson, for Noor.
 * Teacher deck (this repo, <g>/<s>/<interactive|lessons|slides>/): opens on the list of lessons (assets/lessonidx.js) with
   «دخول» (?l=<id>: that lesson only, with the teacher notes), «تشغيل» and «نسخ لمنصة نور»; ?all=1 shows every slide.
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
# ?l=<lessonId> keeps only that lesson (own saved position); runs right after the DECK data, before the deck engine reads it.
FILTER = (MARK + ';(function(){var q=new URLSearchParams(location.search).get("l");if(!q)return;var D=window.DECK,L=D.lessons.filter(function(x){return x.id===q});'
          'if(!L.length)return;D.lessons=L;D.units=(D.units||[]).filter(function(u){return u.id===L[0].unit});D.store+="-"+q})();')
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

def teacher(h, student_url):
    d, i, e = deck_of(h)
    if not d: return None
    if MARK not in h[e:e + 400]: h = h[:e] + FILTER + h[e:]
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
    n = nl = 0
    for p in pages:
        rel = p[len(R):]; g, s, sec = rel.split('/')[:3]
        if only and '%s/%s' % (g, s) not in only: continue
        h = open(p, encoding='utf8').read()
        d, _, _ = deck_of(h)
        if not d: continue
        ids = [L.get('id') for L in d['lessons']]
        if len(set(ids)) != len(ids) or not all(ids): print('skip (lesson ids not unique):', rel); continue
        url = '/afuq/%s/%s/view/%s/' % (g, s, sec)
        t = teacher(h, url)
        if t != h: open(p, 'w', encoding='utf8').write(t)
        out = F + '%s/%s/view/%s/index.html' % (g, s, sec); os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf8').write(student(t, url))
        n += 1; nl += len(ids)
        print('%-26s %3d lessons -> %s' % (rel[:-11], len(ids), url))
    print('%d decks, %d lesson links' % (n, nl))

if __name__ == '__main__': main()
