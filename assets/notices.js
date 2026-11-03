/* «📢 الإعلانات» (owner, 2026-10-31; one «جديد» label per announcement, 2026-11-02): a button at the top of the home page and
   the link pages (/p/). Tapping it opens the announcements of /announce.json {"important":[{id, title, lines:[…], img?, imgAlt?, link?:{href,text}}]},
   newest first, each folded under its title. An announcement this device has not opened carries «جديد» (on its title and on the
   button); opening it removes the label for good on this device (localStorage).
   Usage: <div data-notices></div> + <script src="/assets/notices.js" defer></script>, or window.afuqNotices(element). */
(function(){
'use strict';
var css='.ntc-b{display:flex;align-items:center;gap:10px;width:100%;margin:0 0 12px;padding:12px 16px;border:2px solid #C53030;border-radius:14px;'+
 'background:#FFF5F5;color:#9B1C1C;font:inherit;font-weight:800;font-size:16px;cursor:pointer;text-align:start}'+
 '.ntc-b:hover{background:#FFE9E9}.ntc-b .ic{font-size:22px}.ntc-b .go{margin-inline-start:auto;font-size:13.5px;font-weight:700;opacity:.85}'+
 '.ntc-new{display:inline-block;padding:1px 9px;border-radius:999px;background:#E53E3E;color:#fff;font-size:12.5px;font-weight:800;line-height:1.7;white-space:nowrap}'+
 '.ntc-b .ntc-new{animation:ntcP 1.6s infinite}'+
 '@keyframes ntcP{0%{box-shadow:0 0 0 0 #E53E3E99}70%{box-shadow:0 0 0 8px #E53E3E00}100%{box-shadow:0 0 0 0 #E53E3E00}}@media (prefers-reduced-motion:reduce){.ntc-b .ntc-new{animation:none}}'+
 '.ntc-d{border:0;border-radius:18px;padding:0;width:min(600px,calc(100vw - 24px));max-height:calc(100vh - 32px);overflow:auto;background:#fff;color:#1A202C;box-shadow:0 24px 70px #0007}'+
 '.ntc-d::backdrop{background:#0b1220b3}.ntc-in{padding:18px 16px 16px;direction:rtl;text-align:right}'+
 '.ntc-in>h2{margin:0 0 12px;font-size:20px;font-weight:900;color:#9B1C1C}'+
 '.ntc-n{border:2px solid #C53030;border-radius:14px;margin:0 0 12px;background:#FFF5F5;overflow:hidden}'+
 '.ntc-n>summary{list-style:none;display:flex;align-items:center;gap:8px;padding:12px 14px;cursor:pointer;color:#C53030;font-size:18px;font-weight:900}'+
 '.ntc-n>summary::-webkit-details-marker{display:none}.ntc-n>summary .ar{margin-inline-start:auto;font-size:13px;font-weight:700;opacity:.8}'+
 '.ntc-n[open]>summary .ar{transform:rotate(180deg)}.ntc-body{padding:0 14px 12px}'+
 '.ntc-body p{margin:6px 0;font-size:17px;font-weight:800;line-height:1.9;color:#1A202C}'+
 '.ntc-body a.im{display:block;margin:4px 0 8px}.ntc-body img{display:block;width:100%;height:auto;border-radius:12px;border:1px solid #F1C7C7}'+
 '.ntc-body a.go{display:block;margin:10px 0 2px;padding:11px;border-radius:12px;background:#2F6FB3;color:#fff;text-align:center;text-decoration:none;font-weight:800;font-size:16px}'+
 '.ntc-x{display:block;width:100%;padding:11px;border:0;border-radius:12px;background:#C53030;color:#fff;font:inherit;font-weight:800;font-size:16px;cursor:pointer}'+
 '@media (prefers-color-scheme:dark){.ntc-b{background:#3A1418;color:#FFB4B4;border-color:#FF7A7A}.ntc-b:hover{background:#4A1A1F}'+
 '.ntc-d{background:#172238;color:#E6ECF6}.ntc-in>h2{color:#FFB4B4}.ntc-n{background:#2A1620;border-color:#FF7A7A}.ntc-n>summary{color:#FF9A9A}.ntc-body p{color:#F2F5FA}}';
var NS=null, KEY='afuq-notices-read', OLD='afuq-notices-seen';
function load(){ return NS||(NS=fetch('/announce.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():{};}).then(function(j){return (j&&j.important)||[];}).catch(function(){return [];})); }
function idOf(a){ return String(a.id||a.title||''); }
function read(){ var r=[]; try{ r=JSON.parse(localStorage.getItem(KEY)||'[]')||[]; if(!r.length&&localStorage.getItem(OLD)) r=['rules']; }catch(e){} return r; }   /* opened before the labels: the rules notice */
function markRead(id){ var r=read(); if(r.indexOf(id)<0){ r.push(id); try{ localStorage.setItem(KEY,JSON.stringify(r)); }catch(e){} } }
function unread(list){ var r=read(); return list.filter(function(a){ return r.indexOf(idOf(a))<0; }); }
function mk(t,c,x){ var n=document.createElement(t); if(c)n.className=c; if(x!=null)n.textContent=x; return n; }
function show(list,onChange){
  var d=mk('dialog','ntc-d'),box=mk('div','ntc-in'); d.setAttribute('aria-label','الإعلانات');
  box.append(mk('h2',null,'📢 الإعلانات'));
  var r=read();
  list.forEach(function(a){
    var id=idOf(a), n=mk('details','ntc-n'), s=mk('summary'), body=mk('div','ntc-body');
    s.append(mk('span',null,'📢 '+(a.title||'إعلان')));
    if(r.indexOf(id)<0) s.append(mk('span','ntc-new','جديد'));
    s.append(mk('span','ar','▾'));
    if(a.img){ var ln=mk('a','im'); ln.href=a.img; ln.target='_blank'; ln.rel='noopener'; var im=mk('img'); im.src=a.img; im.alt=a.imgAlt||a.title||''; im.loading='lazy'; ln.append(im); body.append(ln); }
    (a.lines||[a.text]).forEach(function(l){ if(l) body.append(mk('p',null,l)); });
    if(a.link&&a.link.href){ var go=mk('a','go',a.link.text||'افتح الرابط'); go.href=a.link.href; go.target='_blank'; go.rel='noopener'; body.append(go); }
    n.append(s,body); box.append(n);
    n.addEventListener('toggle',function(){ if(!n.open) return; markRead(id); var t=s.querySelector('.ntc-new'); if(t)t.remove(); onChange(); });
  });
  if(list.length===1) box.querySelector('details').open=true;
  var x=mk('button','ntc-x','حسنًا، فهمت'); x.type='button'; x.onclick=function(){d.close();}; box.append(x);
  d.append(box); document.body.append(d); d.addEventListener('close',function(){d.remove();});
  if(d.showModal)d.showModal(); else d.setAttribute('open','');
}
function mount(host){
  if(!host||host._ntc) return; host._ntc=1;
  load().then(function(list){
    if(!list.length) return;
    if(!document.getElementById('ntc-css')){ var s=mk('style'); s.id='ntc-css'; s.textContent=css; document.head.append(s); }
    var b=mk('button','ntc-b'); b.type='button';
    function paint(){ var u=unread(list).length; b.replaceChildren(mk('span','ic','📢'), mk('span',null,'الإعلانات'+(list.length>1?' ('+list.length.toLocaleString('ar')+')':'')));
      if(u) b.append(mk('span','ntc-new',u>1?'جديد ('+u.toLocaleString('ar')+')':'جديد'));
      b.append(mk('span','go','اضغط لقراءة الإعلانات ←')); }
    paint(); b.onclick=function(){ show(list,paint); };
    host.replaceChildren(b);
  });
}
window.afuqNotices=mount;
function auto(){ Array.prototype.forEach.call(document.querySelectorAll('[data-notices]'),mount); }
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',auto); else auto();
})();
