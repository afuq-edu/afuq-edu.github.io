#!/usr/bin/env python3
"""No tables in any prep (owner, 2026-10-25): procedures, questions (التقويم التكويني / الختامي) and outcome levels are numbered
paragraphs. Procedures: the «إجراءات سير الدرس» field of a prep page
shows each step as one numbered paragraph — «1. 5 دقائق — التهيئة: <the teacher's part>» with «• الطالب: …» under it —
separated by light dashed lines, and its copy text is the same steps one per line with a blank line between them, so the
paste into Noor (assets/copyfix.js) keeps them as separate, ordered points.
The tables (الزمن | الخطوة | دور المعلم | دور الطالب, or الزمن | دور المعلم | دور الطالب with a «الاستراتيجية: …» line) are
read row by row; both the html and its copy text are rewritten:
  {h, t} fields (grade 10 sciences; their lesson «comb» field is rebuilt), [html, text] pairs (grade 11 sciences),
  parallel html / plain (grade 8 math) and h / t (grade 12 sciences) lists.
Questions (المستوى | السؤال | الإجابة النموذجية) → «1. مستوى المعرفة: <السؤال>» + «• الإجابة النموذجية: …»; outcome levels
(المخرج | المستوى, المخرج | نصه | المستوى) → «1. فهم: <المخرج>»; any other table → «1. <cell> — <cell> …».
tools/twoshift.js draws the two-shift copy the same way (renderSteps). Idempotent.
Usage: python3 tools/proc_list.py [grade/subject ...]   (default: every prep page that still has such a table)"""
import re, os, sys, json, glob, html as H
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B

TABLE = re.compile(r'<table\b[^>]*>.*?</table>', re.S)
def is_proc(s): return isinstance(s, str) and s.lstrip().startswith('<') and bool(TABLE.search(s)) and ('</td>' in s or '</th>' in s)   # html fields only (IT lessons quote «<table>» in text)
def cells(tr): return re.findall(r'<t([hd])\b[^>]*>(.*?)</t[hd]>', tr, re.S)
def plain(x):
    x = re.sub(r'<span class=["\']m["\']>(.*?)</span>', '⁦\\1⁩', x, flags=re.S)
    x = re.sub(r'<br\s*/?>', ' ', x); x = re.sub(r'<[^>]+>', '', x)
    return re.sub(r'\s+', ' ', H.unescape(x)).strip()
def minutes(n):
    return '%d %s' % (n, 'دقيقة' if n == 1 or n > 10 else 'دقيقتان' if n == 2 else 'دقائق')

def steps_of(tbl):
    rows = re.findall(r'<tr\b[^>]*>(.*?)</tr>', tbl, re.S)
    head = [plain(c) for k, c in cells(rows[0])]
    col = lambda *names: next((i for i, h in enumerate(head) if any(n in h for n in names)), None)
    it, ist, ite, isu = col('الزمن'), col('الخطوة', 'المرحلة'), col('دور المعلم'), col('دور الطالب')
    out = []
    for r in rows[1:]:
        c = [x for k, x in cells(r)]
        if len(c) != len(head): continue
        tm = plain(c[it]); m = re.findall(r'([0-9٠-٩]+)\s*(?:دقائق|دقيقة|دقيقتان|د\b|د$)', tm) or re.findall(r'[0-9٠-٩]+', tm)
        d = int(str(m[-1]).translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))) if m else 0
        te = c[ite].strip(); name = plain(c[ist]) if ist is not None else ''
        sm = re.match(r'\s*<span class=["\']stg["\']>\s*(?:الاستراتيجية\s*[:：]\s*)?(.*?)</span>\s*(?:<br\s*/?>)?', te, re.S)
        if sm:
            if not name: name = plain(sm.group(1))
            te = te[sm.end():]
        out.append({'d': d, 'name': name, 'teacher': te.strip(), 'student': c[isu].strip() if isu is not None else ''})
    return out

ROW = 'margin:0;padding:10px 2px;border-bottom:1px dashed #d8d0bf;line-height:1.9'
def render_html(st):
    ps = []
    for k, s in enumerate(st, 1):
        lab = '%d. %s' % (k, minutes(s['d'])) + (' — ' + H.escape(s['name']) if s['name'] else '') + ':'
        ps.append('<p class="pstep" style="%s"><b>%s</b> %s%s</p>' % (ROW, lab, s['teacher'],
                  '<br><span style="opacity:.85">• الطالب: %s</span>' % s['student'] if s['student'] else ''))
    return '<div class="plist">' + ''.join(ps) + '</div>'
def render_text(st):
    out = []
    for k, s in enumerate(st, 1):
        t = '%d. %s' % (k, minutes(s['d'])) + (' — ' + s['name'] if s['name'] else '') + ': ' + plain(s['teacher'])
        if s['student']: t += '\n• الطالب: ' + plain(s['student'])
        out.append(t)
    return '\n\n'.join(out)
def rows_of(tbl):
    rows = re.findall(r'<tr\b[^>]*>(.*?)</tr>', tbl, re.S)
    head = [plain(c) for k, c in cells(rows[0])] if rows and all(k == 'h' for k, c in cells(rows[0])) else []
    body = [[x.strip() for k, x in cells(r)] for r in (rows[1:] if head else rows)]
    return head, [b for b in body if b]
def items_of(tbl):
    """[(label, main html, sub-line html or '')] for a non-procedure table"""
    head, body = rows_of(tbl)
    col = lambda *names: next((i for i, h in enumerate(head) if any(n == h or n in h for n in names)), None)
    iq, ilv, ians, iout, itext = col('السؤال'), col('المستوى'), col('الإجابة'), col('المخرج'), col('نصه')
    out = []
    for b in body:
        if len(b) != len(head) and head: continue
        if iq is not None:
            out.append((plain(b[ilv]) if ilv is not None else '', b[iq], 'الإجابة النموذجية: ' + b[ians] if ians is not None else ''))
        elif ilv is not None and (iout is not None or itext is not None):
            txt = b[itext] if itext is not None else b[iout]
            lab = plain(b[ilv]) + (' (مخرج آخر)' if iout is not None and itext is not None and 'آخر' in plain(b[iout]) else '')
            out.append((lab, txt, ''))
        else:
            out.append(('', ' — '.join(x for x in b if plain(x)), ''))
    return out
def items_html(it):
    return '<div class="plist">' + ''.join('<p class="pstep" style="%s"><b>%d.%s</b> %s%s</p>' % (
        ROW, k, (' ' + H.escape(lab) + ':') if lab else '', main, '<br><span style="opacity:.85">• %s</span>' % sub if sub else '')
        for k, (lab, main, sub) in enumerate(it, 1)) + '</div>'
def items_text(it, gap):
    return ('\n\n' if gap else '\n').join('%d.%s %s%s' % (k, (' ' + lab + ':') if lab else '', plain(main), '\n• ' + plain(sub) if sub else '')
                                     for k, (lab, main, sub) in enumerate(it, 1))
def to_text(h):
    h = re.sub(r'<br\s*/?>|</(?:p|div|li|h\d)>', '\n', h)
    return '\n'.join(l for l in (plain(x) for x in h.split('\n')) if l)
def convert(h):
    """(new html, copy text) for an html string holding tables; html around them is kept"""
    out_h, out_t, pos = [], [], 0
    for m in TABLE.finditer(h):
        pre = h[pos:m.start()]; tbl = m.group(0); pos = m.end()
        if 'دور المعلم' in tbl and 'الزمن' in tbl:
            pre = re.sub(r'<div class="tot">.*?</div>', '', pre); st = steps_of(tbl); nh, nt = render_html(st), render_text(st)
        else:
            it = items_of(tbl); nh, nt = items_html(it), items_text(it, any(sub for _, _, sub in it))
        out_h += [pre, nh]; t0 = to_text(pre); out_t += ([t0] if t0 else []) + [nt]
    rest = h[pos:]; out_h.append(rest); t1 = to_text(rest)
    if t1: out_t.append(t1)
    return ''.join(out_h), '\n'.join(out_t)

def fix(o):
    n = 0
    def walk(x):
        nonlocal n
        if isinstance(x, dict):
            if is_proc(x.get('h')) and isinstance(x.get('t'), str):
                x['h'], x['t'] = convert(x['h']); n += 1
            for a, b in (('html', 'plain'), ('h', 't')):
                if isinstance(x.get(a), list) and isinstance(x.get(b), list) and len(x[a]) == len(x[b]):
                    for i, v in enumerate(x[a]):
                        if is_proc(v): x[a][i], x[b][i] = convert(v); n += 1
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                if isinstance(v, list) and len(v) == 2 and is_proc(v[0]) and isinstance(v[1], str):
                    v[0], v[1] = convert(v[0]); n += 1
                walk(v)
    walk(o)
    # grade 10: the lesson's merged («مدمج») field is the periods one after another
    for L in (o.get('lessons') or []) if isinstance(o, dict) else []:
        cb = L.get('comb'); ps = L.get('periods') or []
        if not (cb and ps and all(isinstance(p.get('fields'), list) for p in ps)): continue
        for i, f in enumerate(cb.get('fields') or []):
            if isinstance(f, dict) and (is_proc(f.get('h')) or 'class="plist"' in f.get('h', '')) and all('class="plist"' in p['fields'][i].get('h', '') for p in ps):
                f['h'] = ''.join('<div class="psub">الحصة %d: %s</div>%s' % (k + 1, H.escape(p.get('focus', '')), p['fields'][i]['h']) for k, p in enumerate(ps))
                f['t'] = '\n\n'.join('الحصة %d: %s\n%s' % (k + 1, p.get('focus', ''), p['fields'][i]['t']) for k, p in enumerate(ps)); n += 1
    return n

def js_like(o, orig):
    compact = '", "' not in orig[:2000] and '":"' in orig[:2000]
    s = json.dumps(o, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': '))
    return s.replace('</', '<\\/')

def main():
    only = [a.strip('/') for a in sys.argv[1:]]
    pages = sorted(glob.glob(R + '[0-9]*/*/prep*/index.html') + glob.glob(R + '[0-9]*/*/prep/u*/index.html'))
    tot = 0
    for p in pages:
        rel = p[len(R):]
        if only and '/'.join(rel.split('/')[:2]) not in only: continue
        h = open(p, encoding='utf8').read()
        if '<table' not in h: continue
        lits = B.literals(h); t = h; k = 0
        for name, i, e, o in sorted(lits, key=lambda x: -x[1]):
            n = fix(o)
            if n: t = t[:i] + js_like(o, h[i:e]) + t[e:]; k += n
        if t != h: open(p, 'w', encoding='utf8').write(t)
        print('%-28s %d procedure fields' % (rel[:-11], k)); tot += k
    print('done', tot)

if __name__ == '__main__': main()
