/* Custom-link (package) mode. A visitor who opened a custom link /p/#… sees only that package:
   the platform hub, programs and subject portals send them back to their package page, section pages outside
   the package do the same, and allowed section pages get a "back" button to the package page.
   Opening a whole-platform link (/p/#*) or /?afuq-exit ends the mode on that device. */
(function(){
  var K='afuq-pkg-home', P='afuq-pkg-paths', home='', paths=[];
  try{
    if(/[?&]afuq-exit\b/.test(location.search)){ localStorage.removeItem(K); localStorage.removeItem(P); return; }
    home=localStorage.getItem(K)||''; paths=JSON.parse(localStorage.getItem(P)||'[]');
  }catch(e){ return; }
  if(!home) return;
  var s=document.currentScript, role=s&&s.getAttribute('data-role');
  function out(){ document.documentElement.style.display='none'; location.replace(home); }
  if(role==='gate') return out();
  var here=location.pathname.replace(/index\.html$/,'');
  if(!paths.some(function(p){ return here.indexOf('/'+p)===0; })) return out();
  function btn(){
    if(document.getElementById('afuqPkgBack')) return;
    var a=document.createElement('a'); a.id='afuqPkgBack'; a.href=home; a.textContent='→ رجوع';
    a.setAttribute('style','position:fixed;top:10px;left:10px;z-index:2147483647;background:#2F6FB3;color:#fff;font:700 14px/1 system-ui,Tahoma,sans-serif;padding:9px 14px;border-radius:999px;text-decoration:none;box-shadow:0 4px 14px #0004;direction:rtl');
    document.body.appendChild(a);
  }
  if(document.body) btn(); else document.addEventListener('DOMContentLoaded',btn);
})();
