/* «⬇️ تنزيل الشهادة» (owner, 2026-11-10: «اجعل الشهادة قابلة للتنزيل»): every certificate shown on a page as a `.cert` box (homework,
   harvest, explorers) gets a download button next to its print button. It draws the certificate on a canvas (1600×1130, the same look
   as the lesson-games certificate) from the box's own text — name, title, stars, scores, date — and saves a PNG named
   «Afuq-Certificate-<التاريخ>.png»; on phones that can share files it offers the share sheet first (save to Photos / Files / WhatsApp).
   Usage: <script src="/assets/certdl.js" defer></script> (homework pages load it from hwcommon.js). Pages whose certificate is
   already downloadable (the lesson games, SCORM) don't include it. */
(function(){
'use strict';
var FONT=[['400','/assets/f/6231d7c967bf36a7.ttf'],['700','/assets/f/3028c3b3afa120de.ttf']], F='AfuqCert,Tahoma,"Segoe UI",sans-serif', fontsReady=null;
function loadFonts(){ if(fontsReady) return fontsReady;
  fontsReady=Promise.all(FONT.map(function(f){ try{ var ff=new FontFace('AfuqCert','url('+f[1]+')',{weight:f[0]}); document.fonts.add(ff); return ff.load().catch(function(){}); }catch(e){ return null; } })); return fontsReady; }
function tx(n){ var c=n.cloneNode(true); [].forEach.call(c.querySelectorAll('br'),function(b){ b.replaceWith('\n'); }); return c.textContent.replace(/[ \t]+/g,' ').replace(/ *\n */g,'\n').trim(); }
function visible(el){ return !!(el&&el.isConnected&&el.getClientRects().length&&getComputedStyle(el).visibility!=='hidden'); }
/* the certificate's text lines, in order: [{t, role}] role: title | name | stars | row | text */
function lines(el){ var out=[];
  (function walk(n){
    var kids=[].filter.call(n.children,function(c){ return !/^(SCRIPT|STYLE|BUTTON|CANVAS|INPUT|LABEL)$/.test(c.tagName)&&!/(^|\s)(corner|seal|ico)(\s|$)/.test(c.className||'')&&!c.hidden; });
    var blocky=kids.some(function(c){ return /^(DIV|P|H[1-6]|UL|OL|SECTION)$/.test(c.tagName); });
    if(!kids.length||!blocky){
      var cls=' '+(n.className||'')+' ', t=tx(n); if(!t) return;
      var spans=kids.length>1&&kids.every(function(c){ return c.tagName==='SPAN'; })?kids.map(tx).filter(Boolean):null;
      var role=/ (n|cn|name|nm) /.test(cls)?'name':/^[⭐★✨\s]+$/.test(t)?'stars':spans?'row':'text';
      out.push({t:t,role:role,spans:spans});
    } else kids.forEach(walk);
  })(el);
  var ti=-1; out.forEach(function(l,i){ if(ti<0&&l.role==='text'&&/شهادة|certificate/i.test(l.t)&&l.t.length<40){ l.role='title'; ti=i; } });
  return out; }
function wrap(x,t,max){ var out=[]; t.split('\n').forEach(function(p){ var w=p.split(' '),cur='';
  w.forEach(function(s){ var n=cur?cur+' '+s:s; if(x.measureText(n).width>max&&cur){ out.push(cur); cur=s; } else cur=n; }); out.push(cur); }); return out; }
function draw(ls){
  var W=1600,H=1130,c=document.createElement('canvas');c.width=W;c.height=H;var x=c.getContext('2d');
  var g=x.createLinearGradient(0,0,W,H);g.addColorStop(0,'#FFFDF6');g.addColorStop(1,'#F2FAF8');x.fillStyle=g;x.fillRect(0,0,W,H);
  x.strokeStyle='#C99A2E';x.lineWidth=14;x.strokeRect(30,30,W-60,H-60);x.strokeStyle='#1F7A7A';x.lineWidth=4;x.strokeRect(56,56,W-112,H-112);
  x.direction='rtl';x.textAlign='center';x.textBaseline='alphabetic';
  var max=W-300, S=1, rows;
  function layout(s){ var r=[],h=0;
    ls.forEach(function(l){
      var fs=l.role==='title'?84:l.role==='name'?70:l.role==='stars'?60:l.role==='row'?30:36, wt=(l.role==='title'||l.role==='name'||l.role==='row')?'700':'400';
      var f=Math.round(fs*s); x.font=wt+' '+f+'px '+F;
      var lh=Math.round(f*1.45), ln=l.role==='row'?[l.spans.join('   ·   ')]:wrap(x,l.t,max);
      if(l.role==='row'&&x.measureText(ln[0]).width>max) ln=wrap(x,l.spans.join('   ·   '),max);
      r.push({l:l,f:f,wt:wt,lh:lh,ln:ln,gap:l.role==='title'?Math.round(14*s):Math.round(8*s)}); h+=ln.length*lh+r[r.length-1].gap; });
    return {r:r,h:h}; }
  var L=layout(1); while(L.h>H-420&&S>.45){ S-=.05; L=layout(S); }
  rows=L.r;
  x.fillStyle='#1F7A7A';x.font='700 34px '+F;x.fillText('منصة أفق التعليمية',W/2,140);
  var y=(H+170-L.h)/2+rows[0].f*.2;
  rows.forEach(function(o){ var col=o.l.role==='title'?'#B27A00':o.l.role==='name'?'#1F7A7A':o.l.role==='row'?'#1F7A7A':'#22313A';
    x.fillStyle=col;x.font=o.wt+' '+o.f+'px '+F;
    o.ln.forEach(function(t){ y+=o.lh; x.fillText(t,W/2,y);
      if(o.l.role==='name'){ x.strokeStyle='#E3C77A';x.lineWidth=3;x.beginPath();x.moveTo(W/2-330,y+14);x.lineTo(W/2+330,y+14);x.stroke(); } });
    y+=o.gap; });
  ['⭐','⭐','⭐','⭐'].forEach(function(s,k){ x.font='46px '+F; x.fillText(s,k%2?W-110:110,k<2?125:H-90); });
  return c; }
function fname(){ var d=new Date(),p=function(n){ return (n<10?'0':'')+n; };   /* an ASCII name: browsers drop a non-Latin download name («download») */
  return 'Afuq-Certificate-'+d.getFullYear()+p(d.getMonth()+1)+p(d.getDate())+'-'+p(d.getHours())+p(d.getMinutes())+'.png'; }
function save(el,btn){
  var ls=lines(el); if(!ls.length) return; var lab=btn.textContent; btn.disabled=true; btn.textContent='⏳ جارٍ التجهيز…';
  loadFonts().then(function(){ return new Promise(function(r){ requestAnimationFrame(function(){ r(); }); }); }).then(function(){
    var c=draw(ls), name=fname(ls);
    c.toBlob(function(b){
      btn.disabled=false; btn.textContent=lab; if(!b) return;
      var file; try{ file=new File([b],name,{type:'image/png'}); }catch(e){}
      var done=function(){ var u=URL.createObjectURL(b), a=document.createElement('a'); a.href=u; a.download=name; document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function(){ URL.revokeObjectURL(u); },4000); };
      if(file&&navigator.canShare&&navigator.canShare({files:[file]})&&/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)){
        navigator.share({files:[file],title:'شهادة إنجاز'}).catch(function(e){ if(e&&e.name!=='AbortError') done(); }); }
      else done();
    },'image/png'); });
}
var HOOK=new WeakMap();
function attach(cert){
  if(HOOK.has(cert)) return; var prt=document.getElementById('prt')||document.getElementById('bPrint')||[].filter.call(document.querySelectorAll('button'),function(b){ return /طباعة الشهادة/.test(b.textContent); })[0];
  var b=document.createElement('button'); b.type='button'; b.className=(prt&&prt.className)||'btn alt'; b.textContent='⬇️ تنزيل الشهادة (صورة)'; b.id='certDl';
  b.onclick=function(){ save(cert,b); }; HOOK.set(cert,b);
  if(prt&&prt.parentNode) prt.parentNode.insertBefore(b,prt.nextSibling); else cert.parentNode.insertBefore(b,cert.nextSibling);
  [].forEach.call(document.querySelectorAll('#shot,#eHint'),function(h){ h.textContent=h.textContent.replace(/للتسليم:.*$/,'للتسليم: نزّل الشهادة صورة (أو اطبعها) وأرفقها في منصة نور.'); });
}
function sync(){ [].forEach.call(document.querySelectorAll('.cert'),function(c){ if(visible(c)&&tx(c).length>20) attach(c); var b=HOOK.get(c); if(b) b.hidden=!visible(c); }); }
var t=null; function soon(){ clearTimeout(t); t=setTimeout(sync,120); }
new MutationObserver(soon).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['class','hidden','style']});
if(document.readyState!=='loading') soon(); else document.addEventListener('DOMContentLoaded',soon);
window.AfuqCertDownload=function(el){ var b=HOOK.get(el)||document.createElement('button'); save(el,b); };
})();
