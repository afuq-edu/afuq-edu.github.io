#!/usr/bin/env python3
"""Add a per-unit section: one self-contained HTML per unit plus a unit-chooser page.
Usage: python3 tools/add_units.py GRADE SUBJECT SECTION MODE UNIT1.html [UNIT2.html ...]   (files in unit order)
  A file may be given as 'LABEL::path' to show LABEL instead of 'الوحدة الأولى…' (e.g. 'Welcome::a.html').
  SECTION  e.g. harvest | prep | kahoot | homework
  MODE     gold     – locked to the gold package (guard on every page, like slides/board)
           free     – open to everyone (prep)
           homework – list page locked through /assets/hwgate.js, unit pages open for students
           open     – list page locked to the gold package, unit pages open for students (permanent links for Noor)
Creates <g>/<s>/<SECTION>/index.html and <SECTION>/u<N>/index.html. For SECTION=harvest it also adds the
portal card and the catalogue part (other sections are expected to exist in the portal already).
Rerunning replaces the pages."""
import re, os, sys, json
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
SUBJ = {'math':'الرياضيات','science':'العلوم','arabic':'اللغة العربية','english':'اللغة الإنجليزية','islamic':'التربية الإسلامية','social':'الهوية والمواطنة','physics':'الفيزياء','chemistry':'الكيمياء','biology':'الأحياء','it':'تقنية المعلومات'}
GRADE = {1:'الأول',2:'الثاني',3:'الثالث',4:'الرابع',5:'الخامس',6:'السادس',7:'السابع',8:'الثامن',9:'التاسع',10:'العاشر',11:'الحادي عشر',12:'الثاني عشر'}
UNITS = ['الأولى','الثانية','الثالثة','الرابعة','الخامسة','السادسة']
INFO = {  # section: (page title, emoji, intro, per-unit line)
 'harvest': ('حصاد الوحدات', '🌾', 'مراجعة كل وحدة في مسابقة ضد الوقت: نقاط لكل سؤال، شرح للإجابة النموذجية، وشهادة إنجاز باسم الطالب.', 'مسابقة ضد الوقت مع الإجابة النموذجية وشهادة إنجاز'),
 'prep':    ('ملف التحضير', '📝', 'نسخ حقول نور لكل حصة: اختر الوحدة ثم الدرس، وانسخ كل بند بضغطة واحدة.', 'نسخ حقول نور – تحضير منفصل ومدمج'),
 'kahoot':  ('مسابقة المجموعات', '🏆', 'مسابقة فرق داخل الصف لكل وحدة، تُعرض على الشاشة.', 'مسابقة بين مجموعات الصف'),
 'homework':('الواجبات', '📚', 'واجب لكل وحدة؛ أرسل رابط الوحدة للطلاب ليحلّوه.', 'واجب الوحدة – رابط للطلاب'),
}
MSG = {'harvest': 'مسابقة مراجعة للوحدة ضد الوقت، مع شرح الإجابة النموذجية بعد كل سؤال. في النهاية اكتب اسمك وصوّر شهادة الإنجاز وارفعها في نور. افتح الرابط:',
       'homework': 'واجب الوحدة: حلّ الأسئلة ثم صوّر شهادة الإنجاز وارفعها في نور. افتح الرابط:'}
def read(p): return open(R+p, encoding='utf8').read()
def guard(prefix, sec, back):
    return ("<script>(function(){var k='%s%s';function g(n,x){try{return window[n].getItem(x)==='1'}catch(e){return false}}"
            "if(g('localStorage',k)||g('sessionStorage',k)||g('localStorage','afuq-all')||g('sessionStorage','afuq-all'))return;"
            "document.documentElement.style.display='none';location.replace('%s?lock=%s')})()</script>") % (prefix, sec, back, sec)
PKG = '<script src="/assets/pkgmode.js" data-role="page"></script>'
def head_for(mode, prefix, sec, back, is_list):
    if mode == 'gold' or (mode == 'open' and is_list): return guard(prefix, sec, back) + PKG
    if mode == 'open': return PKG
    if mode == 'homework': return ('<script src="/assets/hwgate.js"></script>' if is_list else '') + PKG
    return PKG + '<script src="/assets/copyfix.js"></script>'
def main():
    g = int(sys.argv[1]); s = sys.argv[2]; sec = sys.argv[3]; mode = sys.argv[4]; files = sys.argv[5:]
    assert mode in ('gold', 'free', 'homework', 'open') and files
    lab, grd, d = SUBJ[s], GRADE[g], '%d/%s/' % (g, s)
    v = read('p/index.html')
    prefix = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', v).group(1))[d]['lock']
    title, emo, intro, line = INFO[sec]
    labels = [f.split('::', 1)[0] if '::' in f else 'الوحدة ' + (UNITS[i] if i < len(UNITS) else str(i+1)) for i, f in enumerate(files)]
    files = [f.split('::', 1)[1] if '::' in f else f for f in files]
    os.makedirs(R+d+sec, exist_ok=True)
    for i, f in enumerate(files, 1):
        h = open(f, encoding='utf8').read(); assert h.count('<head>') >= 1, f
        os.makedirs(R+d+sec+'/u%d' % i, exist_ok=True)
        open(R+d+sec+'/u%d/index.html' % i, 'w', encoding='utf8').write(h.replace('<head>', '<head>' + head_for(mode, prefix, sec, '../../', False), 1))
    share = mode in ('homework', 'open')
    if share:
        cards = ''.join('<div class="u row" data-u="u%d" data-name="%s – %s"><a class="t" href="u%d/"><b>%s</b><span>%s</span></a>'
                        '<div class="acts"><a class="btn go" href="u%d/">▶ تشغيل في الصف</a><button type="button" class="btn cp" data-k="link">🔗 نسخ الرابط</button>'
                        '<button type="button" class="btn cp" data-k="msg">📋 نسخ رسالة نور</button></div></div>'
                        % (i, title, labels[i-1], i, labels[i-1], line, i) for i in range(1, len(files)+1))
    else:
        cards = ''.join('<a class="u" href="u%d/"><b>%s</b><span>%s</span></a>' % (i, labels[i-1], line) for i in range(1, len(files)+1))
    note = ('<div class="note"><b>للمعلم:</b> لكل وحدة <b>رابط دائم</b> يفتحه الطلاب مباشرة بلا اشتراك ولا رمز. '
            'اضغط «نسخ رسالة نور» وألصقها في منصة نور (الواجبات أو المحتوى) فتصل للطلاب مع الرابط، أو «نسخ الرابط» وحده. '
            'وللعرض داخل الحصة اضغط «تشغيل في الصف».</div>') if share else ''
    js = ('<script>(function(){var S=%s,L=%s,G=%s;'
          'function cp(t,b,lab){function ok(){b.textContent=\'✔ تم النسخ\';b.classList.add(\'done\');setTimeout(function(){b.textContent=lab;b.classList.remove(\'done\')},1800)}'
          'function fb(){var a=document.createElement(\'textarea\');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand(\'copy\');ok()}catch(e){prompt(\'انسخ:\',t)}a.remove()}'
          'if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(ok,fb);else fb()}'
          'document.querySelectorAll(\'.row\').forEach(function(r){var u=new URL(r.dataset.u+\'/\',location.href).href;'
          'r.querySelectorAll(\'.cp\').forEach(function(b){var lab=b.textContent;b.onclick=function(){'
          'var t=b.dataset.k===\'msg\'?(r.dataset.name+\' – \'+S+\' – الصف \'+G+\'\\n\'+L+\'\\n\'+u):u;cp(t,b,lab)}})})})()</script>'
          ) % (json.dumps(lab, ensure_ascii=False), json.dumps(MSG.get(sec, ''), ensure_ascii=False), json.dumps(grd, ensure_ascii=False)) if share else ''
    page = ('<!doctype html><html lang="ar" dir="rtl"><head>' + head_for(mode, prefix, sec, '../', True) +
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s – %s – الصف %s</title>'
            '<style>:root{--bg:#f6f4ee;--card:#fff;--ink:#1f2a24;--muted:#66726c;--brand:#c27a12;--line:#ece4d2}'
            '@media (prefers-color-scheme:dark){:root{--bg:#141815;--card:#1d231f;--ink:#e8ede9;--muted:#9aa59f;--brand:#e7a93f;--line:#2b332e}}'
            '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,"Segoe UI",sans-serif;line-height:1.7}'
            'main{max-width:760px;margin:0 auto;padding:22px 16px 40px}a.back{color:var(--muted);text-decoration:none;font-size:14px}'
            'h1{margin:10px 0 4px;font-size:26px}p.sub{margin:0 0 18px;color:var(--muted)}'
            '.grid{display:grid;gap:12px}a.u{display:flex;flex-direction:column;gap:2px;padding:16px 18px;border-radius:16px;background:var(--card);'
            'border:1px solid var(--line);border-inline-start:6px solid var(--brand);color:inherit;text-decoration:none}'
            'a.u:hover{border-color:var(--brand)}a.u b,.row .t b{font-size:19px}a.u span,.row .t span{color:var(--muted);font-size:14px}'
            '.row{display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:14px 16px;border-radius:16px;background:var(--card);border:1px solid var(--line);border-inline-start:6px solid var(--brand)}'
            '.row .t{flex:1 1 220px;display:flex;flex-direction:column;color:inherit;text-decoration:none}.acts{display:flex;flex-wrap:wrap;gap:6px}'
            '.btn{font:inherit;font-size:14px;font-weight:700;padding:8px 12px;border-radius:12px;border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer;text-decoration:none;white-space:nowrap}'
            '.btn.go{background:var(--brand);border-color:var(--brand);color:#fff}.btn.done{background:#1f9d55;border-color:#1f9d55;color:#fff}'
            '.note{background:var(--card);border:1px dashed var(--line);border-radius:14px;padding:12px 14px;color:var(--muted);font-size:14.5px;margin:0 0 16px}'
            '.note b{color:var(--ink)}</style></head><body><main>'
            '<a class="back" href="../">→ %s – الصف %s</a><h1>%s %s</h1><p class="sub">%s</p>%s'
            '<div class="grid">%s</div></main>%s</body></html>') % (title, lab, grd, lab, grd, emo, title, intro, note, cards, js)
    open(R+d+sec+'/index.html', 'w', encoding='utf8').write(page)
    if sec == 'harvest': add_harvest_card(d, lab, grd, prefix, v)
    print('done', d+sec, mode, len(files), 'units')
def add_harvest_card(d, lab, grd, prefix, v):
    T = 'حصاد الوحدات'
    p = R+d+'index.html'; u = open(p, encoding='utf8').read()
    if 'data-id="harvest"' not in u:
        ref = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="(?:slides|board|kahoot)">.*?</button>\n', u, re.S).group(0)
        card = re.sub(r'data-id="[a-z]+"', 'data-id="harvest"', ref, count=1)
        card = re.sub(r'<h3>.*?</h3>', '<h3>%s</h3>' % T, card)
        card = re.sub(r'<p>.*?</p>', '<p>%s – %s – الصف %s: مسابقة مراجعة لكل وحدة</p>' % (T, lab, grd), card, flags=re.S)
        card = re.sub(r'<span class="ic">.*?</span>', '<span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21V9"/><path d="M12 9c0-3 2-5 5-5 0 3-2 5-5 5zM12 13c0-3-2-5-5-5 0 3 2 5 5 5zM12 17c0-3 2-5 5-5 0 3-2 5-5 5z"/></svg></span>', card, count=1, flags=re.S)
        a = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="(?:explorer|numbers|kahoot|homework)">', u).group(0)
        u = u.replace(a, card + a, 1)
        first = re.search(r"    (?:explorer|numbers|kahoot|homework):\{title:", u).group(0)
        u = u.replace(first, "    harvest:{title:'%s',hash:null},\n" % T + first, 1)
        open(p, 'w', encoding='utf8').write(u)
    o = '"lock": "%s", "parts": [' % prefix; assert v.count(o) == 1, prefix
    i = v.index(o); j = v.index(']]', i)
    if '"harvest"' not in v[i:j]:
        seg = v[i:j]
        for after in ('["board", "السبورات", true]', '["slides", "عروض باور بوينت", true]', '["prep", "ملف التحضير", false]'):
            if after in seg:
                seg = seg.replace(after, after + ', ["harvest", "%s", true]' % T, 1); break
        v = v[:i] + seg + v[j:]; open(R+'p/index.html', 'w', encoding='utf8').write(v)
main()
