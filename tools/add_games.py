#!/usr/bin/env python3
"""Add the «ألعاب وأنشطة منصة نور» section: student-facing, open copies of the interactive material with a permanent link per
lesson and per activity (for Noor).
 1. Interactive decks (window.DECK): lean copies that keep only the games / interactive activities; link per lesson (?l=ID).
 2. Ready-made game collections (explorer / explorer2 / numbers apps): open copies; link per lesson / per activity (?go=i.j.k)
    through tools/games_nav.json (made by tools/crawl_games_nav.js from tools/games_nav_levels.json); without a map, one link.
The source pages (interactive / lessons / slides / explorer / numbers) are only READ, never changed.

Usage: python3 tools/add_games.py            # every subject that has a deck on the new engine (window.DECK)
       python3 tools/add_games.py 5/math ...  # only these
Writes, per subject:
  $AFUQ_FILES/<g>/<s>/games/index.html   the student deck (open, no gold guard) -> /afuq/<g>/<s>/games/?l=<lessonId>
  <g>/<s>/games/index.html               the gold-only lesson list (copy link / Noor message), in this repo
and adds the portal card, the SECTIONS entry, the catalogue part, the home description and the «جديد» badge.
Push the files repo first, wait for its Pages deploy, then push this one."""
import re, os, sys, json, glob, html
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
F = os.environ.get('AFUQ_FILES', '/home/user/afuq').rstrip('/') + '/'
sys.path.insert(0, R + 'tools')
import fit_slides, mark_new, shutil
SUBJ = {'math':'الرياضيات','science':'العلوم','arabic':'اللغة العربية','english':'اللغة الإنجليزية','islamic':'التربية الإسلامية','social':'الدراسات الاجتماعية','physics':'الفيزياء','chemistry':'الكيمياء','biology':'الأحياء','it':'تقنية المعلومات','advmath':'الرياضيات المتقدمة','basicmath':'الرياضيات الأساسية'}
GRADE = {1:'الأول',2:'الثاني',3:'الثالث',4:'الرابع',5:'الخامس',6:'السادس',7:'السابع',8:'الثامن',9:'التاسع',10:'العاشر',11:'الحادي عشر',12:'الثاني عشر'}
TITLE = 'ألعاب وأنشطة منصة نور'
COLL = ('explorer', 'explorer2', 'numbers')   # ready-made game collections
# The ready-made collections block is switched off (owner's decision 2026-10-16: deep links into them felt disjointed).
# GAMES_COLL=1 python3 tools/add_games.py brings it back; the maps in tools/games_nav*.json are kept for that.
WITH_COLL = os.environ.get('GAMES_COLL') == '1'
NAV_FILE = R + 'tools/games_nav.json'
COLL_GUARD_RE = re.compile(r'<script>\(function\(\)\{var k=[^<]*?</script>\s*|<script src="/assets/pkgmode.js" data-role="page"></script>', re.S)
# slide types a student can solve on their own (teaching / discussion / teacher-led slides are left out)
GAMES = {'quiz', 'mcq', 'tf', 'match', 'sort', 'order', 'balloons', 'memory', 'riddle', 'boxes', 'mystery', 'build', 'fill',
         'compare', 'trace', 'wheel', 'race', 'web', 'code'}
MSG = 'ألعاب وأنشطة تفاعلية للدرس: افتح الرابط وحلّها بنفسك، ثم أرسل نتيجتك أو صورتها في نور إن طلب معلمك. افتح الرابط:'
GUARD_RE = re.compile(r'<script>\(function\(\)\{var k=.*?</script><script src="/assets/pkgmode.js" data-role="page"></script>', re.S)
ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<rect x="2" y="7" width="20" height="11" rx="5"/><path d="M7 10v5M4.5 12.5h5"/><circle cx="16" cy="11" r="1"/><circle cx="18.5" cy="14" r="1"/></svg>')
# ?l=<lessonId> keeps only that lesson (own counter, own saved position); no param = every lesson. Runs right after the DECK data.
LESSON_FILTER = (';(function(){var q=new URLSearchParams(location.search).get("l");if(!q)return;var D=window.DECK,L=D.lessons.filter(function(x){return x.id===q});'
                 'if(!L.length)return;D.lessons=L;D.units=(D.units||[]).filter(function(u){return u.id===L[0].unit});D.store+="-"+q})();')
def read(p): return open(R + p, encoding='utf8').read()
def js(o): return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')

def find_source(g, s):
    for sec in ('interactive', 'lessons', 'slides'):
        p = R + '%d/%s/%s/index.html' % (g, s, sec)
        if not os.path.exists(p): continue
        h = open(p, encoding='utf8').read()
        if 'window.DECK=' not in h: continue
        try: d = json.JSONDecoder().raw_decode(h[h.index('window.DECK=') + 12:])[0]
        except Exception: continue
        if isinstance(d, dict) and 'lessons' in d: return p, h, d
    return None

def build_student(h, d):
    """Return (student html, kept lessons) from a source deck (h: html, d: parsed DECK)."""
    i = h.index('window.DECK=') + 12; _, e = json.JSONDecoder().raw_decode(h[i:])
    lessons = []
    for L in d['lessons']:
        keep = [dict((k, v) for k, v in sl.items() if k != 'note') for sl in L['slides'] if sl['type'] == 'cover' or sl['type'] in GAMES]
        if any(sl['type'] in GAMES for sl in keep): lessons.append(dict(L, slides=keep))
    if not lessons: return None, []
    units = [u for u in d.get('units', []) if any(L.get('unit') == u.get('id') for L in lessons)]
    nd = dict(d, lessons=lessons, units=units, store=d['store'] + '-games',
              title=d['title'].replace('العرض التفاعلي', 'ألعاب وأنشطة').replace('Interactive lessons', 'Games & activities'))
    out = h[:i] + js(nd) + LESSON_FILTER + h[i + e:]
    # keep only the images the kept slides use
    if 'window.IMGS=' in out:
        j = out.index('window.IMGS=') + 12
        imgs, e2 = json.JSONDecoder().raw_decode(out[j:])
        txt = js(lessons)
        out = out[:j] + js({k: v for k, v in imgs.items() if k in txt}) + out[j + e2:]
    out = GUARD_RE.sub('', out, count=1)                      # the student copy is open (no gold guard)
    out = re.sub(r'<title>[^<]*</title>', '<title>%s</title>' % nd['title'], out, count=1)
    return out, lessons

def subj_label(g, s): return 'الهوية والمواطنة' if (s == 'social' and g <= 4) else SUBJ[s]
def esc(x): return html.escape(str(x), quote=True)
JUNK = re.compile(r'[\u200e\u200f\u202a-\u202e\u2066-\u2069\ufe0f]|[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B50\u25C0\u25B6]|لم يبدأ|أنجزت\s*[٠-٩0-9]+\s*من\s*[٠-٩0-9]+|[٠-٩0-9]+\s*(شرائح|دروس|نشاطًا|أنشطة)[^\n]*|ص\s*[0-9٠-٩\-]+|نشاط قبلي\s*الشرح\s*نشاط ختامي[^\n]*')
def short(t, n=80):
    t = JUNK.sub(' ', t); t = re.sub(r'[·•]+', ' ', t); t = re.sub(r'\s+', ' ', t).strip()
    return t if len(t) <= n else t[:n - 1].rstrip() + '…'

NAV_LOADER = (r"""<script>(function(){var N=window.__NAV,q=new URLSearchParams(location.search).get("go");if(!N||!q)return;
var P=q.split(".").map(Number);if(P.some(isNaN))return;
var steps=(N.pre||[]).map(function(p){return{sel:p.sel,idx:p.idx||0}}).concat(P.map(function(v,i){return{sel:N.levels[i],idx:v}}));
function vis(e){var r=e.getBoundingClientRect(),c=getComputedStyle(e);return r.width>4&&r.height>4&&c.visibility!=="hidden"&&c.display!=="none"}
function run(i){if(i>=steps.length)return;var s=steps[i],t=0;(function w(){var l=[].filter.call(document.querySelectorAll(s.sel),vis);
if(l.length>s.idx){l[s.idx].scrollIntoView({block:"center"});l[s.idx].click();setTimeout(function(){run(i+1)},700)}else if(t++<48)setTimeout(w,250)})()}
function go(){setTimeout(function(){run(0)},900)}if(document.readyState==="complete")go();else addEventListener("load",go)})();</script>""")

def load_nav():
    return json.load(open(NAV_FILE, encoding='utf8')) if os.path.exists(NAV_FILE) else {}

def build_collection(g, s, sec, nav):
    """Open copy of a ready-made game collection (guard removed); with a map it gets the ?go= deep-link loader."""
    src = R + '%d/%s/%s/index.html' % (g, s, sec)
    h = open(src, encoding='utf8').read()
    out = COLL_GUARD_RE.sub('', h)
    if nav:
        k = out.rindex('</body>')
        out = out[:k] + '<script>window.__NAV=' + js({'pre': nav.get('pre', []), 'levels': nav['levels']}) + '</script>' + NAV_LOADER + '\n' + out[k:]
    d = F + '%d/%s/games/%s/' % (g, s, sec); os.makedirs(d, exist_ok=True)
    open(d + 'index.html', 'w', encoding='utf8').write(out)
    return len(out)

def btns(): return ('<span class="acts"><a class="btn go" href="%s">▶ تشغيل</a><button type="button" class="btn cp" data-k="link">🔗 نسخ الرابط</button>'
                    '<button type="button" class="btn cp" data-k="msg">📋 نسخ رسالة نور</button></span>')

def row(url, name, title, sub, cls='row'):
    return ('<div class="u %s" data-u="%s" data-name="%s"><a class="t" href="%s"><b>%s</b><span>%s</span></a><div class="acts">'
            '<a class="btn go" href="%s">▶ تشغيل في الصف</a><button type="button" class="btn cp" data-k="link">🔗 نسخ الرابط</button>'
            '<button type="button" class="btn cp" data-k="msg">📋 نسخ رسالة نور</button></div></div>') % (cls, esc(url), esc(name), esc(url), esc(title), esc(sub), esc(url))

def tree_html(nodes, base, trail, path):
    out = []
    for i, n in enumerate(nodes):
        p = path + [i]; url = base + '?go=' + '.'.join(map(str, p)); t = short(n['t']); nm = ' – '.join(trail + [t])
        if n.get('k'):
            out.append('<details class="les" data-u="%s" data-name="%s"><summary><span class="lt">%s</span><span class="acts"><a class="btn go" href="%s">▶ تشغيل</a>'
                       '<button type="button" class="btn cp" data-k="link">🔗 نسخ الرابط</button><button type="button" class="btn cp" data-k="msg">📋 نسخ رسالة نور</button></span></summary>'
                       '<div class="kids">%s</div></details>' % (esc(url), esc(nm), esc(t), esc(url), tree_html(n['k'], base, trail + [t], p)))
        else:
            out.append('<div class="u row leaf" data-u="%s" data-name="%s"><span class="t"><b>%s</b></span><div class="acts"><a class="btn go" href="%s">▶ تشغيل</a>'
                       '<button type="button" class="btn cp" data-k="link">🔗 نسخ الرابط</button><button type="button" class="btn cp" data-k="msg">📋 نسخ رسالة نور</button></div></div>'
                       % (esc(url), esc(nm), esc(t), esc(url)))
    return ''.join(out)

def coll_block(g, s, sec, name, nav):
    base = '/afuq/%d/%s/games/%s/' % (g, s, sec)
    h = '<h2 class="uh">🎮 %s</h2>' % esc(name)
    h += row(base, '%s – %s' % (TITLE, name), 'افتح المجموعة كاملة', 'كل ألعاب وأنشطة «%s»' % name)
    if nav and nav.get('tree'): h += '<div class="tree">' + tree_html(nav['tree'], base, [name], []) + '</div>'
    return h

def list_page(g, s, prefix, lessons, units, colls):
    lab, grd = subj_label(g, s), GRADE[g]
    base = '/afuq/%d/%s/games/' % (g, s)
    guard = ("<script>(function(){var k='%sgames';function g(n,x){try{return window[n].getItem(x)==='1'}catch(e){return false}}"
             "if(g('localStorage',k)||g('sessionStorage',k)||g('localStorage','afuq-all')||g('sessionStorage','afuq-all'))return;"
             "document.documentElement.style.display='none';location.replace('../?lock=games')})()</script>"
             '<script src="/assets/pkgmode.js" data-role="page"></script>') % prefix
    uname = {u['id']: u.get('name', '') for u in units}
    rows, cur = [], None
    if lessons:
        rows.append('<h2 class="uh">🎬 من العرض التفاعلي</h2>')
        rows.append(row(base, '%s – كل دروس %s' % (TITLE, lab), 'كل الألعاب والأنشطة', 'رابط واحد يفتح ألعاب جميع الدروس'))
        for L in lessons:
            if L.get('unit') != cur:
                cur = L.get('unit'); rows.append('<h2 class="uh">%s</h2>' % esc(uname.get(cur) or ''))
            n = sum(1 for sl in L['slides'] if sl['type'] in GAMES)
            t = (L.get('code') + ' ' if L.get('code') else '') + L['title']
            rows.append(row(base + '?l=' + L['id'], '%s – %s' % (TITLE, t.strip()), t.strip(), '%d لعبة ونشاط' % n))
    for sec, name, nav in colls: rows.append(coll_block(g, s, sec, name, nav))
    note = ('<div class="note"><b>للمعلم:</b> لكل درس <b>رابط دائم</b> يفتحه الطلاب مباشرة بلا اشتراك ولا رمز، ويضم ألعاب وأنشطة ذلك الدرس فقط. '
            'وفي «المجموعات الجاهزة» لكل درس ولكل لعبة أو نشاط رابطه الخاص (اضغط على الدرس لترى أنشطته). '
            'اضغط «نسخ رسالة نور» وألصقها في منصة نور، أو «نسخ الرابط» وحده. وللعب داخل الحصة اضغط «تشغيل».</div>')
    script = ('<script>(function(){var S=%s,L=%s,G=%s;'
              'function cp(t,b,lab){function ok(){b.textContent=\'✔ تم النسخ\';b.classList.add(\'done\');setTimeout(function(){b.textContent=lab;b.classList.remove(\'done\')},1800)}'
              'function fb(){var a=document.createElement(\'textarea\');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand(\'copy\');ok()}catch(e){prompt(\'انسخ:\',t)}a.remove()}'
              'if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(ok,fb);else fb()}'
              'document.querySelectorAll(\'.cp\').forEach(function(b){var lab=b.textContent;b.onclick=function(e){e.preventDefault();e.stopPropagation();'
              'var r=b.closest(\'[data-u]\'),u=new URL(r.dataset.u,location.href).href;var t=b.dataset.k===\'msg\'?(r.dataset.name+\' – \'+S+\' – الصف \'+G+\'\\n\'+L+\'\\n\'+u):u;cp(t,b,lab)}})})()</script>'
              ) % (js(lab), js(MSG), js(grd))
    css = ('<style>:root{--bg:#f6f4ee;--card:#fff;--ink:#1f2a24;--muted:#66726c;--brand:#c27a12;--line:#ece4d2}'
           '@media (prefers-color-scheme:dark){:root{--bg:#141815;--card:#1d231f;--ink:#e8ede9;--muted:#9aa59f;--brand:#e7a93f;--line:#2b332e}}'
           '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,"Segoe UI",sans-serif;line-height:1.7}'
           'main{max-width:760px;margin:0 auto;padding:22px 16px 40px}a.back{color:var(--muted);text-decoration:none;font-size:14px}'
           'h1{margin:10px 0 4px;font-size:26px}p.sub{margin:0 0 18px;color:var(--muted)}h2.uh{margin:22px 0 6px;font-size:16px;color:var(--muted)}'
           '.grid>.row,.kids .row{margin-top:8px}'
           '.row{display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:14px 16px;border-radius:16px;background:var(--card);border:1px solid var(--line);border-inline-start:6px solid var(--brand)}'
           '.row .t{flex:1 1 220px;display:flex;flex-direction:column;color:inherit;text-decoration:none}.row .t b{font-size:18px}.row .t span{color:var(--muted);font-size:14px}.acts{display:flex;flex-wrap:wrap;gap:6px}'
           '.row.leaf{padding:9px 12px;border-radius:12px;border-inline-start-width:4px;background:transparent}.row.leaf .t b{font-size:15px;font-weight:600}'
           'details.les{margin-top:8px;border-radius:16px;background:var(--card);border:1px solid var(--line);border-inline-start:6px solid var(--brand)}'
           'details.les>summary{list-style:none;cursor:pointer;display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:12px 16px}details.les>summary::-webkit-details-marker{display:none}'
           'details.les>summary .lt{flex:1 1 220px;font-weight:700;font-size:17px}details.les>summary::before{content:"◂";color:var(--muted)}details.les[open]>summary::before{content:"▾"}'
           'details.les .kids{padding:0 12px 12px 12px}details.les details.les{background:transparent}'
           '.btn{font:inherit;font-size:14px;font-weight:700;padding:8px 12px;border-radius:12px;border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer;text-decoration:none;white-space:nowrap}'
           '.btn.go{background:var(--brand);border-color:var(--brand);color:#fff}.btn.done{background:#1f9d55;border-color:#1f9d55;color:#fff}'
           '.note{background:var(--card);border:1px dashed var(--line);border-radius:14px;padding:12px 14px;color:var(--muted);font-size:14.5px;margin:0 0 16px}'
           '.note b{color:var(--ink)}</style>')
    return ('<!doctype html><html lang="ar" dir="rtl"><head>' + guard +
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s – %s – الصف %s</title>' % (TITLE, lab, grd) + css +
            '</head><body><main><a class="back" href="../">→ %s – الصف %s</a><h1>🎮 %s</h1><p class="sub">ألعاب وأنشطة %s للصف %s، تصلح للطلاب في المنزل أو في الصف.</p>%s'
            '<div class="grid">%s</div></main>%s</body></html>') % (lab, grd, TITLE, lab, grd, note, ''.join(rows), script)

ANCHORS = ('board', 'kahoot', 'homework', 'explorer', 'numbers')
def patch_portal(g, s):
    d = '%d/%s/' % (g, s)
    p = R + d + 'index.html'; u = open(p, encoding='utf8').read()
    if 'data-id="games"' not in u:
        for a in ANCHORS:
            m = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="%s">.*?</button>\n' % a, u, re.S)
            if m: break
        assert m, d
        ref = m.group(0)
        card = ref.replace('data-id="%s"' % a, 'data-id="games"', 1)
        card = re.sub(r'<h3>.*?</h3>', '<h3>%s</h3>' % TITLE, card)
        card = re.sub(r'<p>.*?</p>', '<p>ألعاب وأنشطة %s – الصف %s: رابط دائم لكل درس وكل لعبة للطلاب</p>' % (subj_label(g, s), GRADE[g]), card, flags=re.S)
        card = re.sub(r'<span class="ic">.*?</span>', '<span class="ic">%s</span>' % ICON, card, count=1, flags=re.S)
        u = u.replace(ref, card + ref, 1)
        k = re.search(r"    %s:\{title:" % a, u); assert k, (d, a)
        u = u[:k.start()] + "    games:{title:'%s',hash:null},\n" % TITLE + u[k.start():]
        open(p, 'w', encoding='utf8').write(u)

def patch_catalogue(parts_by_dir):
    q = R + 'p/index.html'; v = open(q, encoding='utf8').read()
    m = re.search(r'var ICON=(\{.*?\});', v); ic = json.loads(m.group(1))
    if 'games' not in ic:
        ic['games'] = ICON; v = v[:m.start(1)] + json.dumps(ic, ensure_ascii=False) + v[m.end(1):]
    for d, prefix in parts_by_dir.items():
        o = '"lock": "%s", "parts": [' % prefix; assert v.count(o) == 1, prefix
        i = v.index(o); j = v.index(']]', i); seg = v[i:j]
        if '"games"' not in seg:
            for a in ANCHORS:
                mm = re.search(r'\["%s", "[^"]*", (?:true|false)\]' % a, seg)
                if mm: break
            assert mm, d
            seg = seg[:mm.start()] + '["games", "%s", true], ' % TITLE + seg[mm.start():]
            v = v[:i] + seg + v[j:]
    open(q, 'w', encoding='utf8').write(v)

def patch_home(done):
    p = R + 'index.html'; L = open(p, encoding='utf8').read().split('\n')
    for g, subs in done.items():
        idx = [k for k, x in enumerate(L) if x.startswith('    %d:[' % g)]
        if not idx: continue
        i = idx[0]; s = L[i]
        for sub in subs:
            if "['%s/'" % sub not in s: continue
            a = s.index("['%s/'" % sub); b = s.index("']", a); seg = s[a:b]
            if 'ألعاب وأنشطة' not in seg and ' · مسابقات كاهوت' in seg:
                s = s[:a] + seg.replace(' · مسابقات كاهوت', ' · ألعاب وأنشطة نور · مسابقات كاهوت', 1) + s[b:]
        L[i] = s
    open(p, 'w', encoding='utf8').write('\n'.join(L))

def remove_games(g, s):
    """Take a games section out of a subject that no longer has anything for it (portal card, catalogue part, hub line, badge, pages)."""
    d = '%d/%s/' % (g, s); hit = False
    p = R + d + 'index.html'; u = open(p, encoding='utf8').read()
    m = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="games">.*?</button>\n', u, re.S)
    if m: u = u.replace(m.group(0), '', 1); hit = True
    u = re.sub(r"    games:\{title:'[^']*',hash:null\},\n", '', u, count=1); open(p, 'w', encoding='utf8').write(u)
    q = R + 'p/index.html'; v = open(q, encoding='utf8').read()
    cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', v).group(1)); o = '"lock": "%s", "parts": [' % cat[d]['lock']
    i = v.index(o); j = v.index(']]', i); seg = v[i:j]; seg2 = seg.replace('["games", "%s", true], ' % TITLE, '')
    if seg2 != seg: v = v[:i] + seg2 + v[j:]; open(q, 'w', encoding='utf8').write(v); hit = True
    h = R + 'index.html'; L = open(h, encoding='utf8').read().split('\n')
    for k, x in enumerate(L):
        if x.startswith('    %d:[' % g) and "['%s/'" % s in x:
            a = x.index("['%s/'" % s); b = x.index("']", a); L[k] = x[:a] + x[a:b].replace(' · ألعاب وأنشطة نور', '') + x[b:]
    open(h, 'w', encoding='utf8').write('\n'.join(L))
    b = R + 'assets/newbadge.js'; t = open(b, encoding='utf8').read(); t2 = re.sub(r'"%sgames": "[^"]*",?\s*' % re.escape(d), '', t)
    if t2 != t: open(b, 'w', encoding='utf8').write(t2.replace(', }', '}').replace(',}', '}'))
    for base in (R, F):
        if os.path.isdir(base + d + 'games'): shutil.rmtree(base + d + 'games'); hit = True
    return hit

def main():
    only = set(a.strip('/') for a in sys.argv[1:])
    cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', read('p/index.html')).group(1))
    NAV = load_nav()
    done, prefixes, skipped, total, removed = {}, {}, [], 0, []
    for d in sorted(cat, key=lambda x: (int(x.split('/')[0]), x)):
        g, s = int(d.split('/')[0]), d.split('/')[1]
        if only and d.strip('/') not in only: continue
        if s not in SUBJ: continue
        src = find_source(g, s); lessons, units, info = [], [], []
        if src:
            sp, h, deck = src
            html_, lessons = build_student(h, deck)
            if html_:
                os.makedirs(F + d + 'games', exist_ok=True)
                open(F + d + 'games/index.html', 'w', encoding='utf8').write(html_)
                fit_slides.fix(F + d + 'games/index.html'); units = deck.get('units', [])
                info.append('deck %d lessons/%d games %.1fMB' % (len(lessons), sum(1 for L in lessons for sl in L['slides'] if sl['type'] in GAMES), os.path.getsize(F + d + 'games/index.html') / 1e6))
        colls = []
        for k, name, _ in cat[d]['parts']:
            if k in COLL and not WITH_COLL and os.path.isdir(F + d + 'games/' + k): shutil.rmtree(F + d + 'games/' + k)
            if k in COLL and WITH_COLL and os.path.exists(R + d + k + '/index.html'):
                nav = NAV.get('%d_%s_%s' % (g, s, k)); size = build_collection(g, s, k, nav); colls.append((k, name, nav))
                n = (lambda t: sum(1 + (len(x.get('k', [])) and 0) for x in t))(nav['tree']) if nav and nav.get('tree') else 0
                info.append('%s %.1fMB%s' % (k, size / 1e6, ' +map' if nav else ''))
        if not lessons and not colls:
            if remove_games(g, s): removed.append(d)
            skipped.append(d); continue
        prefix = cat[d]['lock']
        os.makedirs(R + d + 'games', exist_ok=True)
        open(R + d + 'games/index.html', 'w', encoding='utf8').write(list_page(g, s, prefix, lessons, units, colls))
        patch_portal(g, s); prefixes[d] = prefix; done.setdefault(g, []).append(s)
        mark_new.mark(d + 'games'); total += 1
        print('%-14s %s' % (d, ' | '.join(info)))
    patch_catalogue(prefixes); patch_home(done)
    print('done', total, 'subjects; skipped:', skipped, '; games section removed:', removed)
main()
