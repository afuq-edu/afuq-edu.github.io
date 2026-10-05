/* Custom-link (package) mode. A visitor who opened a custom link /p/#… sees only that package:
   the platform hub, programs, grade/subject portals and any section outside the package send them back to the
   package page; allowed section pages get a "back" button and their "../" links point at the package page.
   Re-checked on bfcache restores. Each tab follows the link it was opened with (sessionStorage); localStorage only holds
   the link opened most recently on the device, for tabs that have none, so another tab never pulls this one away.
   /?afuq-exit ends the mode on this device. */
(function(){
  var K='afuq-pkg-home', P='afuq-pkg-paths';
  var s=document.currentScript, role=s&&s.getAttribute('data-role'), going=false;
  if(/^\/\d+\/[a-z]+\/homework\/[^\/]+\//.test(location.pathname)) role='open'; /* student lesson links are never redirected */
  try{ if(/[?&]afuq-exit\b/.test(location.search)){ localStorage.removeItem(K); localStorage.removeItem(P); try{ sessionStorage.removeItem(K); sessionStorage.removeItem(P); sessionStorage.removeItem('afuq-pkg-all'); }catch(e){} return; } }catch(e){ return; }
  function rd(S,k){ try{ return window[S].getItem(k)||''; }catch(e){ return ''; } }
  function state(){
    try{
      var h=rd('sessionStorage',K), src='sessionStorage';
      if(!h){
        if(rd('sessionStorage','afuq-pkg-all')==='1') return null; /* this tab opened a full-platform link */
        h=rd('localStorage',K); src='localStorage';
      }
      if(!h) return null;
      var p=rd(src,P)||'[]';
      if(src==='localStorage'){ try{ sessionStorage.setItem(K,h); sessionStorage.setItem(P,p); }catch(e){} } /* from now on this tab keeps its own link */
      return {home:h,paths:JSON.parse(p)};
    }catch(e){ return null; }
  }
  function out(home){ if(going) return; going=true; try{ sessionStorage.setItem('afuq-pkg-ret','1'); }catch(e){} /* an automatic bounce must not make this link the device's newest */ document.documentElement.style.display='none'; location.replace(home); }
  function allowed(st){ var here=location.pathname.replace(/index\.html$/,''); return st.paths.some(function(p){ return here.indexOf('/'+p)===0; }); }
  function ui(st){
    Array.prototype.forEach.call(document.querySelectorAll('a[href="../"]'),function(a){ a.setAttribute('href',st.home); });
    if(document.getElementById('afuqPkgBack')) return;
    var a=document.createElement('a'); a.id='afuqPkgBack'; a.href=st.home; a.textContent='→ رجوع';
    a.setAttribute('style','position:fixed;top:10px;left:10px;z-index:2147483647;background:#2F6FB3;color:#fff;font:700 14px/1 system-ui,Tahoma,sans-serif;padding:9px 14px;border-radius:999px;text-decoration:none;box-shadow:0 4px 14px #0004;direction:rtl');
    document.body.appendChild(a);
  }
  function check(){
    var st=state(); if(!st) return;
    if(role==='open' && !allowed(st)) return; /* standalone page: never redirect, only add the back button when it belongs to the visitor's package */
    if(role==='gate' || !allowed(st)) return out(st.home);
    if(document.body) ui(st); else document.addEventListener('DOMContentLoaded',function(){ ui(st); });
  }
  check();
  window.addEventListener('pageshow',function(e){ if(e.persisted) check(); });
})();
