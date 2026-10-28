#!/usr/bin/env python3
"""A subject's gold package from per-lesson content (owner, 2026-10-28: «ابنِ التحضير الناقص والباقات الذهبية … وفق العرض وفكرته
وأسلوبه وشكل الشرائح»), on the engines of the grade-12 biology package (same look, same games):
  slides   («عروض باور بوينت»: the interactive deck, window.DECK) → then add_lesson_links (lesson list + student pages) and add_games
  harvest  (حصاد الوحدات: one quiz per unit, tools/add_harvest.py)
  kahoot   (مسابقات كاهوت: the group contest, every lesson and period)
  homework (الواجبات: per lesson a race, a catch game and an activity, 10 questions each)
Usage: python3 tools/add_gold_pack.py GRADE SUBJECT CONTENT_DIR
  CONTENT_DIR/<lesson id>.json = {"deck": {"id","title","code","emo","theme","slides":[…]}, "harvest": [8 × {t,q,o,a,why}],
  "kahoot": [[period, level, m|t|f, question, correct, wrong…]], "homework": [10 × {t,q,o,a}]}
  Lessons, units and periods come from the subject's prep pages (#json lists in <g>/<s>/prep/u*/index.html), in their order.
Writes the section pages, the portal cards and SECTIONS entries, the catalogue parts in p/index.html, the homework unlock prefix
(assets/hwgate.js) and the «جديد» badge. Rerunning replaces the pages. Then push the files repo first (student pages, games),
wait for its deploy, then push this repo; update the links program («links» collection) to match CAT."""
import re, os, sys, json, glob, shutil, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
T = '12/biology/'                                   # the template package
DEC = json.JSONDecoder()
SUBJ = {'envsci': 'العلوم البيئية'}
GRADE = {9: 'التاسع', 10: 'العاشر', 11: 'الحادي عشر', 12: 'الثاني عشر'}
UNITS_AR = ['الأولى', 'الثانية', 'الثالثة', 'الرابعة', 'الخامسة', 'السادسة']
ICON = {'envsci': '🌍'}
THEMES = ['garden', 'park', 'maproom', 'lab', 'city', 'heritage']

def read(p): return open(R + p, encoding='utf8').read()
def write(p, t):
    os.makedirs(os.path.dirname(R + p), exist_ok=True); open(R + p, 'w', encoding='utf8').write(t)
def js(o): return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
def swap(h, pat, obj):
    m = re.search(pat, h); o, e = DEC.raw_decode(h, m.end()); return h[:m.end()] + js(obj) + h[e:]

def lessons_of(g, s):
    """[{id, title, unit, unit_id, periods:[axis…]}] from the prep pages"""
    import build_quiz as B
    out = []
    for k, p in enumerate(sorted(glob.glob(R + '%d/%s/prep/u*/index.html' % (g, s)), key=lambda x: int(re.search(r'/u(\d+)/', x).group(1))), 1):
        for n, i, e, o in B.literals(open(p, encoding='utf8').read()):
            if n == '#json':
                for L in o: out.append({'id': L['id'], 'title': L['title'], 'unit': L['unit'], 'unit_id': 'U%d' % k, 'periods': [x['axis'] for x in L['periods']]})
    return out

def texts(h, g, s):
    lab, grd = SUBJ[s], GRADE[g]
    h = h.replace('الأحياء – الصف الثاني عشر', '%s – الصف %s' % (lab, grd)).replace('أحياء – الصف الثاني عشر', '%s – الصف %s' % (lab, grd))
    h = h.replace('حصاد - الأحياء - الصف الثاني عشر', 'حصاد - %s - الصف %s' % (lab, grd))
    h = h.replace('الأحياء · الصف الثاني عشر', '%s · الصف %s' % (lab, grd)).replace('· الأحياء ·', '· %s ·' % lab).replace('· واجب منزلي · الأحياء', '· واجب منزلي · ' + lab)
    return h.replace('12/biology/', '%d/%s/' % (g, s))

def guard_key(h, pre, sec): return re.sub(r"var k='ofuq-g12l-unlock-%s'" % sec, "var k='%s%s'" % (pre, sec), h)

def build(g, s, cdir):
    d = '%d/%s/' % (g, s); lab, grd = SUBJ[s], GRADE[g]
    v = read('p/index.html'); cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', v).group(1)); pre = cat[d]['lock']
    les = lessons_of(g, s)
    C = {L['id']: json.load(open(os.path.join(cdir, L['id'] + '.json'), encoding='utf8')) for L in les if os.path.exists(os.path.join(cdir, L['id'] + '.json'))}
    les = [L for L in les if L['id'] in C]
    units = []
    for L in les:
        if not units or units[-1]['id'] != L['unit_id']: units.append({'id': L['unit_id'], 'name': L['unit'], 'theme': THEMES[len(units) % len(THEMES)]})
    # ---- slides
    deck = {'title': 'العرض التفاعلي – %s – الصف %s' % (lab, grd), 'sub': 'الفصل الدراسي الأول', 'store': 'deck2-g%d-%s' % (g, s),
            'cfg': {'lang': 'ar', 'icon': ICON[s], 'wicon': '🌿', 'welcome': 'مرحبًا بكم في عالم %s' % lab, 'mascot': 'OWL', 'kids': False},
            'units': units, 'lessons': []}
    for L in les:
        dk = C[L['id']]['deck']
        deck['lessons'].append({'id': L['id'], 'unit': L['unit_id'], 'unitName': L['unit'], 'title': dk['title'], 'code': dk['code'],
                                'theme': dk.get('theme') or 'garden', 'emo': dk.get('emo') or ICON[s], 'slides': dk['slides']})
    h = read(T + 'slides/index.html')
    h = swap(h, r'window\.DECK=', deck); h = swap(h, r'window\.IMGS=', {})
    write(d + 'slides/index.html', guard_key(texts(h, g, s), pre, 'slides'))
    # ---- kahoot
    D = [{'t': L['title'], 'u': 'الوحدة %d' % int(L['unit_id'][1:]), 'p': L['periods'], 'q': C[L['id']]['kahoot']} for L in les]
    h = read(T + 'kahoot/index.html')
    write(d + 'kahoot/index.html', guard_key(texts(swap(h, r'const D=', D), g, s), pre, 'kahoot'))
    # ---- homework
    hl = [{'id': 'l%d' % i, 'unit': 'الوحدة %d' % int(L['unit_id'][1:]), 'title': L['title']} for i, L in enumerate(les, 1)]
    write(d + 'homework/index.html', texts(swap(read(T + 'homework/index.html'), r'var L=', hl), g, s))
    for f in glob.glob(R + d + 'homework/l*/'): shutil.rmtree(f)
    t0 = 'تركيب DNA وRNA'
    for i, L in enumerate(les, 1):
        for sub in ('', 'race/', 'catch/', 'activity/'):
            h = read(T + 'homework/l1/' + sub + 'index.html')
            if sub: h = swap(h, r'var BANK=', C[L['id']]['homework'])
            write(d + 'homework/l%d/%sindex.html' % (i, sub), texts(h.replace(t0, L['title']), g, s))
    hw = read('assets/hwgate.js')
    if '"%s":' % d not in hw: write('assets/hwgate.js', hw.replace('var L={', 'var L={"%s":"%s",' % (d, pre), 1))
    # ---- portal cards, SECTIONS, catalogue
    P = read(d + 'index.html'); B12 = read(T + 'index.html')
    order = ['prep', 'slides', 'games', 'scorm', 'harvest', 'kahoot', 'homework']
    titles = {'slides': 'عروض باور بوينت', 'kahoot': 'مسابقات كاهوت', 'homework': 'الواجبات', 'harvest': 'حصاد الوحدات'}
    for sec in ('slides', 'kahoot', 'homework'):
        if 'data-id="%s"' % sec in P: continue
        card = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="%s">.*?</button>\n' % sec, B12, re.S).group(0)
        card = card.replace('أحياء الصف الثاني عشر', '%s – الصف %s' % (lab, grd)).replace('واجبات أحياء', 'واجبات ' + lab)
        card = texts(card, g, s)
        prev = [x for x in order[:order.index(sec)] if 'data-id="%s"' % x in P][-1]
        m = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="%s">.*?</button>\n' % prev, P, re.S)
        P = P[:m.end()] + card + P[m.end():]
        e = re.search(r"    %s:\{title:'[^']*',hash:null\},?\n" % prev, P)
        line = e.group(0); entry = "    %s:{title:'%s',hash:null}" % (sec, titles[sec])
        P = P.replace(line, (line if line.rstrip().endswith(',') else line.rstrip('\n') + ',\n') + entry + (',\n' if line.rstrip().endswith(',') else '\n'), 1)
    write(d + 'index.html', P)
    v = read('p/index.html'); o = '"lock": "%s", "parts": [' % pre; i = v.index(o); j = v.index(']]', i) + 1; seg = v[i:j]
    for sec in ('slides', 'kahoot', 'homework'):
        if '"%s"' % sec in seg: continue
        prev = [x for x in order[:order.index(sec)] if '["%s"' % x in seg][-1]
        m = re.search(r'\["%s", "[^"]*", (?:true|false)\]' % prev, seg)
        seg = seg[:m.end()] + ', ["%s", "%s", true]' % (sec, titles[sec]) + seg[m.end():]
    write('p/index.html', v[:i] + seg + v[j:])
    # ---- harvest (one quiz page per unit, installed by add_harvest)
    tmp = '/tmp/claude-0/gold_%d_%s/' % (g, s); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    ht = read(T + 'harvest/u1/index.html').replace('<head><script src="/assets/pkgmode.js" data-role="page"></script>', '<head>', 1)   # add_harvest puts the guard back
    files = []
    for k, U in enumerate(units, 1):
        qs = [dict(q, l=L['id'], sec=3) for L in les if L['unit_id'] == U['id'] for q in C[L['id']]['harvest']]
        H = {'subject': lab, 'grade': 'الصف ' + grd, 'semester': 'الفصل الدراسي الأول', 'unit': U['name'], 'unitShort': 'الوحدة ' + UNITS_AR[k - 1],
             'key': 'g%d-%s-%s' % (g, s, U['id']), 'kids': False, 'lang': 'ar', 'icon': ICON[s],
             'lessons': [{'id': L['id'], 'title': C[L['id']]['deck']['title']} for L in les if L['unit_id'] == U['id']], 'qs': qs}
        f = tmp + 'u%d.html' % k; open(f, 'w', encoding='utf8').write(texts(swap(ht, r'const H=', H), g, s)); files.append(f)
    subprocess.run([sys.executable, R + 'tools/add_harvest.py', str(g), s] + files, check=True)
    for sec in ('slides', 'kahoot', 'homework'): __import__('mark_new').mark(d + sec)
    # ---- lesson links (student pages), games, images, fonts
    sys.argv = ['', '%d/%s' % (g, s)]; __import__('add_lesson_links').main()
    subprocess.run([sys.executable, R + 'tools/add_games.py', '%d/%s' % (g, s)], check=True)
    sys.argv = ['']; __import__('extract_imgs').main()
    subprocess.run([sys.executable, R + 'tools/dedupe_fonts.py', R, os.environ.get('AFUQ_FILES', '/home/user/afuq')], check=False)
    print('done', d, len(les), 'lessons,', sum(len(L['slides']) for L in deck['lessons']), 'slides,', len(units), 'units')

if __name__ == '__main__':
    build(int(sys.argv[1]), sys.argv[2], sys.argv[3])
