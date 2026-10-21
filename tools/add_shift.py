#!/usr/bin/env python3
"""«فترة · ٤٠ د / فترتان · ٣٥ د» in every prep page (assets/shift.js): loads the script first in <head> and passes each
JSON data literal through it, so with two shifts the page draws (and its copy buttons copy) 35-minute plans.
  NAME=<json>                          -> NAME=(window.AFUQ35||function(x){return x})(<json>)
  <script type="application/json">…   -> followed by <script>window.AFUQ35&&AFUQ35.el(…previousElementSibling)</script>
Usage: python3 tools/add_shift.py [grade/subject ...]   Rerunning is a no-op; build_quiz.py runs it after writing the preps.
9/physics/prep35 is already a 35-minute plan, and a page with its own 40/35 switch (7/science/prep) is left out."""
import re, os, sys, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
TAG = '<script src="/assets/shift.js"></script>'
WRAP = '(window.AFUQ35||function(x){return x})('
OWN = re.compile(r'حصة (?:35|٣٥) دقيقة')   # the page's own switch
HOOK = '<script>window.AFUQ35&&AFUQ35.el(document.currentScript.previousElementSibling)</script>'

def pages():
    return sorted(p for p in glob.glob(R + '[0-9]*/*/prep/index.html') + glob.glob(R + '[0-9]*/*/prep/u*/index.html') +
                  glob.glob(R + '[0-9]*/*/prep[0-9]*/index.html') if not re.search(r'/prep35/', p))

def fix(h):
    from build_quiz import literals
    lits = sorted(literals(h), key=lambda x: x[1])
    keep, end = [], -1
    for L in lits:                       # a literal inside another one is the outer one's text
        if L[1] >= end: keep.append(L); end = L[2]
    for name, i, e, o in reversed(keep):
        if name == '#json':
            close = h.find('</script>', e) + len('</script>')
            if not h.startswith(HOOK, close): h = h[:close] + HOOK + h[close:]
        elif not h[:i].endswith(WRAP): h = h[:i] + WRAP + h[i:e] + ')' + h[e:]
    if TAG not in h: h = re.sub(r'<head[^>]*>', lambda m: m.group(0) + TAG, h, count=1)
    return h

def main():
    only = [a.strip('/') for a in sys.argv[1:]]; n = 0
    for p in pages():
        rel = p[len(R):]
        if only and '/'.join(rel.split('/')[:2]) not in only: continue
        h = open(p, encoding='utf8').read()
        if TAG not in h and OWN.search(h): continue
        t = fix(h)
        if t != h: open(p, 'w', encoding='utf8').write(t); n += 1
    print('35-minute switch added to %d prep pages' % n)

if __name__ == '__main__': main()
