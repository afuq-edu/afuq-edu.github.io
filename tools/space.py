#!/usr/bin/env python3
"""/space: room left in the three repos under GitHub Pages' 1 GB (owner, 2026-10-30): each repo's working tree (without .git)
and the size of its last published Pages artifact (GitHub API); the warning (from 85 %) goes by the published size.
Usage: python3 tools/space.py"""
import os, json, subprocess, urllib.request
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
REPOS = [('afuq-edu.github.io', R), ('afuq', '/home/user/afuq/'), ('more', '/home/user/more/')]
LIMIT = 1024

def tree(p):
    if not os.path.isdir(p): return None
    r = subprocess.run(['du', '-sm', '--exclude=.git', p], capture_output=True, text=True).stdout.split()
    return int(r[0]) if r else None

def artifact(repo):
    try:
        with urllib.request.urlopen('https://api.github.com/repos/afuq-edu/%s/actions/artifacts?per_page=30' % repo, timeout=20) as f:
            a = [x for x in json.load(f).get('artifacts', []) if x.get('name') == 'github-pages']
        a.sort(key=lambda x: x['created_at'], reverse=True)
        return (round(a[0]['size_in_bytes'] / 1e6), a[0]['created_at'][:16].replace('T', ' ')) if a else None
    except Exception: return None

def main():
    warn = []
    print('%-22s %10s %16s' % ('المستودع', 'الملفات', 'آخر نشر'))
    for name, path in REPOS:
        t, a = tree(path), artifact(name)
        print('%-22s %10s %16s %s' % (name, ('%d MB' % t) if t is not None else '—', ('%d MB' % a[0]) if a else '—', ('(%s)' % a[1]) if a else ''))
        big = a[0] if a else (t or 0)            # what Pages publishes; the working tree when no artifact is listed
        if big >= 0.85 * LIMIT: warn.append('%s: %d MB من %d (%d%%)' % (name, big, LIMIT, round(100 * big / LIMIT)))
    if warn:
        print('\n⚠ قريب من حد 1 GB أو فوقه:'); [print('  - ' + w) for w in warn]
        print('  أضف الملفات الكبيرة الجديدة إلى مستودع فيه متسع (more)، أو اضغطها (tools/compress_pdf.py).')
    else: print('\n✔ كل المستودعات تحت 85%.')

if __name__ == '__main__': main()
