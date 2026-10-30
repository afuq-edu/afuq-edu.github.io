#!/usr/bin/env python3
"""/graphify: a one-page visual map of the Afuq platform (owner, 2026-10-30): key numbers, the room each repo and each top-level
folder takes under the 1 GB Pages limit, the tree grade → subject → section (from the catalogue CAT in p/index.html) plus the
other folders, every tool with its first docstring line, the skills, the file types, the largest files, and what looks missing.
Usage: python3 tools/graphify.py [OUT.html]      (default: graphify.html in the current folder; self-contained, RTL, light/dark)"""
import os, re, sys, json, glob, html as H, datetime, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools'); sys.dont_write_bytecode = True   # importing space.py must not leave tools/__pycache__
GRADES = ['الأول', 'الثاني', 'الثالث', 'الرابع', 'الخامس', 'السادس', 'السابع', 'الثامن', 'التاسع', 'العاشر', 'الحادي عشر', 'الثاني عشر']
LIMIT = 1024 * 2**20           # GitHub Pages: a published site may be at most 1 GB
BIG_FILE = 25 * 2**20           # GitHub warns at 50 MB and refuses 100 MB; flag files well before that
SCRIPT_EXT = ('.py', '.js', '.sh', '.mjs')
FOLDER_NAMES = {'apps': 'تطبيقات المواد', 'assets': 'ملفات مشتركة (سكربتات، خطوط، صور)', 'tools': 'أدوات البناء والصيانة',
                'p': 'صفحة الروابط المخصصة والباقات', 'programs': 'برامج المالك', 'gifts': 'الهدايا', 'en': 'الواجهة الإنجليزية',
                'notebook': 'الدفتر', 'lessons': 'دروس', 'ofuq': 'أفق', '.claude': 'مهارات Claude', '.github': 'نشر GitHub Pages'}


def other_repo(name):
    """The files repos live next to this one in a session (or where AFUQ_FILES / AFUQ_MORE point)."""
    env = {'afuq': 'AFUQ_FILES', 'more': 'AFUQ_MORE'}[name]
    for p in (os.environ.get(env), os.path.join(os.path.dirname(R.rstrip('/')), name), '/home/user/' + name):
        if p and os.path.isdir(os.path.join(p, '.git')): return p.rstrip('/') + '/'


def tracked(root):
    """The files Pages publishes: those git tracks (all files, without .git, when git is not available)."""
    try:
        r = subprocess.run(['git', '-C', root, 'ls-files', '-z'], capture_output=True, check=True)
        return [f for f in r.stdout.decode('utf8').split('\0') if f and os.path.isfile(root + f) and not os.path.islink(root + f)]
    except Exception:
        out = []
        for d, sub, fs in os.walk(root):
            if '.git' in sub: sub.remove('.git')
            out += [os.path.relpath(os.path.join(d, f), root) for f in fs if not os.path.islink(os.path.join(d, f))]
        return out


def walk(root):
    """Apparent size and file count of every folder (recursively), the size of every file, and per-extension totals."""
    size, files, all_files, ext = {}, {}, [], {}
    for rel in tracked(root):
        s = os.path.getsize(root + rel)
        all_files.append((s, rel))
        e = os.path.splitext(rel)[1].lower() if '.' in os.path.basename(rel).lstrip('.') else '(بلا امتداد)'
        c = ext.setdefault(e, [0, 0]); c[0] += 1; c[1] += s
        parts = rel.split('/')[:-1]
        for i in range(len(parts) + 1):
            k = '/'.join(parts[:i]) + ('/' if i else '')
            size[k] = size.get(k, 0) + s; files[k] = files.get(k, 0) + 1
    return size, files, len(size) - 1, all_files, ext


def first_doc(p):
    t = open(p, encoding='utf8', errors='ignore').read(6000)
    t = re.sub(r'^#!.*\n', '', t)
    m = (re.match(r'\s*(?:[rRuU]?)("""|\'\'\')(.*?)(?:\1|$)', t, re.S) or re.match(r'\s*()/\*\*?(.*?)\*/', t, re.S)
         or re.match(r'\s*()((?:(?://|#)[^\n]*\n?)+)', t))
    if not m: return ''
    s = re.sub(r'^\s*(?://|#|\*)\s?', '', m.group(2).strip(), flags=re.M).strip()
    s = ' '.join(s.split('\n\n')[0].split())            # the first paragraph, its wrapped lines joined
    s = re.split(r'(?<=[^\d\s][.!?؟])\s', s)[0]                # … up to the end of its first sentence
    return s if len(s) <= 240 else s[:239] + '…'


def mb(b): return ('%.1f MB' % (b / 2**20)) if b < 100 * 2**20 else ('%d MB' % round(b / 2**20))


def human(b):
    """A size for the page, isolated left-to-right so «4.9 MB» does not flip to «MB 4.9»."""
    s = '%.2f GB' % (b / 2**30) if b >= 2**30 else mb(b) if b >= 2**20 else '%d KB' % max(1, round(b / 1024))
    return '<bdi dir="ltr">%s</bdi>' % s


def bar(b, label, note='', limit=LIMIT):
    pct = 100 * b / limit
    tone = 'ok' if pct < 70 else ('warn' if pct <= 90 else 'bad')
    return ('<div class="row"><div class="rh"><b>%s</b><span>%s · <bdi>%s%%</bdi></span></div><div class="bar"><i class="%s" style="width:%.1f%%"></i>'
            '</div>%s</div>') % (label, human(b), ('%.0f' % pct) if pct >= 1 else '%.1f' % pct, tone, min(100, pct),
                                 ('<small>%s</small>' % note) if note else '')


def path(p): return '<code dir="ltr">%s</code>' % H.escape(p)


TAMYIZ = {'ملف': 'ملفًا', 'مجلد': 'مجلدًا', 'قسم': 'قسمًا', 'مجلد فرعي': 'مجلدًا فرعيًا'}


def count(n, one, many):
    """Arabic counted noun: plural for 3–10, accusative singular for 11–99, singular otherwise."""
    m = n % 100
    return '%d %s' % (n, many if 3 <= m <= 10 else TAMYIZ.get(one, one) if m >= 11 else one)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'graphify.html'
    size, files, ndirs, all_files, ext = walk(R)
    total = size.get('', 0)

    v = open(R + 'p/index.html', encoding='utf8').read()
    cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', v).group(1))
    by = {}
    for k, c in cat.items(): by.setdefault(int(k.split('/')[0]), []).append((k, c))
    tools = sorted(f for f in glob.glob(R + 'tools/**/*', recursive=True) if f.endswith(SCRIPT_EXT))
    skills = sorted(glob.glob(R + '.claude/skills/*/SKILL.md'))
    pk = json.load(open(R + 'p/packages.json', encoding='utf8')) if os.path.exists(R + 'p/packages.json') else {}
    apps = glob.glob(R + 'apps/*/*/')
    more = other_repo('more')
    nparts = sum(len(c['parts']) for c in cat.values())
    stats = [('الملفات', '{:,}'.format(len(all_files))), ('المجلدات', '{:,}'.format(ndirs)), ('الحجم الكلي', human(total)),
             ('الصفوف', len(by)), ('المواد', len(cat)), ('الأقسام في المواد', nparts), ('تطبيقات المواد', len(apps)),
             ('روابط الباقات', len(pk)), ('الأدوات', len(tools)), ('مهارات Claude', len(skills))]
    if more: stats.insert(7, ('قصص المنهج', len(glob.glob(more + 'stories/*/*.pdf'))))

    # ---- room: repos, then each top-level folder ------------------------------------------------------------------
    notes = []
    try:
        from space import artifact
        art = artifact('afuq-edu.github.io')
    except Exception: art = None
    repos = bar(total, 'afuq-edu.github.io <small>(الملفات)</small>', 'الموقع: البوابات والأقسام والتحاضير والتطبيقات')
    if art:
        repos += bar(art[0] * 1e6, 'آخر نشر على Pages', 'حجم حزمة النشر المضغوطة (%s)' % H.escape(art[1]))
    if total > 0.9 * LIMIT:
        notes.append('ملفات الموقع %s، أي %d%% من حد GitHub Pages ‏1 GB%s.' % (
            human(total), round(100 * total / LIMIT), (' (حزمة النشر المضغوطة %d MB)' % art[0]) if art else ''))
    for name, desc in (('afuq', 'الملفات: نسخ الطلاب والألعاب والسكورم'), ('more', 'إضافي: قصص المنهج')):
        p = other_repo(name)
        if p:
            b = walk(p)[0].get('', 0)
            repos += bar(b, H.escape(name), desc)
            if b > 0.85 * LIMIT: notes.append('مستودع %s ‏%s، أي %d%% من 1 GB.' % (name, human(b), round(100 * b / LIMIT)))
        else:
            repos += '<div class="row muted"><div class="rh"><b>%s</b><span>غير موجود في هذه الجلسة</span></div><small>%s</small></div>' % (name, desc)

    top = sorted((k for k in size if k and k.count('/') == 1), key=lambda k: -size[k])
    folders, small = '', []
    for k in top:
        if size[k] < 2**20: small.append(k); continue
        g = k[:-1]
        lab = ('الصف ' + GRADES[int(g) - 1]) if g.isdigit() and 1 <= int(g) <= 12 else FOLDER_NAMES.get(g, '')
        folders += bar(size[k], path(k) + (' <span class="lab">%s</span>' % lab if lab else ''), count(files[k], 'ملف', 'ملفات'))
    if small:
        folders += '<p class="legend">مجلدات أصغر من 1 MB (%d): %s</p>' % (len(small), ' '.join(path(k) for k in small))

    # ---- tree: grade → subject → section (CAT), then the other folders ------------------------------------------------
    def sec_li(k, p):
        d = k + p[0] + '/'
        return '<li><span class="chip%s">%s</span> %s <em>%s · %s</em></li>' % (
            '' if p[2] or p[0] == 'prep' else ' free', H.escape(p[1]), path(d), count(files.get(d, 0), 'ملف', 'ملفات'), human(size.get(d, 0)))

    tree = ''
    for g in sorted(by):
        subs = ''
        for k, c in by[g]:
            subs += '<details class="subj" style="--c:%s"><summary><b>%s</b> %s<em>%s · %s</em></summary><ul>%s</ul></details>' % (
                H.escape(c.get('color', '#2F6FB3')), H.escape(c['title']), path(k), count(len(c['parts']), 'قسم', 'أقسام'),
                human(size.get(k, 0)), ''.join(sec_li(k, p) for p in c['parts']))
        gk = '%d/' % g
        tree += '<details class="node"><summary><b>الصف %s</b> %s<em>%s · %s · %s</em></summary>%s</details>' % (
            GRADES[g - 1], path(gk), count(len(by[g]), 'مادة', 'مواد'), count(files.get(gk, 0), 'ملف', 'ملفات'), human(size.get(gk, 0)), subs)

    def dir_node(k, depth):
        kids = sorted((x for x in size if x.startswith(k) and x != k and x[len(k):].count('/') == 1), key=lambda x: -size[x])
        loose = files[k] - sum(files[x] for x in kids)
        inner = ''
        if depth < 2:
            inner = ''.join(dir_node(x, depth + 1) for x in kids[:40])
            if len(kids) > 40: inner += '<p class="legend">… و%d مجلدًا آخر</p>' % (len(kids) - 40)
        elif kids: inner = '<p class="legend">%s</p>' % count(len(kids), 'مجلد فرعي', 'مجلدات فرعية')
        if loose: inner += '<p class="legend">%s مباشرة في المجلد</p>' % count(loose, 'ملف', 'ملفات')
        return '<details class="node"><summary>%s<em>%s · %s · %s</em></summary>%s</details>' % (
            path(k), count(len(kids), 'مجلد', 'مجلدات'), count(files[k], 'ملف', 'ملفات'), human(size[k]), inner)

    others = [k for k in top if not k[:-1].isdigit()]
    tree += '<details class="node"><summary><b>المجلدات الأخرى</b><em>%s</em></summary>%s</details>' % (
        count(len(others), 'مجلد', 'مجلدات'), ''.join(dir_node(k, 1) for k in others))
    rootf = [f for s, f in all_files if '/' not in f]
    tree += '<details class="node"><summary><b>ملفات الجذر</b><em>%s</em></summary><p>%s</p></details>' % (
        count(len(rootf), 'ملف', 'ملفات'), ' '.join(path(f) for f in sorted(rootf)))

    # ---- what looks missing or out of place -------------------------------------------------------------------------
    light = []                  # subjects lacking most of their grade's usual sections (PE, arts…): one line for all of them
    for g in sorted(by):
        have = {}
        for k, c in by[g]:
            for p in c['parts']: have.setdefault((p[0], p[1]), set()).add(k)
        usual = [kt for kt, ks in have.items() if len(ks) > len(by[g]) / 2]
        for k, c in by[g]:
            lack = [kt[1] for kt in usual if k not in have[kt]]
            if len(lack) >= 5: light.append(k)
            elif lack: notes.append('%s %s ينقصها ما في أغلب مواد صفها: %s.' % (H.escape(c['title']), path(k), '، '.join('«%s»' % H.escape(t) for t in lack)))
    if light:
        notes.append('%s فيها أقسام قليلة مقارنة بصفوفها (غالبًا عمدًا: البدنية والفنون): %s' % (count(len(light), 'مادة', 'مواد'), ' '.join(path(k) for k in light)))
    for g in sorted(by):
        for k, c in by[g]:
            keys = {p[0] for p in c['parts']}
            extra = sorted(os.path.basename(d.rstrip('/')) for d in glob.glob(R + k + '*/') if os.path.basename(d.rstrip('/')) not in keys)
            if extra: notes.append('%s: مجلدات غير ظاهرة في الفهرس %s.' % (H.escape(c['title']), ' '.join(path(e) for e in extra)))
    for d in sorted(glob.glob(R + '[0-9]*/*/')):
        k = os.path.relpath(d, R) + '/'
        if k not in cat: notes.append('المجلد %s ليس مادة في فهرس الأقسام CAT.' % path(k))
    big = sorted([x for x in all_files if x[0] >= BIG_FILE], reverse=True)
    if big: notes.append('%s أكبر من %d MB (أكبرها %s ‏%s).' % (count(len(big), 'ملف', 'ملفات'), BIG_FILE // 2**20, path(big[0][1]), human(big[0][0])))
    junk = [f for s, f in all_files if f.endswith(('.pyc', '.DS_Store', 'Thumbs.db', '~')) or '__pycache__/' in f]
    if junk: notes.append('ملفات مؤقتة لا داعي لها في المستودع: %s.' % ' '.join(path(f) for f in junk[:10]))
    nodoc = [os.path.relpath(f, R) for f in tools if not first_doc(f)]
    if nodoc: notes.append('أدوات بلا شرح في أولها: %s.' % ' '.join(path(f) for f in nodoc))
    note_html = ''.join('<li>%s</li>' % n for n in notes) or '<li>لا شيء لافت.</li>'

    # ---- tables -------------------------------------------------------------------------------------------------------
    tool_rows = ''.join('<tr><td>%s</td><td dir="auto">%s</td></tr>' % (path(os.path.relpath(f, R)), H.escape(first_doc(f)) or '<span class="muted">—</span>')
                        for f in tools)
    skill_rows = ''
    for s in skills:
        t = open(s, encoding='utf8').read()
        n = re.search(r'^name:\s*(.+)$', t, re.M); d = re.search(r'^description:\s*(.+)$', t, re.M)
        skill_rows += '<tr><td>%s</td><td dir="auto">%s</td></tr>' % (path('/' + (n.group(1).strip() if n else os.path.basename(os.path.dirname(s)))),
                                                          H.escape(d.group(1).strip() if d else ''))
    ext_rows = ''.join('<tr><td>%s</td><td>{:,}</td><td>%s</td><td class="mini"><div class="bar"><i class="ok" style="width:%.1f%%"></i></div></td></tr>'
                       .format(c[0]) % (path(e), human(c[1]), 100 * c[1] / total) for e, c in sorted(ext.items(), key=lambda x: -x[1][1]))
    big_rows = ''.join('<tr><td>%s</td><td>%s</td></tr>' % (path(f), human(s)) for s, f in sorted(all_files, reverse=True)[:15])

    cards = ''.join('<div class="st"><b>%s</b><span>%s</span></div>' % (n, H.escape(t)) for t, n in stats)
    try: head = subprocess.run(['git', '-C', R, 'log', '-1', '--format=%h · %cd', '--date=format:%Y-%m-%d %H:%M'],
                               capture_output=True, text=True).stdout.strip()
    except Exception: head = ''
    when = datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ((' — آخر تعديل <bdi dir="ltr">%s</bdi>' % H.escape(head)) if head else '')
    page = TEMPLATE
    for a, b in (('when', when), ('cards', cards), ('notes', note_html), ('repos', repos), ('folders', folders), ('tree', tree),
                 ('tools', tool_rows), ('skills', skill_rows), ('ext', ext_rows), ('big', big_rows)):
        page = page.replace('{{%s}}' % a, b)
    open(out, 'w', encoding='utf8').write(page)
    print('map written:', out, '|', re.sub('<[^>]+>', '', ' · '.join('%s %s' % (t, n) for t, n in stats)), '| notes:', len(notes))


TEMPLATE = '''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>خريطة منصة أفق</title><style>
:root{--bg:#F3F7FC;--card:#fff;--ink:#17233D;--muted:#5B6782;--line:#DCE4EF;--brand:#2F6FB3;--ok:#1F9D55;--warn:#D98A0B;--bad:#D64545;--chip:#EEF4FB;--note:#FFF6E5}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0F1626;--card:#18223A;--ink:#E8EDF7;--muted:#9AA6C2;--line:#2B3756;--brand:#6EA8FF;--chip:#1F2B47;--ok:#3CC57A;--warn:#F0A63A;--bad:#F06A6A;--note:#2A2616}}
:root[data-theme="dark"]{--bg:#0F1626;--card:#18223A;--ink:#E8EDF7;--muted:#9AA6C2;--line:#2B3756;--brand:#6EA8FF;--chip:#1F2B47;--ok:#3CC57A;--warn:#F0A63A;--bad:#F06A6A;--note:#2A2616}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,"Segoe UI",system-ui,sans-serif;line-height:1.7}
main{max-width:1000px;margin:0 auto;padding:20px 16px 60px}h1{margin:0;font-size:clamp(22px,5vw,30px)}h2{font-size:19px;margin:30px 0 10px}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}#theme{background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:99px;padding:6px 12px;font:inherit;cursor:pointer}
.sub{color:var(--muted);margin:2px 0 16px;font-size:14px}.muted{color:var(--muted)}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;unicode-bidi:isolate;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:10px}.st{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px}
.st b{display:block;font-size:24px;color:var(--brand)}.st span{color:var(--muted);font-size:13.5px}
.notes{background:var(--note);border:1px solid var(--line);border-radius:14px;padding:10px 14px 10px 14px;margin:0}.notes ul{margin:0;padding-inline-start:20px}.notes li{margin:4px 0}
.box{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:6px 14px}
.row{padding:10px 0;border-top:1px solid var(--line)}.row:first-child{border-top:0}.rh{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:baseline}
.rh span{color:var(--muted);font-size:14px}.lab{color:var(--muted);font-weight:normal;font-size:13px}.row small{color:var(--muted)}
.bar{height:10px;border-radius:99px;background:var(--chip);margin:6px 0 2px;overflow:hidden}.bar i{display:block;height:100%;border-radius:99px}
.ok{background:var(--ok)}.warn{background:var(--warn)}.bad{background:var(--bad)}
.legend{color:var(--muted);font-size:13px;margin:6px 0}
details.node,details.subj{border-top:1px dashed var(--line);padding:4px 0}details details{margin-inline-start:14px}
.box>details:first-child{border-top:0}summary{cursor:pointer;padding:3px 0;overflow-wrap:anywhere}summary em,li em{display:inline-block;white-space:nowrap;font-style:normal;color:var(--muted);font-size:12.5px;margin-inline-start:8px}
summary code{margin-inline-start:6px;color:var(--muted)}.subj summary b::before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--c);margin-inline-end:6px}
ul{margin:4px 0 8px;padding-inline-start:18px}li{margin:3px 0}
.chip{font-size:12.5px;padding:1px 10px;border-radius:99px;background:var(--chip);border:1px solid var(--line);white-space:nowrap}.chip.free{border-style:dashed}
.wrap{overflow-x:auto;border-radius:14px;border:1px solid var(--line)}table{width:100%;border-collapse:collapse;background:var(--card);font-size:14px}
td[dir=auto]{text-align:start}th{text-align:start;font-size:13px;color:var(--muted);padding:8px 10px;background:var(--chip)}td{padding:7px 10px;border-top:1px solid var(--line);vertical-align:top}
td:first-child{white-space:nowrap}td.mini{width:30%;min-width:80px}td.mini .bar{margin:8px 0}
@media (max-width:600px){td:first-child{white-space:normal}.stack tr{display:block;border-top:1px solid var(--line)}.stack tr:first-child{display:none}
.stack td{display:block;border:0;padding:3px 12px}.stack td:first-child{padding-top:10px;font-weight:bold}.stack td:last-child{padding-bottom:10px}}
</style></head><body><main>
<div class="top"><div><h1>🗺️ خريطة منصة أفق التعليمية</h1><p class="sub">أُنشئت {{when}}</p></div><button id="theme" type="button" aria-label="الوضع الفاتح أو الداكن">🌓</button></div>
<div class="stats">{{cards}}</div>
<h2>ما يحتاج انتباهًا</h2><div class="notes"><ul>{{notes}}</ul></div>
<h2>المساحة أمام حد GitHub Pages ‏(1 GB)</h2><div class="box">{{repos}}</div>
<h2>حجم كل مجلد رئيسي (من 1 GB)</h2><p class="legend">الأخضر تحت 70%، والبرتقالي حتى 90%، والأحمر فوقه.</p><div class="box">{{folders}}</div>
<h2>بنية المشروع</h2><p class="legend">الصفوف والمواد وأقسامها من فهرس الأقسام CAT في <code dir="ltr">p/index.html</code>. اضغط على أي فرع لفتحه؛ الإطار المتقطع = قسم مفتوح بلا قفل.</p><div class="box">{{tree}}</div>
<h2>الأدوات والسكربتات</h2><div class="wrap stack"><table><tr><th>الأداة</th><th>ما تفعله (السطر الأول من شرحها)</th></tr>{{tools}}</table></div>
<h2>مهارات Claude</h2><div class="wrap stack"><table><tr><th>الأمر</th><th>الوصف</th></tr>{{skills}}</table></div>
<h2>أنواع الملفات</h2><div class="wrap"><table><tr><th>النوع</th><th>العدد</th><th>الحجم</th><th>من الكل</th></tr>{{ext}}</table></div>
<h2>أكبر الملفات</h2><div class="wrap"><table><tr><th>الملف</th><th>الحجم</th></tr>{{big}}</table></div>
</main><script>
(function(){var b=document.getElementById('theme'),r=document.documentElement;
function cur(){return r.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')}
b.onclick=function(){r.dataset.theme=cur()=='dark'?'light':'dark'};})();
</script></body></html>'''

if __name__ == '__main__': main()
