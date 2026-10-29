#!/usr/bin/env python3
"""Two gold sections per subject from the owner's app folders (owner, 2026-10-28):
  «ملخصات الدروس» (lsum)  one PDF summary per lesson, by unit, to open or download, with the recommendation to upload it to
                          «مرفقات المادة» in منصة نور;
  «تطبيق المادة» (app)     the subject app (a PWA: full screen, works offline): the section opens it straight away and its
                          own bar offers «📲 تثبيت» (on iPhone: Share → Add to Home Screen).
Input: folders الصف_<grade>/<subject>/ each with index.html (data in <script id="data">: units, lessons, pdfs), manifest.webmanifest,
sw.js, icons/ and الملخصات/*.pdf (the app links to them).
Usage: python3 tools/add_apps.py DIR [DIR ...]   (a DIR holds الصف_* folders)
The app and its PDFs are copied as they are to apps/<g>/<s>/ in this repo — open, so students can install it too (the files
repo is at the 1 GB Pages limit). <g>/<s>/app/ (locked like every gold section) forwards to it, <g>/<s>/lsum/ lists the
PDFs. Adds the portal cards and SECTIONS entries, the catalogue parts in p/index.html, the home page list and the «جديد»
badge. Rerunning replaces the files. Then update the links program (collection links, each subject's «parts»)."""
import re, os, sys, json, glob, shutil, html as H, unicodedata
from urllib.parse import quote
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
GRADES = ['الأول', 'الثاني', 'الثالث', 'الرابع', 'الخامس', 'السادس', 'السابع', 'الثامن', 'التاسع', 'العاشر', 'الحادي_عشر', 'الثاني_عشر']
SUBJ = {'التربية_الإسلامية': 'islamic', 'الرياضيات': 'math', 'العلوم': 'science', 'اللغة_الإنجليزية': 'english', 'اللغة_العربية': 'arabic',
        'الهوية_والمواطنة': 'social', 'الدراسات_الاجتماعية': 'social', 'تقنية_المعلومات': 'it', 'الفيزياء': 'physics', 'الكيمياء': 'chemistry',
        'الأحياء': 'biology', 'العلوم_البيئية': 'envsci', 'التربية_البدنية': 'pe', 'الفنون_البصرية': 'arts', 'المهارات_الموسيقية': 'music',
        'الرياضيات_الأساسية': 'basicmath', 'الرياضيات_المتقدمة': 'advmath', 'هذا_وطني': 'homeland'}
LSUM, APP = ('lsum', 'ملخصات الدروس'), ('app', 'تطبيق المادة')
SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
ICON = {'lsum': SVG % '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/>',
        'app': SVG % '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/><path d="M12 6v6M9.5 9.5 12 12l2.5-2.5"/>'}
DEC = json.JSONDecoder()

def read(p): return open(R + p, encoding='utf8').read()
def write(p, t):
    os.makedirs(os.path.dirname(R + p), exist_ok=True); open(R + p, 'w', encoding='utf8').write(t)

def guard(prefix, key):
    return ("<script>(function(){var k='%s%s';function g(n,x){try{if(window[n].getItem(x)==='1')return true}catch(e){}try{return new RegExp('(^|; )'+x+'=1(;|$)').test(document.cookie)||(' '+window.name+' ').indexOf(' '+x+' ')>=0}catch(e){return false}}"
            "if(g('localStorage',k)||g('sessionStorage',k)||g('localStorage','afuq-all')||g('sessionStorage','afuq-all'))return;"
            "document.documentElement.style.display='none';location.replace('../?lock=%s')})()</script>"
            "<script src=\"/assets/pkgmode.js\" data-role=\"page\"></script>") % (prefix, key, key)

CSS = ('<style>:root{--bg:#f6f4ee;--card:#fff;--ink:#1f2a24;--muted:#66726c;--brand:#2E6F73;--line:#e6e0d2;--soft:#eef5f4;--tip:#fff7e0;--tipline:#f0d48a}'
       '@media (prefers-color-scheme:dark){:root{--bg:#141815;--card:#1d231f;--ink:#e8ede9;--muted:#9aa59f;--brand:#5fb3b8;--line:#2b332e;--soft:#1f2b2a;--tip:#2a2516;--tipline:#5c4d22}}'
       '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,"Segoe UI",sans-serif;line-height:1.7}'
       'main{max-width:820px;margin:0 auto;padding:22px 16px 40px}a.back{color:var(--muted);text-decoration:none;font-size:14px}'
       'h1{margin:10px 0 4px;font-size:26px}p.sub{margin:0 0 14px;color:var(--muted)}'
       '.tip{background:var(--tip);border:1px solid var(--tipline);border-radius:14px;padding:10px 14px;margin:0 0 16px;font-size:15px}'
       '.unit{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:6px 16px 10px;margin:0 0 14px}'
       '.unit h2{font-size:17px;margin:10px 0 6px;color:var(--brand)}'
       '.row{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;padding:10px 0;border-top:1px dashed var(--line)}'
       '.row .t{flex:1 1 220px;display:flex;gap:8px;align-items:baseline}.code{font-size:13px;color:var(--muted);direction:ltr;unicode-bidi:isolate;min-width:2.6em}'
       '.acts{display:flex;flex-wrap:wrap;gap:6px}.btn{font:inherit;font-size:14px;font-weight:700;padding:7px 12px;border-radius:12px;border:1px solid var(--line);'
       'background:var(--soft);color:var(--ink);text-decoration:none;white-space:nowrap}.btn.go{background:var(--brand);border-color:var(--brand);color:#fff}</style>')

def lsum_page(g, lab, prefix, D, base):
    les = {L['id']: L for L in D['lessons']}
    body = ''
    for U in D['units']:
        rows = ''
        for i in U['ids']:
            P = D.get('pdfs', {}).get(i) or {}; f = P.get('s') or P.get('m')   # «m»: some apps file a lesson's PDF under it
            if not f or i not in les: continue
            url = base + quote(f)
            rows += ('<div class="row"><div class="t"><span class="code">%s</span><b>%s</b></div><div class="acts">'
                     '<a class="btn go" href="%s" target="_blank" rel="noopener">📄 فتح الملخص</a>'
                     '<a class="btn" href="%s" download="%s">⬇ تحميل</a></div></div>') % (H.escape(i), H.escape(les[i]['title']), url, url, H.escape(os.path.basename(f), True))
        if rows: body += '<section class="unit"><h2>%s</h2>%s</section>' % (H.escape(U['name']), rows)
    return ('<!doctype html><html lang="ar" dir="rtl"><head>' + guard(prefix, LSUM[0]) +
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s – %s – الصف %s</title>%s</head><body><main>'
            '<a class="back" href="../">→ %s – الصف %s</a><h1>📄 %s</h1>'
            '<p class="sub">ملخص لكل درس في ملف PDF: افتحه للعرض أو الطباعة، أو حمّله.</p>'
            '<div class="tip">💡 <b>توصية:</b> ارفع ملف ملخص الدرس في <b>«مرفقات المادة»</b> في منصة نور، ليرجع إليه طلابك في أي وقت.</div>%s'
            '</main></body></html>') % (LSUM[1], lab, GRADES[g - 1].replace('_', ' '), CSS, lab, GRADES[g - 1].replace('_', ' '), LSUM[1], body)

def app_page(g, lab, prefix, base):
    return ('<!doctype html><html lang="ar" dir="rtl"><head>' + guard(prefix, APP[0]) +
            '<script>if(document.documentElement.style.display!==\'none\')location.replace(%s)</script><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s – %s – الصف %s</title>%s</head><body><main><a class="back" href="../">→ %s – الصف %s</a><h1>📲 %s</h1>'
            '<p class="sub"><a class="btn go" href="%s">افتح التطبيق وثبّته على هاتفك</a></p></main></body></html>'
            ) % (json.dumps(base), APP[1], lab, GRADES[g - 1].replace('_', ' '), CSS, lab, GRADES[g - 1].replace('_', ' '), APP[1], base)

CARD = r'    <button class="card" style="--c:var\(--c\d\)" data-id="%s">.*?</button>\n'
def portal(d, sec, title, desc, after):
    u = read(d + 'index.html')
    if 'data-id="%s"' % sec in u: return
    ids = re.findall(r'data-id="([a-z0-9]+)"', u)
    prev = next((a for a in after if a in ids), ids[-1])
    m = re.search(CARD % prev, u, re.S); e = re.search(r"    %s:\{title:'[^']*',hash:null\},?\n" % prev, u)
    assert m and e, (d, prev)
    card = re.sub(r'data-id="[a-z0-9]+"', 'data-id="%s"' % sec, m.group(0), count=1)
    card = re.sub(r'<h3>.*?</h3>', '<h3>%s</h3>' % title, card)
    card = re.sub(r'<p>.*?</p>', '<p>%s</p>' % desc, card, flags=re.S)
    card = re.sub(r'<span class="ic">.*?</span>', '<span class="ic">%s</span>' % ICON[sec], card, count=1, flags=re.S)
    u = u.replace(m.group(0), m.group(0) + card, 1)
    line = e.group(0); entry = "    %s:{title:'%s',hash:null}" % (sec, title)
    u = u.replace(line, (line if line.rstrip().endswith(',') else line.rstrip('\n') + ',\n') + entry + (',\n' if line.rstrip().endswith(',') else '\n'), 1)
    write(d + 'index.html', u)

def catalogue(prefix, sec, title, after):
    v = read('p/index.html')
    m = re.search(r'var ICON=(\{.*?\});', v); ic = json.loads(m.group(1))
    if sec not in ic: ic[sec] = ICON[sec]; v = v[:m.start(1)] + json.dumps(ic, ensure_ascii=False) + v[m.end(1):]
    o = '"lock": "%s", "parts": [' % prefix; assert v.count(o) == 1, prefix
    i = v.index(o); j = v.index(']]', i) + 1; seg = v[i:j]
    if '["%s"' % sec not in seg:
        keys = re.findall(r'\["([a-z0-9]+)", "[^"]*", (?:true|false)\]', seg)
        prev = next((a for a in after if a in keys), keys[-1])
        mm = re.search(r'\["%s", "[^"]*", (?:true|false)\]' % prev, seg)
        seg = seg[:mm.end()] + ', ["%s", "%s", true]' % (sec, title) + seg[mm.end():]
    write('p/index.html', v[:i] + seg + v[j:])

def home(g, s):
    L = read('index.html').split('\n')
    i = next(k for k, x in enumerate(L) if x.startswith('    %d:[' % g)); x = L[i]
    a = x.find("['%s/'" % s)
    if a < 0: return
    b = x.index("']", a); seg = x[a:b]
    for t in (LSUM[1], APP[1]):
        if t not in seg: seg += ' · ' + t
    L[i] = x[:a] + seg + x[b:]; write('index.html', '\n'.join(L))

SPEAK = "function speak(text) {"
CLEAN = ("function speak(text) {   text = String(text).replace(/[\\p{Extended_Pictographic}\\u{1F1E6}-\\u{1F1FF}\\u{1F3FB}-\\u{1F3FF}\\uFE0F\\u200D\\u20E3]/gu, ' ')"
         ".replace(/\\s+/g, ' ').trim();")   # icons out (owner, 2026-10-28: the voice read 🔊 as «سماعة»)
def fix_app(d):
    """the app's speech without icons; the service worker's cache renamed so installed apps take the new page"""
    h = open(d + 'index.html', encoding='utf8').read()
    if CLEAN not in h:
        assert h.count(SPEAK) == 1, d
        open(d + 'index.html', 'w', encoding='utf8').write(h.replace(SPEAK, CLEAN, 1))
        w = open(d + 'sw.js', encoding='utf8').read()
        open(d + 'sw.js', 'w', encoding='utf8').write(re.sub(r"const C='([^']*?)(?:-s\d+)?'", lambda m: "const C='%s-s2'" % m.group(1), w, count=1))

def install(src, g, s, cat, lab):
    d = '%d/%s/' % (g, s); prefix = cat[d]['lock']
    h = open(src + '/index.html', encoding='utf8').read()
    m = re.search(r'<script id="data" type="application/json">', h); D, _ = DEC.raw_decode(h, m.end())
    out = 'apps/%d/%s/' % (g, s)
    shutil.rmtree(R + out, ignore_errors=True)
    shutil.copytree(src, R + out, ignore=shutil.ignore_patterns('افتح_التطبيق.html', 'التحاضير', '.DS_Store'))
    for dp, dns, fns in os.walk(R + out, topdown=False):       # names as the app links them (NFC), not a Mac zip's NFD
        for n in dns + fns:
            if unicodedata.normalize('NFC', n) != n: os.rename(os.path.join(dp, n), os.path.join(dp, unicodedata.normalize('NFC', n)))
    fix_app(R + out)
    base = '/' + out
    write(d + 'lsum/index.html', lsum_page(g, lab, prefix, D, base))
    write(d + 'app/index.html', app_page(g, lab, prefix, base))
    grd = GRADES[g - 1].replace('_', ' ')
    portal(d, *LSUM, 'ملخص PDF لكل درس – %s – الصف %s، يُرفع في مرفقات المادة في منصة نور' % (lab, grd), ['summaries', 'recap', 'harvest', 'board', 'slides', 'prep'])
    portal(d, *APP, 'تطبيق %s للصف %s على الهاتف: يُثبَّت بضغطة ويعمل بشاشة كاملة وبدون إنترنت' % (lab, grd), ['homework', 'kahoot'])
    catalogue(prefix, *LSUM, ['summaries', 'recap', 'harvest', 'board', 'slides', 'prep'])
    catalogue(prefix, *APP, ['homework', 'kahoot'])
    home(g, s)
    __import__('mark_new').mark(d + 'lsum', d + 'app')
    n = len(glob.glob(R + out + 'الملخصات/*.pdf'))
    size = sum(os.path.getsize(p) for p in glob.glob(R + out + '**', recursive=True) if os.path.isfile(p)) / 1e6
    return n, size

def main():
    cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', read('p/index.html')).group(1))
    tot = 0; skipped = []
    for top in sys.argv[1:]:
        for gd in sorted(glob.glob(os.path.join(top, 'الصف_*'))):
            gname = unicodedata.normalize('NFC', os.path.basename(gd))[len('الصف_'):]
            if gname not in GRADES: skipped.append(gd); continue
            g = GRADES.index(gname) + 1
            for sd in sorted(glob.glob(gd + '/*/')):
                sname = unicodedata.normalize('NFC', os.path.basename(sd.rstrip('/'))); s = SUBJ.get(sname)   # zips made on a Mac carry NFD names
                if not s or '%d/%s/' % (g, s) not in cat or not os.path.exists(sd + 'index.html'): skipped.append(sd); continue
                lab = sname.replace('_', ' ')
                n, size = install(sd.rstrip('/'), g, s, cat, lab); tot += size
                print('%-12s %3d PDF  %5.1f MB' % ('%d/%s' % (g, s), n, size))
    print('done, %.0f MB' % tot, '; skipped:', skipped)

if __name__ == '__main__': main()
