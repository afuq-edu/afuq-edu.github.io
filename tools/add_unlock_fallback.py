#!/usr/bin/env python3
"""Unlock keys without web storage. A package link (/p/#k…) unlocks its sections by writing keys to localStorage /
sessionStorage. Some browsers keep neither (e.g. the browser built into some school interactive screens, or an app's
web view with DOM storage switched off), so every section then bounced to «هذا القسم مخصص للباقة الذهبية».
p/index.html now also writes each key as a cookie and into window.name when localStorage does not work; this tool
makes every check of those keys read them too:
  - the gate at the top of each section page:  function g(n,x){…}
  - the subject pages' on(k)
  - assets/hwgate.js
  - the generator tools that write the gate (so new pages get it)
Idempotent. Usage: python3 tools/add_unlock_fallback.py"""
import os, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'

FB = "try{return new RegExp('(^|; )'+x+'=1(;|$)').test(document.cookie)||(' '+window.name+' ').indexOf(' '+x+' ')>=0}catch(e){return false}"
G_OLD = "function g(n,x){try{return window[n].getItem(x)==='1'}catch(e){return false}}"
G_NEW = "function g(n,x){try{if(window[n].getItem(x)==='1')return true}catch(e){}" + FB + "}"
ON_OLD = "    try{if(sessionStorage.getItem(k)==='1')return true}catch(e){}\n    return false;"
ON_NEW = ("    try{if(sessionStorage.getItem(k)==='1')return true}catch(e){}\n"
          "    try{if(new RegExp('(^|; )'+k+'=1(;|$)').test(document.cookie)||(' '+window.name+' ').indexOf(' '+k+' ')>=0)return true}catch(e){}\n"
          "    return false;")
HW_OLD = "  try{ if(localStorage.getItem(k)==='1'||sessionStorage.getItem(k)==='1') return; }catch(e){}"
HW_NEW = HW_OLD + "\n  try{ if(new RegExp('(^|; )'+k+'=1(;|$)').test(document.cookie)||(' '+window.name+' ').indexOf(' '+k+' ')>=0) return; }catch(e){}"
SKIP = ('/.git/', '/node_modules/')

def patch(path, pairs):
    s = open(path, encoding='utf8').read(); t = s
    for old, new in pairs:
        if new not in t: t = t.replace(old, new)
    if t != s: open(path, 'w', encoding='utf8').write(t); return True
    return False

def main():
    n = {'pages': 0, 'tools': 0, 'assets': 0}
    for p in glob.glob(R + '**/*.html', recursive=True):
        if any(x in p for x in SKIP): continue
        if patch(p, [(G_OLD, G_NEW), (ON_OLD, ON_NEW)]): n['pages'] += 1
    for p in glob.glob(R + 'tools/*.py'):
        if p.endswith('add_unlock_fallback.py'): continue
        if patch(p, [(G_OLD, G_NEW)]): n['tools'] += 1
    if patch(R + 'assets/hwgate.js', [(HW_OLD, HW_NEW)]): n['assets'] += 1
    print('unlock fallback: %(pages)d pages, %(tools)d tools, %(assets)d assets updated' % n)

if __name__ == '__main__': main()
