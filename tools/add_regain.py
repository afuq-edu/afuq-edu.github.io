#!/usr/bin/env python3
"""/add-regain: «استعادة الوصول» in the lock dialogs of the portal pages (owner, 2026-11-16). Adds <script src="/assets/regain.js" defer> before </body> of every
<g>/<subject>/index.html (the pages whose #dlg says «هذا القسم مخصص للباقة الذهبية»). Safe to run again. Run it after adding a portal page.
Usage: python3 tools/add_regain.py [--check]"""
import glob, os, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
TAG = '<script src="/assets/regain.js" defer></script>\n'

def main():
    check = '--check' in sys.argv; todo = changed = 0
    for p in sorted(glob.glob(R + '[0-9]*/*/index.html')):
        h = open(p, encoding='utf8').read()
        if 'هذا القسم مخصص للباقة الذهبية' not in h or 'id="dlg"' not in h or 'assets/regain.js' in h: continue
        todo += 1
        if check: print('ينقصه:', p[len(R):]); continue
        if h.count('</body>') != 1: print('تخطّي:', p[len(R):]); continue
        open(p, 'w', encoding='utf8').write(h.replace('</body>', TAG + '</body>', 1)); changed += 1
    print('%d صفحة تحتاج، عُدّلت %d' % (todo, changed))
    return 1 if (check and todo) else 0

if __name__ == '__main__': sys.exit(main())
