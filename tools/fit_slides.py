#!/usr/bin/env python3
"""Make the 1600x900 interactive decks fit any screen: the #stage is a flex item, so without flex:none the browser
shrinks it to the window width before fit() scales it, which crops the slide (and squeezes it to a sliver on phones).
Also shows a small 'turn the phone' hint in portrait on phones. Idempotent.
Usage: python3 tools/fit_slides.py FILE.html [...]   (files that are not this deck engine are skipped)"""
import sys
FIX = ('<style id="afuq-fit">#stage{flex:none!important}'
       '#afuqRot{display:none;position:fixed;top:14px;left:50%;transform:translateX(-50%);z-index:60;background:rgba(15,23,42,.85);color:#fff;'
       'font:700 14px/1.4 Tahoma,system-ui,sans-serif;padding:8px 14px;border-radius:999px;direction:rtl;white-space:nowrap;cursor:pointer}'
       '@media (orientation:portrait) and (max-width:700px){#afuqRot{display:block}}</style>'
       '<script>addEventListener("DOMContentLoaded",function(){var d=document.createElement("div");d.id="afuqRot";'
       'd.textContent="\U0001F4F1↻ أدر الهاتف أفقيًا لعرض أكبر";d.onclick=function(){d.remove()};document.body.appendChild(d)})</script>')
KEY = 'function fit(){const k=Math.min(innerWidth/1600,innerHeight/900)'
def fix(p):
    h = open(p, encoding='utf8').read()
    if KEY not in h: return 'skip (other engine)'
    if 'id="afuq-fit"' in h: return 'already'
    i = h.index('<head>') + len('<head>')
    j = h.find('<script src="/assets/pkgmode.js" data-role="page"></script>', i)
    if j != -1 and j < i + 2000: i = j + len('<script src="/assets/pkgmode.js" data-role="page"></script>')
    open(p, 'w', encoding='utf8').write(h[:i] + FIX + h[i:]); return 'fixed'
if __name__ == '__main__':
    for p in sys.argv[1:]: print(fix(p), p)
