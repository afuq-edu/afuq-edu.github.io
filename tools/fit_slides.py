#!/usr/bin/env python3
"""Make every presentation page (slides / lessons / interactive) fit any screen and open full screen.
House rule: run this on every presentation page that is added or replaced (the add_* tools already do).
- A fixed-size #stage that is a flex item gets shrunk by the browser before the deck scales it, which crops the
  slide on PCs and squeezes it on phones; flex:none stops that (harmless for absolutely positioned stages).
- Browsers only allow full screen after a user gesture, so the first tap/click/key enters full screen (and turns
  phones to landscape where allowed). It runs just after the page's own handlers, so a deck's own full-screen
  button is never undone. Decks without their own full-screen button get a ⛶ toggle.
- While a wide slide is on screen in portrait on a phone, a small 'turn the phone' hint shows (tap hides it).
Idempotent; rerunning replaces an older version of the block.
Usage: python3 tools/fit_slides.py FILE.html [...]"""
import sys, re
NEW_ENGINE = 'function fit(){const k=Math.min(innerWidth/1600,innerHeight/900)'
CSS = ('#stage{flex:none!important}'
       '#afuqRot{display:none;position:fixed;top:76px;left:50%;transform:translateX(-50%);z-index:2147483000;background:rgba(15,23,42,.85);color:#fff;'
       'font:700 14px/1.4 Tahoma,system-ui,sans-serif;padding:8px 14px;border-radius:999px;direction:rtl;white-space:nowrap;cursor:pointer}'
       '#afuqRot.on{display:block}:fullscreen #afuqRot{display:none!important}'
       '#afuqFs{position:fixed;top:14px;right:74px;width:50px;height:50px;border-radius:14px;border:0;background:rgba(255,255,255,.18);'
       'color:#fff;font-size:24px;line-height:50px;text-align:center;z-index:55;cursor:pointer;opacity:.7;padding:0}#afuqFs:hover{opacity:1}')
JS = ('(function(){var d=document,E=d.documentElement,asked=false,BTN=%s;'
      'function on(){return d.fullscreenElement||d.webkitFullscreenElement}'
      'function enter(){var r=E.requestFullscreen||E.webkitRequestFullscreen;if(!r||on())return;try{var p=r.call(E,{navigationUI:"hide"});'
      'var lock=function(){try{if(matchMedia("(pointer:coarse)").matches&&screen.orientation&&screen.orientation.lock)screen.orientation.lock("landscape").catch(function(){})}catch(e){}};'
      'if(p&&p.then)p.then(lock,function(){});else lock()}catch(e){}}'
      'function leave(){var x=d.exitFullscreen||d.webkitExitFullscreen;if(x&&on())x.call(d)}'
      'function first(e){if(asked)return;asked=true;if(e&&e.target&&e.target.id==="afuqFs")return;var was=!!on();'
      'setTimeout(function(){if(!was&&!on())enter()},60)}'
      '["pointerdown","keydown"].forEach(function(t){addEventListener(t,first,{capture:true,once:true})});'
      'function wide(){var s=d.querySelector("#stage,#canvas,.stage");if(!s)return false;var r=s.getBoundingClientRect();return r.width>40&&r.height>20&&r.width/r.height>1.3}'
      'addEventListener("DOMContentLoaded",function(){var h=d.createElement("div"),gone=false;h.id="afuqRot";h.textContent="\U0001F4F1↻ أدر الهاتف أفقيًا لعرض أكبر";'
      'h.onclick=function(){gone=true;h.classList.remove("on")};d.body.appendChild(h);'
      'var mq=matchMedia("(orientation:portrait) and (max-width:700px)");setInterval(function(){h.classList.toggle("on",!gone&&mq.matches&&wide())},700);'
      'if(BTN&&(E.requestFullscreen||E.webkitRequestFullscreen)){var b=d.createElement("button");b.id="afuqFs";b.type="button";b.title="ملء الشاشة";b.textContent="⛶";'
      'b.onclick=function(ev){ev.stopPropagation();asked=true;on()?leave():enter()};d.body.appendChild(b)}})})()')
# engine-specific repairs: (marker in the page, extra CSS)
EXTRA = [('.stage-wrap{position:relative;min-height:0;display:grid', '#app{height:100%}')]  # 'ديني حياتي' grade 1: lesson grid had no height, slides were invisible
def block(btn, extra=''): return '<!--afuq-fit--><style id="afuq-fit">' + CSS + extra + '</style><script>' + (JS % ('true' if btn else 'false')) + '</script><!--/afuq-fit-->'
OLD = re.compile(r'<!--afuq-fit-->.*?<!--/afuq-fit-->|<style id="afuq-fit">.*?</style><script>addEventListener\("DOMContentLoaded".*?</script>', re.S)
PKG = '<script src="/assets/pkgmode.js" data-role="page"></script>'
def fix(p):
    h = open(p, encoding='utf8').read()
    if '<head>' not in h: return 'skip (no <head>)'
    own = 'requestFullscreen' in OLD.sub('', h)          # the deck has its own full-screen control
    FIX = block(btn=(NEW_ENGINE in h) or not own, extra=''.join(c for m, c in EXTRA if m in h))
    if FIX in h: return 'already'
    h2, n = OLD.subn('', h, count=1)
    i = h2.index('<head>') + len('<head>')
    j = h2.find(PKG, i)
    if j != -1 and j < i + 2000: i = j + len(PKG)
    open(p, 'w', encoding='utf8').write(h2[:i] + FIX + h2[i:]); return 'updated' if n else 'fixed'
if __name__ == '__main__':
    for p in sys.argv[1:]: print(fix(p), p)
