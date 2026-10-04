/* Custom-link (package) mode. A visitor who opened a custom link /p/#… sees only that package:
   the platform hub, programs, grade/subject portals and any section outside the package send them back to the
   package page; allowed section pages get a "back" button and their "../" links point at the package page.
   Re-checked on bfcache restores and when another tab changes the mode. /?afuq-exit ends the mode on this device. */
(function(){
  var K='afuq-pkg-home', P='afuq-pkg-paths';
  var s=document.currentScript, role=s&&s.getAttribute('data-role'), going=false;
  try{ if(/[?&]afuq-exit\b/.test(location.search)){ localStorage.removeItem(K); localStorage.removeItem(P); try{ sessionStorage.removeItem(K); sessionStorage.removeItem(P); }catch(e){} return; } }catch(e){ return; }
  function get(k){ var v=''; try{ v=localStorage.getItem(k)||''; }catch(e){} if(!v){ try{ v=sessionStorage.getItem(k)||''; }catch(e){} } return v; }
  function state(){ try{ var h=get(K); return h?{home:h,paths:JSON.parse(get(P)||'[]')}:null; }catch(e){ return null; } }
  function out(home){ if(going) return; going=true; document.documentElement.style.display='none'; location.replace(home); }
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
    if(role==='gate' || !allowed(st)) return out(st.home);
    if(document.body) ui(st); else document.addEventListener('DOMContentLoaded',function(){ ui(st); });
  }
  check();
  window.addEventListener('pageshow',function(e){ if(e.persisted) check(); });
  window.addEventListener('storage',function(e){ if(e.key===K||e.key===P) check(); });
})();
