/* Custom-link (package) mode. A visitor who opened a custom link /p/#… sees only that package:
   the platform hub, programs, grade/subject portals and any section outside the package send them back to the
   package page; allowed section pages get a "back" button and their "../" links point at the package page.
   Re-checked on bfcache restores. Each tab follows the link it was opened with (sessionStorage); localStorage only holds
   the link opened most recently on the device, for tabs that have none, so another tab never pulls this one away.
   /?afuq-exit ends the mode on this device. */
(function(){
  var K='afuq-pkg-home', P='afuq-pkg-paths';
  var s=document.currentScript, role=s&&s.getAttribute('data-role'), going=false;
  if(/^\/\d+\/[a-z]+\/(?:homework|harvest)\/[^\/]+\//.test(location.pathname)) role='open'; /* student lesson / harvest-unit links are never redirected */
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
  // Trial links (/p/#t…) unlock this tab for one hour only: when it ends, forget them and go back to the link page,
  // which explains that the trial is over.
  function trialEnd(){ var t=+rd('sessionStorage','afuq-trial-exp'); return t>0?t:0; }
  function trialOver(){
    var t=trialEnd(); if(!t||Date.now()<=t) return false;
    var home=rd('sessionStorage',K)||'/p/';
    try{ for(var i=sessionStorage.length-1;i>=0;i--){ var k=sessionStorage.key(i); if(/^(ofuq-|afuq-all|afuq-pkg-paths|afuq-pkg-all)/.test(k)) sessionStorage.removeItem(k); } }catch(e){}
    out(home); return true;
  }
  // Plain links (/p/#…!) open the subjects' other sections for a few hours (see p/index.html): when that ends, those
  // sections are taken out of this tab's package, so the normal check below sends the visitor back to the link page.
  function previewEnd(){ var t=+rd('sessionStorage','afuq-prev-exp'); return t>0?t:0; }
  function previewOver(){
    var t=previewEnd(); if(!t||Date.now()<=t) return false;
    try{
      JSON.parse(rd('sessionStorage','afuq-prev-keys')||'[]').forEach(function(k){ sessionStorage.removeItem(k); });
      sessionStorage.setItem(P,rd('sessionStorage','afuq-prev-base')||'[]');
      ['afuq-prev-exp','afuq-prev-keys','afuq-prev-base'].forEach(function(k){ sessionStorage.removeItem(k); });
    }catch(e){}
    return true;
  }
  function check(){
    if(trialOver()) return;
    previewOver();
    var pe=previewEnd(); if(pe&&!check.ptimer) check.ptimer=setTimeout(function(){ check.ptimer=0; check(); }, pe-Date.now()+500);
    var t=trialEnd(); if(t&&!check.timer) check.timer=setTimeout(function(){ check.timer=0; check(); }, t-Date.now()+500);
    var st=state(); if(!st) return;
    if(role==='open' && !allowed(st)) return; /* standalone page: never redirect, only add the back button when it belongs to the visitor's package */
    if(role==='gate' || !allowed(st)) return out(st.home);
    if(document.body) ui(st); else document.addEventListener('DOMContentLoaded',function(){ ui(st); });
  }
  // A stable link this device has used may have been cancelled ("-" in /p/packages.json): its page takes back what it opened.
  function cancelled(){
    if(role==='open'||!window.fetch) return;
    var codes=[]; try{ for(var i=0;i<localStorage.length;i++){ var k=localStorage.key(i); if(k&&k.indexOf('afuq-pkg-k:')===0) codes.push(k.slice(11)); } }catch(e){ return; }
    if(!codes.length) return;
    fetch('/p/packages.json').then(function(r){ return r.ok?r.json():null; }).then(function(j){
      if(j) for(var i=0;i<codes.length;i++) if(j[codes[i]]==='-') return out('/p/#'+codes[i]);
    }).catch(function(){});
  }
  check(); cancelled();
  window.addEventListener('pageshow',function(e){ if(e.persisted) check(); });
  document.addEventListener('visibilitychange',function(){ if(!document.hidden && !trialOver() && previewOver()) check(); });
})();
