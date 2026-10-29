#!/usr/bin/env python3
"""«شاشة الهاتف» (owner, 2026-10-29): the home page, the gold link page and every subject portal look like a phone's home
screen (glassy daytime app icons): /assets/phone.css after the page's own style, /assets/phone.js before </body>.
Usage: python3 tools/phone_ui.py      (idempotent; new portals copied from an existing one already carry it)"""
import os, glob, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
CSS, JS = '<link rel="stylesheet" href="/assets/phone.css">', '<script src="/assets/phone.js" defer></script>'
n = 0
for p in ['index.html', 'p/index.html'] + sorted(glob.glob(R + '[0-9]*/*/index.html')):
    p = p if p.startswith('/') else R + p
    h = open(p, encoding='utf8').read(); h0 = h
    if CSS not in h: h = h.replace('</head>', CSS + '\n</head>', 1)
    if JS not in h: h = h.replace('</body>', JS + '\n</body>', 1)
    if h != h0: open(p, 'w', encoding='utf8').write(h); n += 1
print('phone screen on', n, 'pages')
