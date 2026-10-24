#!/usr/bin/env python3
"""Add a gold-only 'harvest' section (حصاد الوحدات): one self-contained HTML quiz per unit.
Usage: python3 tools/add_harvest.py GRADE SUBJECT UNIT1.html [UNIT2.html ...]   (in unit order)
Creates <g>/<s>/harvest/index.html (unit chooser) and harvest/u<N>/index.html, adds the portal card
and the catalogue part in p/index.html. Rerunning replaces the unit pages."""
import re, os, sys, json
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
SUBJ = {'math':'الرياضيات','science':'العلوم','arabic':'اللغة العربية','english':'اللغة الإنجليزية','islamic':'التربية الإسلامية','social':'الهوية والمواطنة','physics':'الفيزياء','chemistry':'الكيمياء','biology':'الأحياء','it':'تقنية المعلومات'}
GRADE = {1:'الأول',2:'الثاني',3:'الثالث',4:'الرابع',5:'الخامس',6:'السادس',7:'السابع',8:'الثامن',9:'التاسع',10:'العاشر',11:'الحادي عشر',12:'الثاني عشر'}
UNITS = ['الأولى','الثانية','الثالثة','الرابعة','الخامسة','السادسة']
TITLE = 'حصاد الوحدات'
def read(p): return open(R+p, encoding='utf8').read()
def guard(prefix, back):
    return ("<script>(function(){var k='%sharvest';function g(n,x){try{if(window[n].getItem(x)==='1')return true}catch(e){}try{return new RegExp('(^|; )'+x+'=1(;|$)').test(document.cookie)||(' '+window.name+' ').indexOf(' '+x+' ')>=0}catch(e){return false}}"
            "if(g('localStorage',k)||g('sessionStorage',k)||g('localStorage','afuq-all')||g('sessionStorage','afuq-all'))return;"
            "document.documentElement.style.display='none';location.replace('%s?lock=harvest')})()</script>"
            "<script src=\"/assets/pkgmode.js\" data-role=\"page\"></script>") % (prefix, back)
def main():
    g = int(sys.argv[1]); s = sys.argv[2]; files = sys.argv[3:]
    lab, grd, d = SUBJ[s], GRADE[g], '%d/%s/' % (g, s)
    v = read('p/index.html')
    prefix = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', v).group(1))[d]['lock']
    os.makedirs(R+d+'harvest', exist_ok=True)
    for i, f in enumerate(files, 1):
        h = open(f, encoding='utf8').read(); assert h.count('<head>') >= 1, f
        os.makedirs(R+d+'harvest/u%d' % i, exist_ok=True)
        open(R+d+'harvest/u%d/index.html' % i, 'w', encoding='utf8').write(h.replace('<head>', '<head>' + guard(prefix, '../../'), 1))
    cards = ''.join('<a class="u" href="u%d/"><b>الوحدة %s</b><span>مسابقة ضد الوقت مع الإجابة النموذجية وشهادة إنجاز</span></a>' % (i, UNITS[i-1]) for i in range(1, len(files)+1))
    page = ('<!doctype html><html lang="ar" dir="rtl"><head>' + guard(prefix, '../') +
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s – %s – الصف %s</title>'
            '<style>:root{--bg:#f6f4ee;--card:#fff;--ink:#1f2a24;--muted:#66726c;--brand:#c27a12;--line:#ece4d2}'
            '@media (prefers-color-scheme:dark){:root{--bg:#141815;--card:#1d231f;--ink:#e8ede9;--muted:#9aa59f;--brand:#e7a93f;--line:#2b332e}}'
            '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,"Segoe UI",sans-serif;line-height:1.7}'
            'main{max-width:760px;margin:0 auto;padding:22px 16px 40px}a.back{color:var(--muted);text-decoration:none;font-size:14px}'
            'h1{margin:10px 0 4px;font-size:26px}p.sub{margin:0 0 18px;color:var(--muted)}'
            '.grid{display:grid;gap:12px}a.u{display:flex;flex-direction:column;gap:2px;padding:16px 18px;border-radius:16px;background:var(--card);'
            'border:1px solid var(--line);border-inline-start:6px solid var(--brand);color:inherit;text-decoration:none}'
            'a.u:hover{border-color:var(--brand)}a.u b{font-size:19px}a.u span{color:var(--muted);font-size:14px}</style></head><body><main>'
            '<a class="back" href="../">→ %s – الصف %s</a><h1>🌾 %s</h1>'
            '<p class="sub">مراجعة كل وحدة من %s للصف %s في مسابقة ضد الوقت: نقاط لكل سؤال، شرح للإجابة النموذجية، وشهادة إنجاز باسم الطالب.</p>'
            '<div class="grid">%s</div></main></body></html>') % (TITLE, lab, grd, lab, grd, TITLE, lab, grd, cards)
    open(R+d+'harvest/index.html', 'w', encoding='utf8').write(page)
    # portal card + section title
    p = R+d+'index.html'; u = open(p, encoding='utf8').read()
    if 'data-id="harvest"' not in u:
        ref = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="slides">.*?</button>\n', u, re.S).group(0)
        card = re.sub(r'data-id="slides"', 'data-id="harvest"', ref)
        card = re.sub(r'<h3>.*?</h3>', '<h3>%s</h3>' % TITLE, card)
        card = re.sub(r'<p>.*?</p>', '<p>%s – %s – الصف %s: مسابقة مراجعة لكل وحدة</p>' % (TITLE, lab, grd), card, flags=re.S)
        card = re.sub(r'<span class="ic">.*?</span>', '<span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21V9"/><path d="M12 9c0-3 2-5 5-5 0 3-2 5-5 5zM12 13c0-3-2-5-5-5 0 3 2 5 5 5zM12 17c0-3 2-5 5-5 0 3-2 5-5 5z"/></svg></span>', card, count=1, flags=re.S)
        a = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="(?:explorer|numbers|kahoot|homework)">', u).group(0)
        u = u.replace(a, card + a, 1)
        first = re.search(r"    (?:explorer|numbers|kahoot|homework):\{title:", u).group(0)
        u = u.replace(first, "    harvest:{title:'%s',hash:null},\n" % TITLE + first, 1)
        open(p, 'w', encoding='utf8').write(u)
    # catalogue part (after board, else after slides)
    o = '"lock": "%s", "parts": [' % prefix; assert v.count(o) == 1, prefix
    i = v.index(o); j = v.index(']]', i)
    if '"harvest"' not in v[i:j]:
        seg = v[i:j]
        for after in ('["board", "السبورات", true]', '["slides", "عروض باور بوينت", true]'):
            if after in seg:
                seg = seg.replace(after, after + ', ["harvest", "%s", true]' % TITLE, 1); break
        else:
            seg = seg.replace('["prep", "ملف التحضير", false]', '["prep", "ملف التحضير", false], ["harvest", "%s", true]' % TITLE, 1)
        v = v[:i] + seg + v[j:]; open(R+'p/index.html', 'w', encoding='utf8').write(v)
    print('done', d, len(files), 'units')
main()
