#!/usr/bin/env python3
"""The arts gold package (owner, 2026-11-04: «العروض التفاعلية والملخصات وكاهوت» for الفنون البصرية / التشكيلية, grades 1–12),
from per-lesson content written from the arts preps, on the engines of the grade-12 biology package:
  slides  («العروض التفاعلية»: the interactive deck, window.DECK) → then add_lesson_links (lesson list + student pages)
  lsum    («ملخصات الدروس»: one A4 PDF summary per lesson, made here from the content, with the Noor upload tip)
  kahoot  («مسابقات كاهوت»: the group contest, every lesson and period)
Usage: python3 tools/add_arts_pack.py CONTENT_DIR [GRADE ...]          (default: every grade with content)
  CONTENT_DIR/gGG/LNN.json = {"deck": {"title","code","emo","theme","slides":[…]}, "kahoot": [[period, level, m|t|f, q, …]],
  "summary": {"intro","points":[…],"terms":[[t,d]…],"steps":[…],"tools":[…],"tip"}}   (NN = lesson order in <g>/arts/prep/)
Lessons, units and periods come from <g>/arts/prep/index.html. The summary PDFs (Chromium via Playwright) go to <g>/arts/lsum/.
Writes the section pages, the portal cards and SECTIONS entries, the catalogue parts in p/index.html, the home page list and the
«جديد» badge. Rerunning replaces the pages. Then push the files repo first (student pages), wait for its deploy, then push this
repo; update the links program («links» collection) to match CAT."""
import re, os, sys, json, glob, subprocess, html as H
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B, add_apps as A
T = '12/biology/'
DEC = json.JSONDecoder()
GRADE = {1: 'الأول', 2: 'الثاني', 3: 'الثالث', 4: 'الرابع', 5: 'الخامس', 6: 'السادس', 7: 'السابع', 8: 'الثامن', 9: 'التاسع', 10: 'العاشر', 11: 'الحادي عشر', 12: 'الثاني عشر'}
THEMES = ['garden', 'park', 'heritage', 'city', 'lab', 'maproom']
SEC = {'slides': 'العروض التفاعلية', 'lsum': 'ملخصات الدروس', 'kahoot': 'مسابقات كاهوت'}
AFTER = {'slides': ['prep'], 'lsum': ['scorm', 'slides', 'prep'], 'kahoot': ['lsum', 'scorm', 'slides', 'prep']}
DESC = {'slides': 'عرض تفاعلي لكل درس: شرح وأنشطة وألعاب للصف', 'lsum': 'ملخص لكل درس في ملف PDF لمرفقات المادة في نور',
        'kahoot': 'مسابقة المجموعات لكل درس وحصة'}

def read(p): return open(R + p, encoding='utf8').read()
def write(p, t):
    os.makedirs(os.path.dirname(R + p), exist_ok=True); open(R + p, 'w', encoding='utf8').write(t)
def js(o): return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
def swap(h, pat, obj):
    m = re.search(pat, h); o, e = DEC.raw_decode(h, m.end()); return h[:m.end()] + js(obj) + h[e:]
def texts(h, d, lab, grd):
    for a in ('الأحياء – الصف الثاني عشر', 'أحياء – الصف الثاني عشر'): h = h.replace(a, '%s – الصف %s' % (lab, grd))
    h = h.replace('الأحياء · الصف الثاني عشر', '%s · الصف %s' % (lab, grd)).replace('· الأحياء ·', '· %s ·' % lab)
    return h.replace(T, d)
def guard_key(h, pre, sec): return re.sub(r"var k='ofuq-g12l-unlock-%s'" % sec, "var k='%s%s'" % (pre, sec), h)

CAP = {'goals': ('items', 4), 'explain': ('lines', 5)}   # what fits one slide on a 16:9 screen (tested 2026-11-04)
def fit(slides):
    """a goals / explain slide longer than one screen becomes two or more, the next ones titled «… (تابع)»"""
    out = []
    for s in slides:
        k, n = CAP.get(s.get('type'), (None, 0)); xs = s.get(k) if k else None
        if not xs or len(xs) <= n: out.append(s); continue
        for j in range(0, len(xs), n):
            out.append(dict(s, **{k: xs[j:j + n]}, title=s['title'] + (' (تابع)' if j else '')))
    return out

def lessons_of(g):
    h = read('%d/arts/prep/index.html' % g); lits = B.literals(h); les, kmap = B.page_lessons(lits)
    by = {n: o for n, i, e, o in lits}; out = []
    for L, k in zip(les, kmap):
        raw = by[k[0]][k[2]]
        out.append({'title': L['title'], 'unit': L['unit'], 'periods': [p.get('ax') or p.get('axis') or '' for p in raw['periods']]})
    return out

SUMCSS = ('@page{size:A4;margin:14mm 14mm 12mm}*{box-sizing:border-box}body{margin:0;font-family:Tahoma,"Segoe UI",sans-serif;color:#1f2a24;line-height:1.75;font-size:12.5pt}'
          'header{border-bottom:3px solid #C2367A;padding-bottom:6px;margin-bottom:10px}header small{color:#6b5b66;font-size:10pt}'
          'h1{margin:2px 0 0;font-size:19pt;color:#8E1F57}p.intro{margin:6px 0 10px;font-size:12.5pt}'
          'h2{font-size:13pt;margin:12px 0 4px;color:#C2367A}ul,ol{margin:0;padding-inline-start:22px}li{margin:2px 0}'
          'table{width:100%;border-collapse:collapse;font-size:11.5pt}td{border:1px solid #ecd3e0;padding:4px 8px;vertical-align:top}td:first-child{font-weight:700;width:30%;background:#fdf1f7}'
          '.cols{display:flex;gap:14px}.cols>div{flex:1}.tip{margin-top:12px;background:#fff7e0;border:1px solid #f0d48a;border-radius:10px;padding:8px 12px}'
          'footer{margin-top:10px;color:#8a7f86;font-size:9.5pt;text-align:center}')
def summary_html(g, lab, L, dk, S, n):
    e = H.escape; li = lambda xs: ''.join('<li>%s</li>' % e(x) for x in xs)
    h = '<header><small>%s – الصف %s · %s</small><h1>%s %s</h1></header>' % (e(lab), GRADE[g], e(L['unit']), e(dk.get('emo', '🎨')), e(dk['title']))
    h += '<p class="intro">%s</p><h2>⭐ أهم ما في الدرس</h2><ul>%s</ul>' % (e(S['intro']), li(S['points']))
    if S.get('terms'): h += '<h2>📘 مفاهيم الدرس</h2><table>%s</table>' % ''.join('<tr><td>%s</td><td>%s</td></tr>' % (e(a), e(b)) for a, b in S['terms'])
    cols = ''
    if S.get('steps'): cols += '<div><h2>🖌️ خطوات العمل</h2><ol>%s</ol></div>' % li(S['steps'])
    if S.get('tools'): cols += '<div><h2>🧰 الأدوات والخامات</h2><ul>%s</ul></div>' % li(S['tools'])
    if cols: h += '<div class="cols">%s</div>' % cols
    h += '<div class="tip">💡 %s</div><footer>منصة أفق التعليمية · ملخص الدرس %d</footer>' % (e(S['tip']), n)
    return '<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>' % (SUMCSS, h)

PDFJS = r"""const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:690,height:1000}});
for(const [src,out] of JSON.parse(require('fs').readFileSync(process.argv[2],'utf8'))){await p.goto('file://'+src);
 await p.evaluate(()=>{let z=1;while(document.documentElement.scrollHeight>1010&&z>0.7){z-=0.03;document.body.style.zoom=z;}});   /* one A4 page */
 await p.pdf({path:out,format:'A4',printBackground:true,preferCSSPageSize:true});}
await b.close();})();"""

def build(g, cdir):
    d = '%d/arts/' % g; grd = GRADE[g]
    v = read('p/index.html'); cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', v).group(1))
    pre = cat[d]['lock']; lab = re.sub(r'\s*–\s*الصف.*$', '', cat[d]['title']).strip()
    les = lessons_of(g); C = {}
    for n in range(1, len(les) + 1):
        f = os.path.join(cdir, 'g%02d' % g, 'L%02d.json' % n)
        if os.path.exists(f): C[n] = json.load(open(f, encoding='utf8'))
    assert len(C) == len(les), '%s: %d of %d lessons' % (d, len(C), len(les))
    units, uid = [], {}
    for L in les:
        if L['unit'] not in uid:
            uid[L['unit']] = 'U%d' % (len(units) + 1); units.append({'id': uid[L['unit']], 'name': L['unit'], 'theme': THEMES[len(units) % len(THEMES)]})
    # ---- slides
    deck = {'title': 'العرض التفاعلي – %s – الصف %s' % (lab, grd), 'sub': 'الفصل الدراسي الأول', 'store': 'deck2-g%d-arts' % g,
            'cfg': {'lang': 'ar', 'icon': '🎨', 'wicon': '🖌️', 'welcome': 'مرحبًا بكم في عالم %s' % lab, 'mascot': 'OWL', 'kids': g <= 6},
            'units': units, 'lessons': []}
    for n, L in enumerate(les, 1):
        dk = C[n]['deck']
        deck['lessons'].append({'id': 'L%02d' % n, 'unit': uid[L['unit']], 'unitName': L['unit'], 'title': dk['title'], 'code': dk['code'],
                                'theme': dk.get('theme') or 'garden', 'emo': dk.get('emo') or '🎨', 'slides': fit(dk['slides'])})
    h = swap(swap(read(T + 'slides/index.html'), r'window\.DECK=', deck), r'window\.IMGS=', {})
    write(d + 'slides/index.html', guard_key(texts(h, d, lab, grd), pre, 'slides'))
    # ---- kahoot
    D = [{'t': C[n]['deck']['title'], 'u': 'الوحدة %d' % int(uid[L['unit']][1:]), 'p': L['periods'], 'q': C[n]['kahoot']} for n, L in enumerate(les, 1)]
    write(d + 'kahoot/index.html', guard_key(texts(swap(read(T + 'kahoot/index.html'), r'const D=', D), d, lab, grd), pre, 'kahoot'))
    # ---- lsum: the PDFs, then the list page
    tmp = '/tmp/claude-0/arts_sum_%d/' % g; os.makedirs(tmp, exist_ok=True); jobs, pdfs = [], {}
    for f in glob.glob(R + d + 'lsum/*.pdf'): os.remove(f)
    for n, L in enumerate(les, 1):
        name = '%02d %s.pdf' % (n, re.sub(r'[\\/:*?"<>|]+', ' ', C[n]['deck']['title']).strip())
        src = tmp + 'L%02d.html' % n; open(src, 'w', encoding='utf8').write(summary_html(g, lab, L, C[n]['deck'], C[n]['summary'], n))
        os.makedirs(R + d + 'lsum', exist_ok=True); jobs.append([src, R + d + 'lsum/' + name]); pdfs['L%02d' % n] = {'s': name}
    open(tmp + 'jobs.json', 'w').write(json.dumps(jobs)); open(tmp + 'pdf.js', 'w').write(PDFJS)
    subprocess.run(['node', tmp + 'pdf.js', tmp + 'jobs.json'], check=True)
    LD = {'units': [{'name': U['name'], 'ids': ['L%02d' % n for n, L in enumerate(les, 1) if uid[L['unit']] == U['id']]} for U in units],
          'lessons': [{'id': 'L%02d' % n, 'title': C[n]['deck']['title']} for n in range(1, len(les) + 1)], 'pdfs': pdfs}
    write(d + 'lsum/index.html', A.lsum_page(g, lab, pre, LD, '/%s' % d + 'lsum/'))
    # ---- portal, catalogue, home list, badge
    B12 = read(T + 'index.html')
    for sec in ('slides', 'lsum', 'kahoot'):
        if sec != 'lsum':
            A.ICON[sec] = re.search(r'data-id="%s">\s*<div class="hd"><span class="ic">(.*?)</span>' % sec, B12, re.S).group(1)
        A.portal(d, sec, SEC[sec], DESC[sec] + ' – %s – الصف %s' % (lab, grd), AFTER[sec])
        A.catalogue(pre, sec, SEC[sec], AFTER[sec])
        __import__('mark_new').mark(d + sec)
    Lh = read('index.html').split('\n'); i = next(k for k, x in enumerate(Lh) if x.startswith('    %d:[' % g)); x = Lh[i]
    a = x.find("['arts/'")
    if a >= 0:
        b = x.index("']", a); seg = x[a:b]
        for t in SEC.values():
            if t not in seg: seg += ' · ' + t
        Lh[i] = x[:a] + seg + x[b:]; write('index.html', '\n'.join(Lh))
    print('done', d, len(les), 'lessons,', sum(len(L['slides']) for L in deck['lessons']), 'slides,', sum(len(x['q']) for x in D), 'kahoot questions')

if __name__ == '__main__':
    cdir = sys.argv[1]; gs = [int(x) for x in sys.argv[2:]] or sorted(int(p[-2:]) for p in glob.glob(os.path.join(cdir, 'g[0-9][0-9]')))
    for g in gs: build(g, cdir)
    sys.argv = [''] + ['%d/arts' % g for g in gs]; __import__('add_lesson_links').main()
    sys.argv = ['']; __import__('extract_imgs').main()
    subprocess.run([sys.executable, R + 'tools/dedupe_fonts.py', R, os.environ.get('AFUQ_FILES', '/home/user/afuq')], check=False)
