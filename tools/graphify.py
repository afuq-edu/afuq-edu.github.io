#!/usr/bin/env python3
"""/graphify: a one-page visual map of the Afuq platform (owner, 2026-10-30) — the three repos and their room under the
1 GB Pages limit, every grade → subject → section (from the catalogue CAT in p/index.html), the extra content (apps,
stories, skill preps, packages), and every tool in tools/ with its first docstring line.
Usage: python3 tools/graphify.py [OUT.html]      (default: graphify.html in the current folder; self-contained, light/dark)"""
import os, re, sys, json, glob, html as H, subprocess, datetime
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
REPOS = [('afuq-edu.github.io', R, 'الموقع: البوابات والأقسام والتحاضير والتطبيقات'),
         ('afuq', os.environ.get('AFUQ_FILES', '/home/user/afuq') + '/', 'الملفات: نسخ الطلاب والألعاب والسكورم'),
         ('more', os.environ.get('AFUQ_MORE', '/home/user/more') + '/', 'إضافي: قصص المنهج')]
GRADES = ['الأول', 'الثاني', 'الثالث', 'الرابع', 'الخامس', 'السادس', 'السابع', 'الثامن', 'التاسع', 'العاشر', 'الحادي عشر', 'الثاني عشر']
LIMIT = 1024  # MB, GitHub Pages

def size_mb(p):
    if not os.path.isdir(p): return None
    try: return int(subprocess.run(['du', '-sm', '--exclude=.git', p], capture_output=True, text=True).stdout.split()[0])
    except Exception: return None

def first_doc(p):
    t = open(p, encoding='utf8', errors='ignore').read(4000)
    m = re.search(r'"""(.*?)(?:"""|$)', t, re.S) or re.search(r'/\*(.*?)\*/', t, re.S) or re.search(r'^#\s*(?!!)(.+)$', t, re.M)
    s = (m.group(1) if m else '').strip().split('\n')[0].strip()
    return s[:220]

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'graphify.html'
    v = open(R + 'p/index.html', encoding='utf8').read()
    cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', v).group(1))
    by = {}
    for k, c in cat.items():
        g = int(k.split('/')[0]); by.setdefault(g, []).append((k, c))
    secs = {}
    for k, c in cat.items():
        for p in c['parts']: secs[p[1]] = secs.get(p[1], 0) + 1
    tools = sorted(f for f in glob.glob(R + 'tools/*') if f.endswith(('.py', '.js')))
    pk = json.load(open(R + 'p/packages.json', encoding='utf8')) if os.path.exists(R + 'p/packages.json') else {}
    stats = [('الصفوف', len(by)), ('المواد', len(cat)), ('الأقسام في المواد', sum(len(c['parts']) for c in cat.values())),
             ('تطبيقات المواد', len(glob.glob(R + 'apps/*/*/'))), ('قصص المنهج', len(glob.glob(REPOS[2][1] + 'stories/*/*.pdf'))),
             ('روابط الباقات', len(pk)), ('الأدوات', len(tools))]
    rep = ''
    for name, path, desc in REPOS:
        mb = size_mb(path)
        pct = min(100, round(100 * mb / LIMIT)) if mb is not None else 0
        tone = 'ok' if pct < 70 else ('warn' if pct < 90 else 'bad')
        rep += ('<div class="repo"><div class="rh"><b>%s</b><span>%s</span></div><div class="bar"><i class="%s" style="width:%d%%"></i></div>'
                '<small>%s</small></div>') % (H.escape(name), ('%d MB من 1024' % mb) if mb is not None else 'غير موجود في هذه الجلسة',
                                               tone, pct, H.escape(desc))
    grades = ''
    for g in sorted(by):
        subs = ''
        for k, c in by[g]:
            chips = ''.join('<span class="chip%s">%s</span>' % ('' if p[2] or p[0] == 'prep' else ' free', H.escape(p[1])) for p in c['parts'])
            subs += '<details class="subj" style="--c:%s"><summary><b>%s</b><em>%d قسمًا</em></summary><div class="chips">%s</div><code>/%s</code></details>' % (
                H.escape(c.get('color', '#2F6FB3')), H.escape(c['title']), len(c['parts']), chips, H.escape(k))
        grades += '<section class="grade"><h3>الصف %s <em>%d مادة</em></h3>%s</section>' % (GRADES[g - 1], len(by[g]), subs)
    sec_rows = ''.join('<tr><td>%s</td><td>%d</td></tr>' % (H.escape(s), n) for s, n in sorted(secs.items(), key=lambda x: -x[1]))
    tool_rows = ''.join('<tr><td><code>%s</code></td><td>%s</td></tr>' % (H.escape(os.path.basename(f)), H.escape(first_doc(f))) for f in tools)
    cards = ''.join('<div class="st"><b>%s</b><span>%s</span></div>' % (n, H.escape(t)) for t, n in stats)
    when = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    page = TEMPLATE.replace('{{when}}', when).replace('{{cards}}', cards).replace('{{repos}}', rep).replace('{{grades}}', grades) \
        .replace('{{secs}}', sec_rows).replace('{{tools}}', tool_rows)
    open(out, 'w', encoding='utf8').write(page)
    print('map written:', out, '|', ' · '.join('%s %s' % (t, n) for t, n in stats))

TEMPLATE = '''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>خريطة منصة أفق</title><style>
:root{--bg:#F3F7FC;--card:#fff;--ink:#17233D;--muted:#5B6782;--line:#DCE4EF;--brand:#2F6FB3;--ok:#1F9D55;--warn:#D98A0B;--bad:#D64545;--chip:#EEF4FB}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0F1626;--card:#18223A;--ink:#E8EDF7;--muted:#9AA6C2;--line:#2B3756;--brand:#6EA8FF;--chip:#1F2B47}}
:root[data-theme="dark"]{--bg:#0F1626;--card:#18223A;--ink:#E8EDF7;--muted:#9AA6C2;--line:#2B3756;--brand:#6EA8FF;--chip:#1F2B47}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,"Segoe UI",system-ui,sans-serif;line-height:1.7}
main{max-width:1000px;margin:0 auto;padding:20px 16px 60px}h1{margin:0;font-size:clamp(22px,5vw,30px)}h2{font-size:19px;margin:28px 0 10px}
.sub{color:var(--muted);margin:2px 0 16px;font-size:14px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}.st{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px}
.st b{display:block;font-size:26px;color:var(--brand)}.st span{color:var(--muted);font-size:13.5px}
.repo{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:0 0 10px}.rh{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
.rh span{color:var(--muted);font-size:14px}.bar{height:10px;border-radius:99px;background:var(--chip);margin:8px 0 4px;overflow:hidden}.bar i{display:block;height:100%}
.bar .ok{background:var(--ok)}.bar .warn{background:var(--warn)}.bar .bad{background:var(--bad)}.repo small{color:var(--muted)}
.grade{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:10px 14px;margin:0 0 12px}.grade h3{margin:2px 0 6px;font-size:17px}
.grade h3 em,.subj em{font-style:normal;color:var(--muted);font-size:13px;margin-inline-start:6px}
.subj{border-top:1px dashed var(--line);padding:6px 0}.subj summary{cursor:pointer;display:flex;align-items:center;gap:8px}
.subj summary::before{content:"";width:10px;height:10px;border-radius:50%;background:var(--c);flex:none}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 4px}.chip{font-size:12.5px;padding:2px 10px;border-radius:99px;background:var(--chip);border:1px solid var(--line)}
.chip.free{border-style:dashed}.subj code{font-size:12px;color:var(--muted)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;font-size:14px}
td{padding:8px 10px;border-top:1px solid var(--line);vertical-align:top}tr:first-child td{border-top:0}td:first-child{white-space:nowrap}
.wrap{overflow-x:auto}.legend{color:var(--muted);font-size:13px;margin:0 0 8px}
</style></head><body><main>
<h1>🗺️ خريطة منصة أفق التعليمية</h1><p class="sub">أُنشئت {{when}} — من فهرس الأقسام (CAT) والمستودعات وأدوات tools/.</p>
<div class="stats">{{cards}}</div>
<h2>المستودعات (حد GitHub Pages ‏1 GB لكل مستودع)</h2>{{repos}}
<h2>الصفوف والمواد وأقسامها</h2><p class="legend">اضغط على المادة لترى أقسامها؛ الإطار المتقطع = قسم مفتوح بلا قفل الباقة الذهبية.</p>{{grades}}
<h2>الأقسام وعدد المواد التي فيها</h2><div class="wrap"><table>{{secs}}</table></div>
<h2>الأدوات (tools/)</h2><div class="wrap"><table>{{tools}}</table></div>
</main></body></html>'''

if __name__ == '__main__': main()
