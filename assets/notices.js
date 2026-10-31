/* «📢 الإعلانات» (owner, 2026-10-31): a button at the top of the home page and the link pages (/p/); tapping it opens the
   important notices of /announce.json {"important":[{title, lines:[…]}]} in bold. A dot marks notices this device has not opened.
   Usage: <div data-notices></div> + <script src="/assets/notices.js" defer></script>, or window.afuqNotices(element). */
(function(){
'use strict';
var css='.ntc-b{display:flex;align-items:center;gap:10px;width:100%;margin:0 0 12px;padding:12px 16px;border:2px solid #C53030;border-radius:14px;'+
 'background:#FFF5F5;color:#9B1C1C;font:inherit;font-weight:800;font-size:16px;cursor:pointer;text-align:start}'+
 '.ntc-b:hover{background:#FFE9E9}.ntc-b .ic{font-size:22px}.ntc-b .go{margin-inline-start:auto;font-size:13.5px;font-weight:700;opacity:.85}'+
 '.ntc-b .dot{width:10px;height:10px;border-radius:50%;background:#E53E3E;box-shadow:0 0 0 0 #E53E3E99;animation:ntcP 1.6s infinite}'+
 '@keyframes ntcP{70%{box-shadow:0 0 0 9px #E53E3E00}100%{box-shadow:0 0 0 0 #E53E3E00}}@media (prefers-reduced-motion:reduce){.ntc-b .dot{animation:none}}'+
 '.ntc-d{border:0;border-radius:18px;padding:0;width:min(560px,calc(100vw - 32px));max-height:calc(100vh - 40px);overflow:auto;background:#fff;color:#1A202C;box-shadow:0 24px 70px #0007}'+
 '.ntc-d::backdrop{background:#0b1220b3}.ntc-in{padding:22px 22px 18px;direction:rtl;text-align:right}'+
 '.ntc-n{border:2px solid #C53030;border-radius:14px;padding:14px 16px;margin:0 0 12px;background:#FFF5F5}'+
 '.ntc-n h3{margin:0 0 8px;color:#C53030;font-size:22px;font-weight:900}.ntc-n p{margin:6px 0;font-size:18px;font-weight:800;line-height:1.9;color:#1A202C}'+
 '.ntc-x{display:block;width:100%;padding:11px;border:0;border-radius:12px;background:#C53030;color:#fff;font:inherit;font-weight:800;font-size:16px;cursor:pointer}'+
 '@media (prefers-color-scheme:dark){.ntc-b{background:#3A1418;color:#FFB4B4;border-color:#FF7A7A}.ntc-b:hover{background:#4A1A1F}'+
 '.ntc-d{background:#172238;color:#E6ECF6}.ntc-n{background:#2A1620;border-color:#FF7A7A}.ntc-n h3{color:#FF9A9A}.ntc-n p{color:#F2F5FA}}';
var NS=null, KEY='afuq-notices-seen';
function load(){ return NS||(NS=fetch('/announce.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():{};}).then(function(j){return (j&&j.important)||[];}).catch(function(){return [];})); }
function sig(list){ var s=JSON.stringify(list),h=0; for(var i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))|0; return String(h); }
function seen(){ try{return localStorage.getItem(KEY)||'';}catch(e){return '';} }
function mk(t,c,x){ var n=document.createElement(t); if(c)n.className=c; if(x!=null)n.textContent=x; return n; }
function show(list){
  var d=mk('dialog','ntc-d'),box=mk('div','ntc-in'); d.setAttribute('aria-label','الإعلانات');
  list.forEach(function(a){ var n=mk('section','ntc-n'); n.append(mk('h3',null,'📢 '+(a.title||'إعلان'))); (a.lines||[a.text]).forEach(function(l){ if(l) n.append(mk('p',null,l)); }); box.append(n); });
  var x=mk('button','ntc-x','حسنًا، فهمت'); x.type='button'; x.onclick=function(){d.close();}; box.append(x);
  d.append(box); document.body.append(d); d.addEventListener('close',function(){d.remove();});
  if(d.showModal)d.showModal(); else d.setAttribute('open','');
}
function mount(host){
  if(!host||host._ntc) return; host._ntc=1;
  load().then(function(list){
    if(!list.length) return;
    if(!document.getElementById('ntc-css')){ var s=mk('style'); s.id='ntc-css'; s.textContent=css; document.head.append(s); }
    var b=mk('button','ntc-b'); b.type='button'; var k=sig(list);
    b.append(mk('span','ic','📢'), mk('span',null,'الإعلانات'+(list.length>1?' ('+list.length.toLocaleString('ar')+')':'')));
    if(seen()!==k) b.append(mk('span','dot'));
    b.append(mk('span','go','اضغط لقراءة الإعلان ←'));
    b.onclick=function(){ show(list); try{localStorage.setItem(KEY,k);}catch(e){} var dt=b.querySelector('.dot'); if(dt)dt.remove(); };
    host.replaceChildren(b);
  });
}
window.afuqNotices=mount;
function auto(){ Array.prototype.forEach.call(document.querySelectorAll('[data-notices]'),mount); }
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',auto); else auto();
})();
