#!/usr/bin/env python3
"""A new subject's prep (ملف التحضير) from lesson JSON files, on the page engine of an existing prep of the same kind
(owner, 2026-10-28: grade 12 environmental science, built from its books like grade 11's).
Usage: python3 tools/add_prep_units.py GRADE SUBJECT LESSONS_DIR TEMPLATE_GRADE LOCK_PREFIX COLOR
  LESSONS_DIR/L01.json … = {"id","title","unit","periods":[{n, axis, week, date, note, sb, tg, f:[10 fields]}], "closing":{n,a,s}}
  (the prep page format of TEMPLATE_GRADE/SUBJECT/prep/uN, one page per unit, in lesson order).
Writes <g>/<s>/prep/index.html (unit chooser) and prep/u<N>/index.html, the subject portal <g>/<s>/index.html (from the template
subject's), the catalogue entry in p/index.html (CAT), the home page entry (index.html), the closing activities in
tools/identity_items.json, and the «جديد» badge. Then run the prep pipeline (tools/build_quiz.py <g>/<s>, which runs proc_style,
add_identity, stage_times, outcome_times, form_heading, add_shift, add_twoshift) and tools/build_scorm.py <g>/<s>."""
import re, os, sys, json, glob, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
GRADE = {9: 'التاسع', 10: 'العاشر', 11: 'الحادي عشر', 12: 'الثاني عشر'}
UNITS_AR = ['الأولى', 'الثانية', 'الثالثة', 'الرابعة', 'الخامسة', 'السادسة']
DEC = json.JSONDecoder()
def read(p): return open(R + p, encoding='utf8').read()
def write(p, t):
    os.makedirs(os.path.dirname(R + p), exist_ok=True); open(R + p, 'w', encoding='utf8').write(t)

def main():
    g, s, src, tg, lock, color = int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6]
    d, td = '%d/%s/' % (g, s), '%d/%s/' % (tg, s); G, TG = GRADE[g], GRADE[tg]
    les = [json.load(open(f, encoding='utf8')) for f in sorted(glob.glob(os.path.join(src, 'L*.json')))]
    units = []
    for L in les:
        if not units or units[-1][0] != L['unit']: units.append((L['unit'], []))
        units[-1][1].append(L)
    tpl = subprocess.run(['git', 'show', 'HEAD:%sprep/u1/index.html' % td], cwd=R, capture_output=True, text=True).stdout
    m = re.search(r'<script type="application/json" id="data">', tpl); old, e = DEC.raw_decode(tpl, m.end())
    old_unit = old[0]['unit']
    ident = json.load(open(R + 'tools/identity_items.json', encoding='utf8'))
    for k, (uname, ls) in enumerate(units, 1):
        data = [{x: L[x] for x in ('id', 'title', 'unit', 'periods')} for L in ls]
        h = tpl[:m.end()] + json.dumps(data, ensure_ascii=False).replace('</', '<\\/') + tpl[e:]
        h = h.replace(old_unit, uname).replace('الصف ' + TG, 'الصف ' + G).replace(td, d)
        write(d + 'prep/u%d/index.html' % k, h)
        ident[d + 'prep/u%d' % k] = [dict(title=L['title'], **L['closing']) for L in ls]
    json.dump(ident, open(R + 'tools/identity_items.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    # unit chooser
    h = subprocess.run(['git', 'show', 'HEAD:%sprep/index.html' % td], cwd=R, capture_output=True, text=True).stdout
    tu = []
    for k in range(1, 9):
        t = subprocess.run(['git', 'show', 'HEAD:%sprep/u%d/index.html' % (td, k)], cwd=R, capture_output=True, text=True).stdout
        if not t: break
        mm = re.search(r'<script type="application/json" id="data">', t); tu.append(DEC.raw_decode(t, mm.end())[0][0]['unit'])
    for a, (b, _) in zip(tu, units): h = h.replace(re.sub(r'^الوحدة [^:]*:\s*', '', a), re.sub(r'^الوحدة [^:]*:\s*', '', b))
    write(d + 'prep/index.html', h.replace('الصف ' + TG, 'الصف ' + G).replace(td, d))
    # portal page
    oldlock = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', read('p/index.html')).group(1))[td]['lock']
    h = subprocess.run(['git', 'show', 'HEAD:%sindex.html' % td], cwd=R, capture_output=True, text=True).stdout
    write(d + 'index.html', h.replace('الصف ' + TG, 'الصف ' + G).replace(oldlock, lock).replace(td, d))
    # catalogue
    v = read('p/index.html'); cm = re.search(r'var CAT=(\{.*\});\s*\n', v); cat = json.loads(cm.group(1))
    if d not in cat:
        last = [k2 for k2 in cat if k2.startswith('%d/' % g)][-1]
        new = {}
        for k2, val in cat.items():
            new[k2] = val
            if k2 == last: new[d] = {'title': re.sub(TG + r'$', G, cat[td]['title']), 'color': color, 'lock': lock, 'parts': [['prep', 'ملف التحضير', False]]}
        write('p/index.html', v[:cm.start(1)] + json.dumps(new, ensure_ascii=False) + v[cm.end(1):])
    # home page: the subject in the grade's list, like the template grade's entry
    hm = read('index.html')
    ent = re.search(r"\['%s/','[^']*',[A-Z]+,'[^']*'\]" % s, hm[hm.index('    %d:[[' % tg):]).group(0)
    a0 = hm.index('    %d:[[' % g); a1 = hm.index('\n', a0); seg = hm[a0:a1]
    if "['%s/'" % s not in seg:
        k = seg.rindex(']]'); write('index.html', hm[:a0] + seg[:k] + '],' + ent[:-1] + seg[k:] + hm[a1:])
    __import__('mark_new').mark(d + 'prep')
    print('done', d, len(les), 'lessons,', sum(len(L['periods']) for L in les), 'periods,', len(units), 'units')

if __name__ == '__main__': main()
