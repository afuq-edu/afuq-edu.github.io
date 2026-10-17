#!/usr/bin/env python3
"""Store embedded fonts once: every CSS url(data:font/...;base64,...) in the given trees is written to
/assets/f/<sha1-16>.<ext> and replaced by that URL. The same few fonts were embedded in hundreds of pages
(~200 MB of the 1 GB GitHub Pages limit). Pages in the files repo (served at /afuq/) can point at the
same /assets/f/ files because both repos share the afuq-edu.github.io origin.
Usage: python3 tools/dedupe_fonts.py [DIR ...]   (default: this repo). Rerunning is a no-op.
Run it after adding content (CLAUDE.md), before committing."""
import re, os, sys, base64, hashlib
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
OUT = R + 'assets/f/'
EXT = {'font/woff2': 'woff2', 'font/woff': 'woff', 'font/ttf': 'ttf', 'font/otf': 'otf',
       'application/font-woff2': 'woff2', 'application/font-woff': 'woff', 'application/x-font-ttf': 'ttf'}
PAT = re.compile(r"""url\(\s*(['"]?)data:(font/woff2|font/woff|font/ttf|font/otf|application/font-woff2?|application/x-font-ttf);base64,([A-Za-z0-9+/=\s]+?)\1\s*\)""")

def fix(path):
    s = open(path, encoding='utf8').read()
    if 'base64,' not in s: return 0
    def rep(m):
        data = re.sub(r'\s', '', m.group(3)); raw = base64.b64decode(data)
        name = hashlib.sha1(raw).hexdigest()[:16] + '.' + EXT[m.group(2)]
        if not os.path.exists(OUT + name): open(OUT + name, 'wb').write(raw)
        return 'url(/assets/f/%s)' % name
    t = PAT.sub(rep, s)
    if t == s: return 0
    open(path, 'w', encoding='utf8').write(t); return len(s.encode()) - len(t.encode())

def main():
    os.makedirs(OUT, exist_ok=True); roots = sys.argv[1:] or [R]; saved = files = 0
    for root in roots:
        for d, dirs, fs in os.walk(root):
            dirs[:] = [x for x in dirs if x != '.git']
            for f in fs:
                if f.endswith('.html'):
                    n = fix(os.path.join(d, f))
                    if n: saved += n; files += 1
    print('fonts deduplicated in %d pages, %.1f MB saved' % (files, saved / 1e6))

if __name__ == '__main__': main()
