#!/usr/bin/env python3
"""/add-offline: «العمل بدون إنترنت» for the decks (owner, 2026-11-15). Adds <script src="/assets/offline.js" defer> to every deck page
(<g>/<subject>/slides/ and <g>/<subject>/interactive/) and to /p/, right after the page's own pkgmode.js / phone.js tag. The script registers
/sw-offline.js, which keeps the deck, /p/, the portals and the /assets/ files they use in the browser's cache; a deck opened once with internet then
opens without it. Safe to run again (it skips pages that have it). Run it after adding a deck.
Usage: python3 tools/add_offline.py [--check]   (--check only lists the pages that miss it and exits 1 when there are any)"""
import glob, os, re, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
TAG = '<script src="/assets/offline.js" defer></script>'

def main():
    check = '--check' in sys.argv; todo = 0; changed = 0
    pages = sorted(glob.glob(R + '[0-9]*/*/slides/index.html') + glob.glob(R + '[0-9]*/*/interactive/index.html')) + [R + 'p/index.html']
    for p in pages:
        h = open(p, encoding='utf8').read()
        if 'assets/offline.js' in h: continue
        todo += 1
        if check: print('ينقصه:', p[len(R):]); continue
        if p.endswith('/p/index.html'): pat = r'<script src="/assets/phone\.js" defer></script>'
        else: pat = r'<script src="/assets/pkgmode\.js"[^>]*>(?:</script>)?'
        ms = re.findall(pat, h)
        if len(ms) != 1: print('تخطّي (لا موضع واحد):', p[len(R):]); continue
        close = '' if ms[0].endswith('</script>') else '</script>'
        open(p, 'w', encoding='utf8').write(h.replace(ms[0], ms[0] + close + '\n' + TAG, 1)); changed += 1
    print('%d صفحة تحتاج، عُدّلت %d' % (todo, changed))
    return 1 if (check and todo) else 0

if __name__ == '__main__': sys.exit(main())
