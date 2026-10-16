#!/usr/bin/env python3
"""Make the 1600x900 interactive decks fit any screen and open full screen.
- #stage is a flex item: without flex:none the browser shrinks it to the window width before fit() scales it,
  which crops the slide (and squeezes it to a sliver on phones).
- Browsers only allow full screen after a user gesture, so the first tap/click/key on the deck enters full screen
  (and turns phones to landscape where the browser allows it); a ⛶ button toggles it afterwards.
- A small 'turn the phone' hint shows in portrait on phones.
Idempotent; rerunning replaces an older version of the block.
Usage: python3 tools/fit_slides.py FILE.html [...]   (files that are not this deck engine are skipped)"""
import sys, re
FIX = ('<!--afuq-fit--><style id="afuq-fit">#stage{flex:none!important}'
       '#afuqRot{display:none;position:fixed;top:76px;left:50%;transform:translateX(-50%);z-index:60;background:rgba(15,23,42,.85);color:#fff;'
       'font:700 14px/1.4 Tahoma,system-ui,sans-serif;padding:8px 14px;border-radius:999px;direction:rtl;white-space:nowrap;cursor:pointer}'
       '@media (orientation:portrait) and (max-width:700px){#afuqRot{display:block}}'
       '#afuqFs{position:fixed;top:14px;right:74px;width:50px;height:50px;border-radius:14px;border:0;background:rgba(255,255,255,.18);'
       'color:#fff;font-size:24px;line-height:50px;text-align:center;z-index:55;cursor:pointer;opacity:.7;padding:0}#afuqFs:hover{opacity:1}'
       ':fullscreen #afuqRot{display:none!important}</style>'
       '<script>(function(){var d=document,E=d.documentElement,asked=false;'
       'function on(){return d.fullscreenElement||d.webkitFullscreenElement}'
       'function enter(){var r=E.requestFullscreen||E.webkitRequestFullscreen;if(!r||on())return;try{var p=r.call(E,{navigationUI:"hide"});'
       'var lock=function(){try{if(matchMedia("(pointer:coarse)").matches&&screen.orientation&&screen.orientation.lock)screen.orientation.lock("landscape").catch(function(){})}catch(e){}};'
       'if(p&&p.then)p.then(lock,function(){});else lock()}catch(e){}}'
       'function leave(){var x=d.exitFullscreen||d.webkitExitFullscreen;if(x&&on())x.call(d)}'
       'function first(e){if(asked)return;asked=true;if(e&&e.target&&e.target.id==="afuqFs")return;enter()}'
       '["pointerdown","keydown"].forEach(function(t){addEventListener(t,first,{capture:true,once:true})});'
       'addEventListener("DOMContentLoaded",function(){var h=d.createElement("div");h.id="afuqRot";h.textContent="\U0001F4F1↻ أدر الهاتف أفقيًا لعرض أكبر";'
       'h.onclick=function(){h.remove()};d.body.appendChild(h);'
       'if(E.requestFullscreen||E.webkitRequestFullscreen){var b=d.createElement("button");b.id="afuqFs";b.type="button";b.title="ملء الشاشة";b.textContent="⛶";'
       'b.onclick=function(ev){ev.stopPropagation();asked=true;on()?leave():enter()};d.body.appendChild(b)}})})()</script><!--/afuq-fit-->')
KEY = 'function fit(){const k=Math.min(innerWidth/1600,innerHeight/900)'
OLD = re.compile(r'<!--afuq-fit-->.*?<!--/afuq-fit-->|<style id="afuq-fit">.*?</style><script>addEventListener\("DOMContentLoaded".*?</script>', re.S)
PKG = '<script src="/assets/pkgmode.js" data-role="page"></script>'
def fix(p):
    h = open(p, encoding='utf8').read()
    if KEY not in h: return 'skip (other engine)'
    if FIX in h: return 'already'
    h2, n = OLD.subn('', h, count=1)
    i = h2.index('<head>') + len('<head>')
    j = h2.find(PKG, i)
    if j != -1 and j < i + 2000: i = j + len(PKG)
    open(p, 'w', encoding='utf8').write(h2[:i] + FIX + h2[i:]); return 'updated' if n else 'fixed'
if __name__ == '__main__':
    for p in sys.argv[1:]: print(fix(p), p)
