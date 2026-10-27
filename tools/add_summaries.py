#!/usr/bin/env python3
"""«الملخصات» (owner, 2026-10-27): for every lesson a full one-page summary («الملخص الشامل») and a mind map («الخريطة
الذهنية»), PDFs made by the owner, plus (when sent) one file with all of them. Gold-only section.
Usage: python3 tools/add_summaries.py GRADE SUBJECT MANIFEST.json
  MANIFEST: {"lessons": [{"code": "1-1", "t": title, "unit": unit name, "s": summary.pdf, "m": mind-map.pdf}, …], "all": all.pdf or null}
PDFs go (compressed, tools/compress_pdf.py) to the files repo: <g>/<s>/summaries/<code>-s.pdf, <code>-m.pdf, all.pdf.
Writes <g>/<s>/summaries/index.html (units → lessons, two buttons each), the portal card, the catalogue part in p/index.html
and the «جديد» badge. Push the files repo first, wait for its deploy, then push this repo; then add the part to the links
program (collection links, the subject's «parts»)."""
import re, os, sys, json, html as H, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
F = os.environ.get('AFUQ_FILES', '/home/user/afuq').rstrip('/') + '/'
sys.path.insert(0, R + 'tools')
SUBJ = {'math': 'الرياضيات', 'science': 'العلوم', 'arabic': 'اللغة العربية', 'english': 'اللغة الإنجليزية', 'islamic': 'التربية الإسلامية',
        'social': 'الدراسات الاجتماعية', 'physics': 'الفيزياء', 'chemistry': 'الكيمياء', 'biology': 'الأحياء', 'it': 'تقنية المعلومات'}
GRADE = {1: 'الأول', 2: 'الثاني', 3: 'الثالث', 4: 'الرابع', 5: 'الخامس', 6: 'السادس', 7: 'السابع', 8: 'الثامن', 9: 'التاسع', 10: 'العاشر', 11: 'الحادي عشر', 12: 'الثاني عشر'}
TITLE, KEY = 'الملخصات', 'summaries'
ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5"/><circle cx="12" cy="14" r="1.6"/><path d="M12 12.4V10M13.4 15l2 1.2M10.6 15l-2 1.2"/></svg>')

def fname(code): return code.replace('أ', 'a').replace('ب', 'b').replace('ج', 'c')

def guard(prefix):
    return ("<script>(function(){var k='%s%s';function g(n,x){try{if(window[n].getItem(x)==='1')return true}catch(e){}try{return new RegExp('(^|; )'+x+'=1(;|$)').test(document.cookie)||(' '+window.name+' ').indexOf(' '+x+' ')>=0}catch(e){return false}}"
            "if(g('localStorage',k)||g('sessionStorage',k)||g('localStorage','afuq-all')||g('sessionStorage','afuq-all'))return;"
            "document.documentElement.style.display='none';location.replace('../?lock=%s')})()</script>"
            "<script src=\"/assets/pkgmode.js\" data-role=\"page\"></script>") % (prefix, KEY, KEY)

def compress(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    subprocess.check_output([sys.executable, R + 'tools/compress_pdf.py', src, dst])

def unit_label(u, k):
    u = re.sub(r'^\s*[0-9٠-٩]+\s*[.)-]\s*', '', u or '').strip()
    return u if u.startswith('الوحدة') else ('الوحدة %d%s' % (k, (': ' + u) if u else ''))

def page(g, s, lab, grd, prefix, lessons, has_all):
    base = '/afuq/%d/%s/%s/' % (g, s, KEY)
    units, order = {}, []
    for e in lessons:
        u = e['unit']
        if u not in units: units[u] = []; order.append(u)
        units[u].append(e)
    body = ''
    for k, u in enumerate(order, 1):
        rows = ''.join(
            '<div class="row"><div class="t"><span class="code">%s</span><b>%s</b></div><div class="acts">'
            '<a class="btn go" href="%s%s-s.pdf" target="_blank" rel="noopener">📄 الملخص الشامل</a>'
            '<a class="btn" href="%s%s-m.pdf" target="_blank" rel="noopener">🧠 الخريطة الذهنية</a></div></div>'
            % (H.escape(re.sub(r'([أبج])$', r' \1', e['code'])), H.escape(e['t']), base, fname(e['code']), base, fname(e['code'])) for e in units[u])
        body += '<section class="unit"><h2>%s</h2>%s</section>' % (H.escape(unit_label(u, k)), rows)
    allbtn = ('<a class="btn all" href="%sall.pdf" target="_blank" rel="noopener">📥 كل الملخصات والخرائط الذهنية في ملف واحد</a>' % base) if has_all else ''
    return ('<!doctype html><html lang="ar" dir="rtl"><head>' + guard(prefix) +
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>%s – %s – الصف %s</title>'
            '<style>:root{--bg:#f6f4ee;--card:#fff;--ink:#1f2a24;--muted:#66726c;--brand:#2E6F73;--line:#e6e0d2;--soft:#eef5f4}'
            '@media (prefers-color-scheme:dark){:root{--bg:#141815;--card:#1d231f;--ink:#e8ede9;--muted:#9aa59f;--brand:#5fb3b8;--line:#2b332e;--soft:#1f2b2a}}'
            '*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,"Segoe UI",sans-serif;line-height:1.7}'
            'main{max-width:820px;margin:0 auto;padding:22px 16px 40px}a.back{color:var(--muted);text-decoration:none;font-size:14px}'
            'h1{margin:10px 0 4px;font-size:26px}p.sub{margin:0 0 14px;color:var(--muted)}'
            '.unit{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:6px 16px 10px;margin:0 0 14px}'
            '.unit h2{font-size:17px;margin:10px 0 6px;color:var(--brand)}'
            '.row{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;padding:10px 0;border-top:1px dashed var(--line)}'
            '.row .t{flex:1 1 220px;display:flex;gap:8px;align-items:baseline}.code{font-size:13px;color:var(--muted);direction:ltr;unicode-bidi:isolate;min-width:2.6em}'
            '.acts{display:flex;flex-wrap:wrap;gap:6px}.btn{font:inherit;font-size:14px;font-weight:700;padding:7px 12px;border-radius:12px;border:1px solid var(--line);'
            'background:var(--soft);color:var(--ink);text-decoration:none;white-space:nowrap}.btn.go{background:var(--brand);border-color:var(--brand);color:#fff}'
            '.btn.all{display:inline-block;margin:0 0 16px;background:var(--brand);border-color:var(--brand);color:#fff}</style></head><body><main>'
            '<a class="back" href="../">→ %s – الصف %s</a><h1>📚 %s</h1>'
            '<p class="sub">لكل درس ملخص شامل في صفحة واحدة، وخريطة ذهنية في صفحة. اضغط لفتح الملف، ومن العارض يمكنك تحميله أو طباعته.</p>%s%s'
            '</main></body></html>') % (TITLE, lab, grd, lab, grd, TITLE, allbtn, body)

def portal(d, lab, grd):
    p = R + d + 'index.html'; u = open(p, encoding='utf8').read()
    if 'data-id="%s"' % KEY in u: return
    for after in ('harvest', 'board', 'slides', 'prep'):   # the card and the section entry go after this one
        m = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="%s">.*?</button>\n' % after, u, re.S)
        e = re.search(r"    %s:\{title:'[^']*',hash:null\},?\n" % after, u)
        if m and e: break
    ref = m.group(0)
    card = re.sub(r'data-id="[a-z]+"', 'data-id="%s"' % KEY, ref, count=1)
    card = re.sub(r'<h3>.*?</h3>', '<h3>%s</h3>' % TITLE, card)
    card = re.sub(r'<p>.*?</p>', '<p>ملخص شامل وخريطة ذهنية لكل درس – %s – الصف %s</p>' % (lab, grd), card, flags=re.S)
    card = re.sub(r'<span class="ic">.*?</span>', '<span class="ic">%s</span>' % ICON, card, count=1, flags=re.S)
    u = u.replace(ref, ref + card, 1)
    line = e.group(0); entry = "    %s:{title:'%s',hash:null}" % (KEY, TITLE)
    new = (line if line.rstrip().endswith(',') else line.rstrip('\n') + ',\n') + entry + (',\n' if line.rstrip().endswith(',') else '\n')
    u = u.replace(line, new, 1)
    open(p, 'w', encoding='utf8').write(u)

def catalogue(d, prefix):
    v = open(R + 'p/index.html', encoding='utf8').read()
    o = '"lock": "%s", "parts": [' % prefix; assert v.count(o) == 1, prefix
    i = v.index(o); j = v.index(']]', i); seg = v[i:j]
    if '"%s"' % KEY in seg: return
    for after in ('["harvest", "حصاد الوحدات", true]', '["board", "السبورات", true]', '["slides", "عروض باور بوينت", true]', '["prep", "ملف التحضير", false]'):
        if after in seg: seg = seg.replace(after, after + ', ["%s", "%s", true]' % (KEY, TITLE), 1); break
    open(R + 'p/index.html', 'w', encoding='utf8').write(v[:i] + seg + v[j:])

def main():
    g, s, man = int(sys.argv[1]), sys.argv[2], json.load(open(sys.argv[3], encoding='utf8'))
    d = '%d/%s/' % (g, s); lab, grd = SUBJ[s], GRADE[g]
    prefix = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', open(R + 'p/index.html', encoding='utf8').read()).group(1))[d]['lock']
    out = F + d + KEY + '/'
    for e in man['lessons']:
        compress(e['s'], out + fname(e['code']) + '-s.pdf'); compress(e['m'], out + fname(e['code']) + '-m.pdf')
    if man.get('all'): compress(man['all'], out + 'all.pdf')
    os.makedirs(R + d + KEY, exist_ok=True)
    open(R + d + KEY + '/index.html', 'w', encoding='utf8').write(page(g, s, lab, grd, prefix, man['lessons'], bool(man.get('all'))))
    portal(d, lab, grd); catalogue(d, prefix)
    __import__('mark_new').mark(d + KEY)
    size = sum(os.path.getsize(out + f) for f in os.listdir(out)) / 1e6
    print('done', d + KEY, len(man['lessons']), 'lessons, %.1f MB' % size)

if __name__ == '__main__': main()
