#!/usr/bin/env python3
"""SCORM 1.2 packages for منصة نور: one zip per lesson («ألعاب ونشاط الدرس»: three games + one activity, then the certificate).
Usage: python3 tools/build_scorm.py [grade/subject ...]      (default: every تقنية المعلومات subject, */it)
Each package is self-contained (no internet needed inside Noor): the lesson page of /afuq/q/<g>/<s>/ with the quiz engine,
its stylesheet and the certificate font inside the zip, plus a small SCORM wrapper that
  - starts the attempt (cmi.core.lesson_status «incomplete»), takes the pupil's name from the LMS for the certificate,
  - sends the score after every game (cmi.core.score.raw = total / 40 × 100) and «completed» once all four are done,
  - keeps the progress in cmi.suspend_data, so a pupil who comes back on another device carries on.
Outside an LMS the page works as the normal lesson page. Output:
  $AFUQ_FILES/scorm/<g>/<s>/L<NN>.zip            (download: /afuq/scorm/<g>/<s>/L<NN>.zip)
  <g>/<s>/scorm/index.html                        gold-only list page (download buttons, how to add it in Noor)
plus the portal card, the SECTIONS entry, the catalogue part and the «جديد» badge. Rerun after build_quiz.py (zips are
byte-stable, so unchanged lessons do not change)."""
import re, os, sys, json, glob, html, zipfile, hashlib
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
F = os.environ.get('AFUQ_FILES', '/home/user/afuq').rstrip('/') + '/'
sys.path.insert(0, R + 'tools')
import mark_new
GRADE = {1:'الأول',2:'الثاني',3:'الثالث',4:'الرابع',5:'الخامس',6:'السادس',7:'السابع',8:'الثامن',9:'التاسع',10:'العاشر',11:'الحادي عشر',12:'الثاني عشر'}
TITLE = 'سكورم لمنصة نور'
ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 8v13H3V8"/><path d="M1 3h22v5H1z"/><path d="M10 12h4"/></svg>'
DEC = json.JSONDecoder()
FONT_RE = re.compile(r'url\(/assets/f/([0-9a-f]+\.(?:ttf|woff2?|otf))\)')
STAMP = (2026, 1, 1, 0, 0, 0)

def esc(x): return html.escape(str(x), quote=True)
def js(o): return json.dumps(o, ensure_ascii=False).replace('</', '<\\/')

SCORM_JS = r"""(function(){
/* SCORM 1.2 wrapper (tools/build_scorm.py): finds the LMS API, reports progress from the lesson engine's afuq-q events */
var C=window.SCORM_CFG||{},A=null,on=false,done=false,t0=Date.now();
function find(w){for(var n=0;w&&n<15;n++){try{if(w.API)return w.API;}catch(e){} if(w.parent&&w.parent!==w)w=w.parent;else break;}return null;}
A=find(window);if(!A&&window.opener)A=find(window.opener);
function get(k){try{return String(A.LMSGetValue(k)||'');}catch(e){return '';}}
function set(k,v){try{A.LMSSetValue(k,String(v));}catch(e){}}
function commit(){try{A.LMSCommit('');}catch(e){}}
if(A){try{var r=A.LMSInitialize('');on=(r===true||r==='true');}catch(e){}}
if(!on) return;
var st=get('cmi.core.lesson_status');done=(st==='completed'||st==='passed');
if(!st||st==='not attempted') set('cmi.core.lesson_status','incomplete');
set('cmi.core.score.min',0);set('cmi.core.score.max',100);
try{ /* progress from an earlier session (another device) */
  var sd=get('cmi.suspend_data');if(sd&&!localStorage.getItem(C.key))localStorage.setItem(C.key,sd);
  if(!localStorage.getItem('afuq-q-name')){var nm=get('cmi.core.student_name').trim();
    if(nm.indexOf(',')>0){var p=nm.split(',');nm=(p[1]+' '+p[0]).trim();}
    if(nm)localStorage.setItem('afuq-q-name',nm);}
}catch(e){}
commit();
window.addEventListener('afuq-q',function(ev){var d=ev.detail||{};
  if(d.st){set('cmi.suspend_data',JSON.stringify(d.st).slice(0,4000));
    set('cmi.core.score.raw',Math.round((d.total||0)*100/(d.max||40)));}
  if(d.done&&!done){done=true;set('cmi.core.lesson_status','completed');}
  commit();});
function fin(){if(!on)return;var s=Math.round((Date.now()-t0)/1000),h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;
  function p(n,w){n=String(n);while(n.length<w)n='0'+n;return n;}
  set('cmi.core.session_time',p(h,4)+':'+p(m,2)+':'+p(x,2));set('cmi.core.exit',done?'':'suspend');commit();
  try{A.LMSFinish('');}catch(e){}on=false;}
window.addEventListener('pagehide',fin);window.addEventListener('beforeunload',fin);
})();"""

MANIFEST = '''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="afuq-%(id)s" version="1.0"
  xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
  xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd http://www.imsglobal.org/xsd/imsmd_rootv1p2p1 imsmd_rootv1p2p1.xsd http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata><schema>ADL SCORM</schema><schemaversion>1.2</schemaversion></metadata>
  <organizations default="org">
    <organization identifier="org">
      <title>%(title)s</title>
      <item identifier="item1" identifierref="res1" isvisible="true">
        <title>%(title)s</title>
        <adlcp:masteryscore>50</adlcp:masteryscore>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res1" type="webcontent" adlcp:scormtype="sco" href="index.html">
%(files)s
    </resource>
  </resources>
</manifest>
'''

def package(g, s, page, d, li, eng, css, fonts):
    L = d['L'][li]
    title = '%s – %s – الصف %s – %s' % ('ألعاب ونشاط الدرس', d['sn'], d['gn'], L['t'])
    key = 'afuq-q:%s/%s/%d' % (d['g'], d['s'], li + 1)
    dd = dict(d, l=li + 1)
    css2 = FONT_RE.sub(lambda m: 'url(fonts/%s)' % m.group(1), css)
    doc = ('<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
           '<title>%s</title>\n<style>%s</style></head><body><div id="app"></div>\n'
           '<script>window.SCORM_CFG=%s;</script>\n<script>%s</script>\n'
           '<script>window.QZ=%s;</script>\n<script>%s</script></body></html>\n') % (
        esc(title), css2, js({'key': key}), SCORM_JS, js(dd), eng)
    files = {'index.html': doc.encode('utf8')}
    for f in fonts: files['fonts/' + f] = open(R + 'assets/f/' + f, 'rb').read()
    man = MANIFEST % {'id': '%s-%s-L%02d' % (g, s, li + 1), 'title': esc(title),
                      'files': '\n'.join('      <file href="%s"/>' % k for k in sorted(files))}
    files['imsmanifest.xml'] = man.encode('utf8')
    out = F + 'scorm/%s/%s/L%02d.zip' % (g, s, li + 1)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for k in ['imsmanifest.xml'] + sorted(x for x in files if x != 'imsmanifest.xml'):
            zi = zipfile.ZipInfo(k, STAMP); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
            z.writestr(zi, files[k])
    new = open(tmp, 'rb').read()
    if os.path.exists(out) and open(out, 'rb').read() == new: os.remove(tmp)
    else: os.replace(tmp, out)
    return L, os.path.getsize(out)

def list_page(g, s, d, rows, prefix):
    lab, grd = d['sn'], GRADE[int(g)]
    guard = ("<script>(function(){var k='%sscorm';function g(n,x){try{if(window[n].getItem(x)==='1')return true}catch(e){}try{return new RegExp('(^|; )'+x+'=1(;|$)').test(document.cookie)||(' '+window.name+' ').indexOf(' '+x+' ')>=0}catch(e){return false}}"
             "if(g('localStorage',k)||g('sessionStorage',k)||g('localStorage','afuq-all')||g('sessionStorage','afuq-all'))return;"
             "document.documentElement.style.display='none';location.replace('../?lock=scorm')})()</script>"
             '<script src="/assets/pkgmode.js" data-role="page"></script>') % prefix
    items, cur = [], None
    for li, L, size in rows:
        if L.get('u') != cur:
            cur = L.get('u'); items.append('<h2 class="uh">%s</h2>' % esc(cur or ''))
        name = 'Afuq-%s-G%s-L%02d.zip' % (s.upper(), g, li + 1)   # ASCII: browsers drop a non-ASCII download name ("download")
        url = '/afuq/scorm/%s/%s/L%02d.zip' % (g, s, li + 1)
        items.append('<div class="row"><div class="t"><b>%d. %s</b><span>٣ ألعاب + نشاط + شهادة · %d ك.ب</span></div>'
                     '<span class="acts"><a class="btn go" href="%s" download="%s">⬇️ تنزيل ملف السكورم</a>'
                     '<a class="btn" href="/afuq/q/%s/%s/?l=%d" target="_blank" rel="noopener">👁 معاينة</a></span></div>'
                     % (li + 1, esc(L['t']), round(size / 1024), url, esc(name), g, s, li + 1))
    note = ('<div class="note"><b>طريقة الإضافة في منصة نور:</b> نزّل ملف الدرس (zip) كما هو دون فكّه، ثم في نور أضف مرفقًا من نوع '
            '<b>SCORM</b> تحت عنوان الدرس وارفع الملف — ملف واحد لكل عنوان. يلعب الطالب الألعاب الثلاث ثم النشاط (١٠ درجات لكلٍّ منها)، '
            'وتظهر له شهادة باسمه في النهاية، وتصل درجته (من ١٠٠) وحالة الإكمال إلى نور تلقائيًا. الملف يعمل داخل نور دون الحاجة إلى موقعنا.</div>')
    css = ('<style>:root{--bg:#f6f4ee;--card:#fff;--ink:#1f2a24;--muted:#66726c;--brand:#2f6fb3;--line:#ece4d2}'
           '@media (prefers-color-scheme:dark){:root{--bg:#141815;--card:#1d231f;--ink:#e8ede9;--muted:#9aa59f;--brand:#5b9be0;--line:#2b332e}}'
           '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,"Segoe UI",sans-serif;line-height:1.7}'
           'main{max-width:760px;margin:0 auto;padding:22px 16px 40px}a.back{color:var(--muted);text-decoration:none;font-size:14px}'
           'h1{margin:10px 0 4px;font-size:26px}p.sub{margin:0 0 18px;color:var(--muted)}h2.uh{margin:22px 0 6px;font-size:16px;color:var(--muted)}'
           '.row{display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:14px 16px;margin-top:8px;border-radius:16px;background:var(--card);border:1px solid var(--line);border-inline-start:6px solid var(--brand)}'
           '.row .t{flex:1 1 220px;display:flex;flex-direction:column}.row .t b{font-size:18px}.row .t span{color:var(--muted);font-size:14px}.acts{display:flex;flex-wrap:wrap;gap:6px}'
           '.btn{font:inherit;font-size:14px;font-weight:700;padding:8px 12px;border-radius:12px;border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer;text-decoration:none;white-space:nowrap}'
           '.btn.go{background:var(--brand);border-color:var(--brand);color:#fff}'
           '.note{background:var(--card);border:1px dashed var(--line);border-radius:14px;padding:12px 14px;color:var(--muted);font-size:14.5px;margin:0 0 16px}.note b{color:var(--ink)}</style>')
    return ('<!doctype html><html lang="ar" dir="rtl"><head>' + guard +
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s – %s – الصف %s</title>' % (TITLE, lab, grd) + css +
            '</head><body><main><a class="back" href="../">→ %s – الصف %s</a><h1>📦 %s</h1><p class="sub">ملف سكورم لكل درس من %s للصف %s: ألعاب ونشاط وشهادة، يُرفع في مرفقات منصة نور.</p>%s'
            '%s</main><script src="/assets/newbadge.js" defer></script></body></html>') % (lab, grd, TITLE, lab, grd, note, ''.join(items))

ANCHORS = ('kahoot', 'homework', 'board', 'explorer')
def patch_portal(g, s, lab):
    d = '%s/%s/' % (g, s); p = R + d + 'index.html'; u = open(p, encoding='utf8').read()
    if 'data-id="scorm"' in u: return
    m = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="games">.*?</button>\n', u, re.S)
    a = 'games'
    if not m:
        for a in ANCHORS:
            m = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="%s">.*?</button>\n' % a, u, re.S)
            if m: break
    assert m, d
    ref = m.group(0)
    card = ref.replace('data-id="%s"' % a, 'data-id="scorm"', 1)
    card = re.sub(r'<h3>.*?</h3>', '<h3>%s</h3>' % TITLE, card)
    card = re.sub(r'<p>.*?</p>', '<p>%s – الصف %s: ملف سكورم لكل درس (ألعاب + شهادة) لمرفقات نور</p>' % (lab, GRADE[int(g)]), card, flags=re.S)
    card = re.sub(r'<span class="ic">.*?</span>', '<span class="ic">%s</span>' % ICON, card, count=1, flags=re.S)
    u = u.replace(ref, ref + card, 1) if a == 'games' else u.replace(ref, card + ref, 1)
    k = re.search(r"    %s:\{title:[^\n]*\n" % a, u); assert k, (d, a)
    ins = "    scorm:{title:'%s',hash:null},\n" % TITLE
    u = u[:k.end()] + ins + u[k.end():] if a == 'games' else u[:k.start()] + ins + u[k.start():]
    open(p, 'w', encoding='utf8').write(u)

def patch_catalogue(dirs):
    q = R + 'p/index.html'; v = open(q, encoding='utf8').read()
    m = re.search(r'var ICON=(\{.*?\});', v); ic = json.loads(m.group(1))
    if 'scorm' not in ic:
        ic['scorm'] = ICON; v = v[:m.start(1)] + json.dumps(ic, ensure_ascii=False) + v[m.end(1):]
    cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', v).group(1))
    for d in dirs:
        o = '"lock": "%s", "parts": [' % cat[d]['lock']; assert v.count(o) == 1, d
        i = v.index(o); j = v.index(']]', i); seg = v[i:j]
        if '"scorm"' in seg: continue
        mm = re.search(r'\["games", "[^"]*", (?:true|false)\]', seg)
        if mm: seg = seg[:mm.end()] + ', ["scorm", "%s", true]' % TITLE + seg[mm.end():]
        else:
            for a in ANCHORS:
                mm = re.search(r'\["%s", "[^"]*", (?:true|false)\]' % a, seg)
                if mm: break
            assert mm, d
            seg = seg[:mm.start()] + '["scorm", "%s", true], ' % TITLE + seg[mm.start():]
        v = v[:i] + seg + v[j:]
    open(q, 'w', encoding='utf8').write(v)
    return cat

def main():
    only = [a.strip('/') for a in sys.argv[1:]] or ['%d/it' % g for g in range(1, 13)]
    eng = open(R + 'tools/quiz/engine.js', encoding='utf8').read().replace('</', '<\\/')
    css = open(R + 'tools/quiz/engine.css', encoding='utf8').read()
    fonts = sorted(set(FONT_RE.findall(css)))
    cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', open(R + 'p/index.html', encoding='utf8').read()).group(1))
    dirs, n, tot = [], 0, 0
    for gs in only:
        g, s = gs.split('/')
        qp = F + 'q/%s/%s/index.html' % (g, s)
        if not os.path.exists(qp) or not os.path.exists(R + gs + '/index.html'): print('skip', gs); continue
        h = open(qp, encoding='utf8').read(); m = re.search(r'window\.QZ=', h); d, _ = DEC.raw_decode(h, m.end())
        rows = []
        for li in range(len(d['L'])):
            L, size = package(g, s, h, d, li, eng, css, fonts); rows.append((li, L, size)); n += 1; tot += size
        os.makedirs(R + gs + '/scorm', exist_ok=True)
        open(R + gs + '/scorm/index.html', 'w', encoding='utf8').write(list_page(g, s, d, rows, cat[gs + '/']['lock']))
        patch_portal(g, s, d['sn']); dirs.append(gs + '/'); mark_new.mark(gs + '/scorm')
        print('%-8s %2d SCORM packages' % (gs, len(rows)))
    patch_catalogue(dirs)
    print('%d packages, %.1f MB' % (n, tot / 1e6))

if __name__ == '__main__': main()
