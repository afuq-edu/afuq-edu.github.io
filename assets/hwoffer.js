/* «الواجبات التلقائية» offer card (owner, 2026-11-03): above «منصة المعلم» on the home page (gifts section) and the link pages (/p/).
   Tapping it opens the details and the button to install the «حاضر» tool. Usage: <div data-hwoffer></div> + this script (defer),
   or window.afuqHwOffer(element). Edit the text here. */
(function(){
'use strict';
var PHONE='76506037', INSTALL='/afaq-subscribe/install.html';
var TITLE='الواجبات التلقائية · عرض بريالين', SUB='واجب مصحَّح تلقائيًا لكل درس في منصة نور · اضغط للتفاصيل';
var LINES=['📝 لكل عنوان درس واجب في قسم «المهام الإلكترونية» بمنصة نور، فتزيد نقاطك في المنصة بشكل ملحوظ.',
  '✅ الواجب يُصحَّح تلقائيًا، وتظهر الدرجة لدى المعلم والطالب في منصة نور.',
  '⚡ الواجبات تدخل تلقائيًا عن طريق أداة «حاضر»: تختار الدروس فقط.',
  '💳 طريقة الاشتراك: ادفع الرسوم (ريالان)، ثم أرسل اسمك بالكامل كما هو في منصة نور إلى المشرف ('+PHONE+').'];
var css='.hwo{display:flex;align-items:center;gap:12px;width:100%;margin:0 0 12px;padding:14px 16px;border:2px solid #2F6FB3;border-radius:14px;'+
 'background:#EEF5FF;color:#14325C;font:inherit;text-align:start;cursor:pointer}.hwo:hover{background:#E2EEFF}'+
 '.hwo .gi{font-size:26px}.hwo b{display:block;font-size:16px;font-weight:800}.hwo small{display:block;color:#3E5B82;font-size:13px}'+
 '.hwo .tag{margin-inline-start:auto;flex:none;padding:2px 10px;border-radius:999px;background:#2F6FB3;color:#fff;font-size:12.5px;font-weight:800}'+
 '.hwo-d{border:0;border-radius:18px;padding:0;width:min(560px,calc(100vw - 24px));max-height:calc(100vh - 32px);overflow:auto;background:#fff;color:#1A202C;box-shadow:0 24px 70px #0007}'+
 '.hwo-d::backdrop{background:#0b1220b3}.hwo-in{padding:20px 18px 16px;direction:rtl;text-align:right}.hwo-in h3{margin:0 0 10px;color:#1F5A9E;font-size:20px;font-weight:900}'+
 '.hwo-in p{margin:6px 0;font-size:16.5px;font-weight:700;line-height:1.9}'+
 '.hwo-in a.go{display:block;margin:12px 0 8px;padding:11px;border-radius:12px;background:#2F6FB3;color:#fff;text-align:center;text-decoration:none;font-weight:800;font-size:16px}'+
 '.hwo-in .x{display:block;width:100%;padding:10px;border:1px solid #CBD5E1;border-radius:12px;background:transparent;color:inherit;font:inherit;font-weight:700;cursor:pointer}'+
 '@media (prefers-color-scheme:dark){.hwo{background:#16263F;color:#DCE8FA;border-color:#6EA8FF}.hwo:hover{background:#1B2E4C}.hwo small{color:#A9BEDC}'+
 '.hwo-d{background:#172238;color:#E6ECF6}.hwo-in h3{color:#8FBCFF}}';
function mk(t,c,x){ var n=document.createElement(t); if(c)n.className=c; if(x!=null)n.textContent=x; return n; }
function open(){
  var d=mk('dialog','hwo-d'), w=mk('div','hwo-in'); w.append(mk('h3',null,TITLE));
  LINES.forEach(function(l){ w.append(mk('p',null,l)); });
  var go=mk('a','go','⬇️ تثبيت أداة حاضر'); go.href=INSTALL; go.target='_blank'; go.rel='noopener'; w.append(go);
  var x=mk('button','x','إغلاق'); x.type='button'; x.onclick=function(){ d.close(); }; w.append(x);
  d.append(w); document.body.append(d); d.addEventListener('close',function(){ d.remove(); });
  if(d.showModal) d.showModal(); else d.setAttribute('open','');
}
function mount(host){
  if(!host||host._hwo) return; host._hwo=1;
  if(!document.getElementById('hwo-css')){ var s=mk('style'); s.id='hwo-css'; s.textContent=css; document.head.append(s); }
  var b=mk('button','hwo'); b.type='button'; var t=mk('span');
  t.append(mk('b',null,TITLE), mk('small',null,SUB)); b.append(mk('span','gi','📝'), t, mk('span','tag','عرض'));
  b.onclick=open; host.replaceChildren(b);
}
window.afuqHwOffer=mount;
function auto(){ Array.prototype.forEach.call(document.querySelectorAll('[data-hwoffer]'),mount); }
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',auto); else auto();
})();
