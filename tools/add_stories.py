#!/usr/bin/env python3
"""«قصص المنهج» (story): one illustrated PDF story per subject (owner, 2026-10-29), shown two ways:
  • the gold section <g>/<s>/story/ (locked): open or download it;
  • inside the subject app (apps/<g>/<s>/): a «📖 قصص المنهج» tile; the story is saved with the app on install, so it opens
    without internet (tools/add_apps.py fix_app).
The PDFs live in the repo afuq-edu/more (served at /more/stories/<g>/<s>.pdf): this repo is near the 1 GB Pages limit.
Usage: python3 tools/add_stories.py PDF [PDF ...]      (names قصص_المنهج_<المادة>_الصف_<الصف>.pdf)
Then push afuq-edu/more first, wait for its deploy, then this repo; add «story» to the links program."""
import re, os, sys, json, shutil, unicodedata, html as H
from urllib.parse import quote
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import add_apps as A
R = A.R
KEY, TITLE = 'story', 'قصص المنهج'
A.ICON[KEY] = A.SVG % '<path d="M4 5a2 2 0 0 1 2-2h5v17H6a2 2 0 0 0-2 2z"/><path d="M20 5a2 2 0 0 0-2-2h-5v17h5a2 2 0 0 1 2 2z"/>'

def parse(path):
    b = unicodedata.normalize('NFC', os.path.basename(path))
    m = re.match(r'^قصص_المنهج_(.+)_الصف_(.+)\.pdf$', b)
    if not m or m.group(2) not in A.GRADES or m.group(1) not in A.SUBJ: return None
    return A.GRADES.index(m.group(2)) + 1, A.SUBJ[m.group(1)], m.group(1).replace('_', ' ')

def page(g, lab, prefix, url):
    grd = A.GRADES[g - 1].replace('_', ' ')
    return ('<!doctype html><html lang="ar" dir="rtl"><head>' + A.guard(prefix, KEY) +
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s – %s – الصف %s</title>%s</head><body><main>'
            '<a class="back" href="../">→ %s – الصف %s</a><h1>📖 %s</h1>'
            '<p class="sub">قصة مصوّرة لدروس %s للصف %s: افتحها للعرض أو الطباعة، أو حمّلها.</p>'
            '<div class="tip">💡 القصة موجودة أيضًا داخل <b>«تطبيق المادة»</b>، وتعمل فيه بدون إنترنت بعد تثبيته.</div>'
            '<section class="unit"><div class="row"><div class="t"><b>📖 %s – %s – الصف %s</b></div><div class="acts">'
            '<a class="btn go" href="%s" target="_blank" rel="noopener">📖 افتح القصة</a><a class="btn" href="%s" download="%s">⬇ تحميل</a></div></div></section>'
            '</main></body></html>') % (TITLE, lab, grd, A.CSS, lab, grd, TITLE, lab, grd, TITLE, lab, grd, url, url,
                                        H.escape('%s - %s - الصف %s.pdf' % (TITLE, lab, grd), True))

def home(g, s):
    L = A.read('index.html').split('\n')
    i = next(k for k, x in enumerate(L) if x.startswith('    %d:[' % g)); x = L[i]
    a = x.find("['%s/'" % s)
    if a < 0: return
    b = x.index("']", a); seg = x[a:b]
    if TITLE not in seg:
        seg = seg.replace(' · ' + A.APP[1], ' · %s · %s' % (TITLE, A.APP[1])) if A.APP[1] in seg else seg + ' · ' + TITLE
    L[i] = x[:a] + seg + x[b:]; A.write('index.html', '\n'.join(L))

def main():
    cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', A.read('p/index.html')).group(1))
    done, skipped = [], []
    for f in sys.argv[1:]:
        p = parse(f)
        if not p or '%d/%s/' % p[:2] not in cat: skipped.append(os.path.basename(f)); continue
        g, s, lab = p; d = '%d/%s/' % (g, s); prefix = cat[d]['lock']
        os.makedirs(A.STORIES + str(g), exist_ok=True); shutil.copyfile(f, A.STORIES + '%d/%s.pdf' % (g, s))
        url = A.story_url(g, s)
        A.write(d + KEY + '/index.html', page(g, lab, prefix, url))
        A.portal(d, KEY, TITLE, 'قصة مصوّرة لدروس %s – الصف %s، وتعمل داخل تطبيق المادة بدون إنترنت' % (lab, A.GRADES[g - 1].replace('_', ' ')), ['lsum', 'summaries', 'recap', 'harvest', 'prep'])
        A.catalogue(prefix, KEY, TITLE, ['lsum', 'summaries', 'recap', 'harvest', 'prep'])
        home(g, s)
        __import__('mark_new').mark(d + KEY)
        if os.path.isdir(R + 'apps/' + d): A.fix_app(R + 'apps/' + d)
        done.append('%s %.1f MB' % (d, os.path.getsize(A.STORIES + '%d/%s.pdf' % (g, s)) / 1e6))
    print('\n'.join(done)); print('done', len(done), '; skipped:', skipped)

if __name__ == '__main__': main()
