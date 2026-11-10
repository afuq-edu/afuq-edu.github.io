#!/usr/bin/env python3
"""«⬇️ تنزيل الشهادة» (owner, 2026-11-10): adds <script src="/assets/certdl.js" defer> to every page that shows a certificate box
(.cert) of its own — the harvest quizzes, the older homework copies, the explorers — except pages whose certificate is already a
downloadable image (they draw it on a canvas: toDataURL). The homework pages (hwcommon.js) load it themselves.
Usage: python3 tools/add_certdl.py        (idempotent; add_harvest.py runs it after writing a page)"""
import re, os, glob, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
TAG = '<script src="/assets/certdl.js" defer></script>'
CERT = re.compile(r"class=\"cert[\" ]|class:\s*'cert'|id=\"cert\"")

def fix(p):
    h = open(p, encoding='utf8').read()
    if 'certdl.js' in h or not CERT.search(h) or 'شهادة' not in h: return 0
    if 'toDataURL' in h and 'download' in h: return 0          # already a downloadable image
    if '</body>' not in h: return 0
    open(p, 'w', encoding='utf8').write(h.replace('</body>', TAG + '\n</body>', 1)); return 1

def main(paths=None):
    n = 0
    for p in paths or sorted(glob.glob(R + '[0-9]*/*/*/index.html') + glob.glob(R + '[0-9]*/*/*/*/index.html')):
        if 'prep' in p.split('/')[-3:-1]: continue
        try: n += fix(p)
        except Exception: pass
    print('certdl.js added to %d pages' % n); return n

if __name__ == '__main__': main()
