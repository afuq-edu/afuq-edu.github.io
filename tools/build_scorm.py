#!/usr/bin/env python3
"""SCORM 1.2 packages for منصة نور: one zip per lesson («ألعاب ونشاط الدرس»: three games + one activity; the pupil picks any of them and gets a certificate for
each one finished (owner, 2026-10-30), and a full certificate after all four).
Usage: python3 tools/build_scorm.py [grade/subject ...]      (default: every subject with a lesson-games page, /afuq/q/*/*)
Each package is self-contained (no internet needed inside Noor): the lesson page of /afuq/q/<g>/<s>/ with the quiz engine,
its stylesheet and the certificate font inside the zip, plus a small SCORM wrapper that
  - starts the attempt (cmi.core.lesson_status «incomplete»), takes the pupil's name from the LMS for the certificate,
  - sends the score after every game (cmi.core.score.raw = average of the finished games × 10) and «completed» once one is done,
  - keeps the progress in cmi.suspend_data, so a pupil who comes back on another device carries on.
Outside an LMS the page works as the normal lesson page. The zips are NOT stored on the site (2 700 lessons ≈ 250 MB, the
files repo is near the 1 GB Pages limit): /assets/scorm.js (written here from SCORM_JS + MANIFEST) builds a lesson's zip in the
teacher's browser from the lesson page data, the engine and the font when «تنزيل» is pressed. Output:
  assets/scorm.js                                  the in-browser builder
  <g>/<s>/scorm/index.html                        gold-only list page (download buttons, how to attach it in Noor)
  $SCORM_ZIP/<g>/<s>/L<NN>.zip                     only with SCORM_ZIP=<dir> (local tests; same files as the browser makes)
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
ZIPS = (os.environ.get('SCORM_ZIP', '').rstrip('/') + '/') if os.environ.get('SCORM_ZIP') else ''   # write the zips too (local tests)

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

CLIENT = r"""/* SCORM 1.2 packages for منصة نور, built in the teacher's browser (written by tools/build_scorm.py — edit it there).
   A «.scorm-dl» button (data-g, data-s, data-l) builds the zip of that lesson from files already on the site — the lesson page
   data (/afuq/q/<g>/<s>/), the quiz engine and the certificate font — so the site stores no zips. */
(function(){
'use strict';
var WRAP=__WRAP__, MAN=__MAN__;
var CRC=(function(){var t=[];for(var n=0;n<256;n++){var c=n;for(var k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
function crc32(b){var c=0xFFFFFFFF;for(var i=0;i<b.length;i++)c=CRC[(c^b[i])&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0;}
function zip(files){ /* [[name, Uint8Array]] → Blob (stored, no compression) */
  var enc=new TextEncoder(),parts=[],cen=[],off=0,D=((2026-1980)<<9)|(1<<5)|1;
  files.forEach(function(f){var nm=enc.encode(f[0]),d=f[1],c=crc32(d),h=new DataView(new ArrayBuffer(30));
    h.setUint32(0,0x04034b50,true);h.setUint16(4,20,true);h.setUint16(10,0,true);h.setUint16(12,D,true);
    h.setUint32(14,c,true);h.setUint32(18,d.length,true);h.setUint32(22,d.length,true);h.setUint16(26,nm.length,true);
    parts.push(new Uint8Array(h.buffer),nm,d);
    var e=new DataView(new ArrayBuffer(46));e.setUint32(0,0x02014b50,true);e.setUint16(4,20,true);e.setUint16(6,20,true);
    e.setUint16(14,D,true);e.setUint32(16,c,true);e.setUint32(20,d.length,true);e.setUint32(24,d.length,true);
    e.setUint16(28,nm.length,true);e.setUint32(38,0o644<<16,true);e.setUint32(42,off,true);cen.push(new Uint8Array(e.buffer),nm);
    off+=30+nm.length+d.length;});
  var cs=cen.reduce(function(a,x){return a+x.length;},0),z=new DataView(new ArrayBuffer(22));
  z.setUint32(0,0x06054b50,true);z.setUint16(8,files.length,true);z.setUint16(10,files.length,true);z.setUint32(12,cs,true);z.setUint32(16,off,true);
  return new Blob(parts.concat(cen,[new Uint8Array(z.buffer)]),{type:'application/zip'});}
function esc(x){return String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function js(o){return JSON.stringify(o).replace(/<\//g,'<\\/');}
function txt(u){return fetch(u,{cache:'no-cache'}).then(function(r){if(!r.ok)throw new Error(u);return r.text();});}
function bin(u){return fetch(u).then(function(r){if(!r.ok)throw new Error(u);return r.arrayBuffer();}).then(function(b){return new Uint8Array(b);});}
var cache={};
function build(g,s,l){
  var page=cache[g+'/'+s]||(cache[g+'/'+s]=txt('/afuq/q/'+g+'/'+s+'/'));
  return Promise.all([page,txt('/afuq/q/engine.js'),txt('/afuq/q/engine.css')]).then(function(r){
    var h=r[0],i=h.indexOf('window.QZ=')+10,d=JSON.parse(h.slice(i,h.indexOf(';</script>',i)));
    var L=d.L[l-1],fonts=[],css=r[2].replace(/url\(\/assets\/f\/([0-9a-f]+\.(?:ttf|woff2?|otf))\)/g,function(m,f){if(fonts.indexOf(f)<0)fonts.push(f);return 'url(fonts/'+f+')';});
    var title='ألعاب ونشاط الدرس – '+d.sn+' – الصف '+d.gn+' – '+L.t, dd=Object.assign({},d,{l:l});
    var doc='<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<title>'+esc(title)+
      '</title>\n<style>'+css+'</style></head><body><div id="app"></div>\n<script>window.SCORM_CFG='+js({key:'afuq-q:'+d.g+'/'+d.s+'/'+l})+';</script>\n<script>'+WRAP+
      '</script>\n<script>window.QZ='+js(dd)+';</script>\n<script>'+r[1].replace(/<\//g,'<\\/')+'</script></body></html>\n';
    return Promise.all(fonts.map(function(f){return bin('/assets/f/'+f);})).then(function(fb){
      var enc=new TextEncoder(),files=[['index.html',enc.encode(doc)]];fonts.forEach(function(f,k){files.push(['fonts/'+f,fb[k]]);});
      var names=files.map(function(f){return f[0];}).sort();
      var man=MAN.replace('%(id)s',g+'-'+s+'-L'+(l<10?'0':'')+l).split('%(title)s').join(esc(title))
        .replace('%(files)s',names.map(function(n){return '      <file href="'+n+'"/>';}).join('\n'));
      return zip([['imsmanifest.xml',enc.encode(man)]].concat(files.sort(function(a,b){return a[0]<b[0]?-1:1;})));});});}
document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('.scorm-dl');if(!b||b.disabled)return;e.preventDefault();
  var lab=b.innerHTML,g=b.dataset.g,s=b.dataset.s,l=+b.dataset.l;b.disabled=true;b.textContent='⏳ جارٍ التجهيز…';
  build(g,s,l).then(function(blob){var a=document.createElement('a'),u=URL.createObjectURL(blob);a.href=u;
    a.download='Afuq-'+s.toUpperCase()+'-G'+g+'-L'+(l<10?'0':'')+l+'.zip';document.body.appendChild(a);a.click();a.remove();
    setTimeout(function(){URL.revokeObjectURL(u);},4000);b.innerHTML='✔ تم التنزيل';setTimeout(function(){b.innerHTML=lab;b.disabled=false;},2500);})
  .catch(function(){b.innerHTML='⚠️ تعذّر التجهيز، حاول مرة أخرى';setTimeout(function(){b.innerHTML=lab;b.disabled=false;},3000);});});
window.afuqScorm=build;
})();
"""
def write_client():
    t = CLIENT.replace('__WRAP__', json.dumps(SCORM_JS, ensure_ascii=False)).replace('__MAN__', json.dumps(MANIFEST, ensure_ascii=False))
    p = R + 'assets/scorm.js'
    if not os.path.exists(p) or open(p, encoding='utf8').read() != t: open(p, 'w', encoding='utf8').write(t)

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
    out = ZIPS + '%s/%s/L%02d.zip' % (g, s, li + 1)
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
        items.append('<div class="row"><div class="t"><b>%d. %s</b><span>٣ ألعاب + نشاط، وشهادة لكلٍّ منها</span></div>'
                     '<span class="acts"><button type="button" class="btn go scorm-dl" data-g="%s" data-s="%s" data-l="%d">⬇️ تنزيل ملف السكورم</button>'
                     '<a class="btn" href="/afuq/q/%s/%s/?l=%d" target="_blank" rel="noopener">👁 معاينة</a></span></div>'
                     % (li + 1, esc(L['t']), g, s, li + 1, g, s, li + 1))
    note = ('<div class="note"><b>📎 الملف يُرفَق في «مرفقات المادة» في منصة نور:</b><ol>'
            '<li>اضغط «⬇️ تنزيل ملف السكورم» للدرس الذي تريده.</li>'
            '<li>في منصة نور افتح <b>مرفقات المادة</b>، وتحت عنوان الدرس اختر إضافة مرفق من نوع <b>SCORM</b>.</li>'
            '<li>ارفع ملف الـ zip <b>كاملًا كما هو دون فكّه</b> — لا ترفع ملف index وحده. ملف واحد لكل عنوان درس.</li></ol>'
            'يختار الطالب أي لعبة أو النشاط (١٠ درجات لكلٍّ منها)، وتظهر له شهادة باسمه لكل واحدة يُنهيها، دون أن يُلزَم بإنهاء الأربعة '
            '(ومن ينهي الأربعة يحصل أيضًا على الشهادة الكاملة)، وتصل درجته (معدّل ما أنهاه، من ١٠٠) وحالة الإكمال '
            'إلى نور تلقائيًا. الملف يعمل داخل نور دون الحاجة إلى موقعنا. (على الجوال قد يفكّ الآيفون الملف تلقائيًا؛ الأسهل الرفع من الكمبيوتر.)</div>')
    css = ('<style>:root{--bg:#f6f4ee;--card:#fff;--ink:#1f2a24;--muted:#66726c;--brand:#2f6fb3;--line:#ece4d2}'
           '@media (prefers-color-scheme:dark){:root{--bg:#141815;--card:#1d231f;--ink:#e8ede9;--muted:#9aa59f;--brand:#5b9be0;--line:#2b332e}}'
           '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,"Segoe UI",sans-serif;line-height:1.7}'
           'main{max-width:760px;margin:0 auto;padding:22px 16px 40px}a.back{color:var(--muted);text-decoration:none;font-size:14px}'
           'h1{margin:10px 0 4px;font-size:26px}p.sub{margin:0 0 18px;color:var(--muted)}h2.uh{margin:22px 0 6px;font-size:16px;color:var(--muted)}'
           '.row{display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:14px 16px;margin-top:8px;border-radius:16px;background:var(--card);border:1px solid var(--line);border-inline-start:6px solid var(--brand)}'
           '.row .t{flex:1 1 220px;display:flex;flex-direction:column}.row .t b{font-size:18px}.row .t span{color:var(--muted);font-size:14px}.acts{display:flex;flex-wrap:wrap;gap:6px}'
           '.btn{font:inherit;font-size:14px;font-weight:700;padding:8px 12px;border-radius:12px;border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer;text-decoration:none;white-space:nowrap}'
           '.btn.go{background:var(--brand);border-color:var(--brand);color:#fff}'
           '.note{background:var(--card);border:1px dashed var(--line);border-radius:14px;padding:12px 14px;color:var(--muted);font-size:14.5px;margin:0 0 16px}.note b{color:var(--ink)}.note ol{margin:6px 0 8px;padding-inline-start:22px}.note li{margin:2px 0}</style>')
    return ('<!doctype html><html lang="ar" dir="rtl"><head>' + guard +
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s – %s – الصف %s</title>' % (TITLE, lab, grd) + css +
            '</head><body><main><a class="back" href="../">→ %s – الصف %s</a><h1>📦 %s</h1><p class="sub">ملف سكورم لكل درس من %s للصف %s: ألعاب ونشاط وشهادة، يُرفَق في «مرفقات المادة» في منصة نور.</p>%s'
            '%s</main><script src="/assets/scorm.js"></script><script src="/assets/newbadge.js" defer></script></body></html>') % (lab, grd, TITLE, lab, grd, note, ''.join(items))

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
    if not m:   # a subject with the prep only: after it
        a = 'prep'; m = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="prep">.*?</button>\n', u, re.S)
    assert m, d
    ref = m.group(0)
    card = ref.replace('data-id="%s"' % a, 'data-id="scorm"', 1)
    card = re.sub(r'<h3>.*?</h3>', '<h3>%s</h3>' % TITLE, card)
    card = re.sub(r'<p>.*?</p>', '<p>%s – الصف %s: ملف سكورم لكل درس (ألعاب + شهادة) لمرفقات نور</p>' % (lab, GRADE[int(g)]), card, flags=re.S)
    card = re.sub(r'<span class="ic">.*?</span>', '<span class="ic">%s</span>' % ICON, card, count=1, flags=re.S)
    u = u.replace(ref, ref + card, 1) if a in ('games', 'prep') else u.replace(ref, card + ref, 1)
    k = re.search(r"    %s:\{title:[^\n]*\n" % a, u); assert k, (d, a)
    ins = "    scorm:{title:'%s',hash:null},\n" % TITLE
    if a == 'prep' and not k.group(0).rstrip().endswith(','):   # prep was the last entry
        u = u[:k.start()] + k.group(0).rstrip('\n') + ',\n' + u[k.end():]; k = re.search(r"    prep:\{title:[^\n]*\n", u)
        ins = ins.replace('},\n', '}\n')
    u = u[:k.end()] + ins + u[k.end():] if a in ('games', 'prep') else u[:k.start()] + ins + u[k.start():]
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
            if mm: seg = seg[:mm.start()] + '["scorm", "%s", true], ' % TITLE + seg[mm.start():]
            else:   # the prep is the only part: after it (j is on the «]]» that closes it and the list)
                v = v[:j + 1] + ', ["scorm", "%s", true]' % TITLE + v[j + 1:]; continue
        v = v[:i] + seg + v[j:]
    open(q, 'w', encoding='utf8').write(v)
    return cat

def main():
    only = [a.strip('/') for a in sys.argv[1:]] or sorted(p[len(F) + 2:-11] for p in glob.glob(F + 'q/*/*/index.html'))
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
            if ZIPS: L, size = package(g, s, h, d, li, eng, css, fonts); tot += size
            else: L = d['L'][li]
            rows.append((li, L, 0)); n += 1
        os.makedirs(R + gs + '/scorm', exist_ok=True)
        open(R + gs + '/scorm/index.html', 'w', encoding='utf8').write(list_page(g, s, d, rows, cat[gs + '/']['lock']))
        patch_portal(g, s, d['sn']); dirs.append(gs + '/'); mark_new.mark(gs + '/scorm')
        print('%-8s %2d SCORM packages' % (gs, len(rows)))
    patch_catalogue(dirs); write_client()
    print('%d lessons%s' % (n, ', zips %.1f MB in %s' % (tot / 1e6, ZIPS) if ZIPS else ''))

if __name__ == '__main__': main()
