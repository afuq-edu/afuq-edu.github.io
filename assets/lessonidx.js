/* Interactive decks (window.DECK): open on a list of the lessons instead of one long run of hundreds of slides.
   Teacher deck (data-mode="teacher"): each lesson has «دخول» (that lesson with the teacher notes, ?l=<id>), «تشغيل» (the
   student page) and «نسخ لمنصة نور» (the student link of that lesson only + a short message); ?all=1 shows every slide.
   Student page (data-mode="student", files repo /afuq/<g>/<s>/view/<sec>/): ?l=<id> shows that lesson only, nothing else.
   The lesson filter itself sits right after the DECK data (tools/add_lesson_links.py). */
(function(){
  var me=document.currentScript, mode=(me&&me.getAttribute('data-mode'))||'teacher', stu=(me&&me.getAttribute('data-student'))||'';
  var D=window.DECK; if(!D||!D.lessons) return;
  var q=new URLSearchParams(location.search), here=location.pathname;
  function el(t,c,x){ var n=document.createElement(t); if(c) n.className=c; if(x!=null) n.textContent=x; return n; }
  var css='#afuqIdx{position:fixed;inset:0;z-index:2147483600;overflow:auto;background:#F4F7FB;color:#1F2D3D;font-family:"Plex","Taj","Segoe UI",Tahoma,sans-serif;direction:rtl;-webkit-overflow-scrolling:touch}'+
    '#afuqIdx .w{max-width:860px;margin:0 auto;padding:18px 16px 60px}#afuqIdx h1{font-size:clamp(19px,4.5vw,26px);margin:6px 0 4px;color:#1D4E89}'+
    '#afuqIdx .s{color:#5B6B7B;font-size:14px;margin:0 0 12px}#afuqIdx h2{font-size:16px;margin:18px 0 8px;color:#2F6FB3;border-bottom:2px solid #DCE6F2;padding-bottom:4px}'+
    '#afuqIdx .r{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;background:#fff;border:1px solid #DCE6F2;border-radius:14px;padding:10px 12px;margin:8px 0;box-shadow:0 1px 3px #1d4e8912}'+
    '#afuqIdx .t{flex:1 1 220px;min-width:0;font-weight:700;font-size:16px;line-height:1.5}#afuqIdx .t i{font-style:normal;color:#7A8A99;font-weight:400;font-size:13px;margin-inline-start:6px}'+
    '#afuqIdx .c{display:inline-block;min-width:34px;text-align:center;background:#EAF1FA;color:#2F6FB3;border-radius:8px;padding:1px 6px;margin-inline-end:6px;font-size:13px}'+
    '#afuqIdx .a{display:flex;gap:6px;flex-wrap:wrap}#afuqIdx .b{font:inherit;font-size:14px;font-weight:700;border-radius:999px;padding:6px 14px;cursor:pointer;text-decoration:none;border:1.5px solid #2F6FB3;color:#2F6FB3;background:#fff;white-space:nowrap}'+
    '#afuqIdx .b.p{background:#2F6FB3;color:#fff}#afuqIdx .b.n{border-color:#1E9E5A;color:#1E9E5A}#afuqIdx .b.ok{background:#1E9E5A;color:#fff;border-color:#1E9E5A}'+
    '#afuqIdx .all{display:inline-block;margin-top:18px;color:#5B6B7B;font-size:14px}#afuqLs{position:fixed;right:12px;bottom:12px;z-index:2147483600;background:#2F6FB3;color:#fff;'+
    'font:700 14px/1 system-ui,Tahoma,sans-serif;padding:10px 14px;border-radius:999px;text-decoration:none;box-shadow:0 4px 14px #0004;direction:rtl}';
  function addCss(){ var s=document.createElement('style'); s.textContent=css; document.head.appendChild(s); }
  function studentUrl(id){ return location.origin+stu+'?l='+encodeURIComponent(id); }
  function copy(t,btn){
    var done=function(){ var o=btn.textContent; btn.textContent='تم النسخ ✓'; btn.classList.add('ok'); setTimeout(function(){ btn.textContent=o; btn.classList.remove('ok'); },1800); };
    var fb=function(){ var a=document.createElement('textarea'); a.value=t; a.setAttribute('readonly',''); a.style.cssText='position:fixed;top:-1000px;opacity:0'; document.body.appendChild(a); a.select();
      var ok=false; try{ ok=document.execCommand('copy'); }catch(e){} document.body.removeChild(a); if(ok) done(); else window.prompt('انسخ الرابط:',t); };
    if(navigator.clipboard&&window.isSecureContext) navigator.clipboard.writeText(t).then(done,fb); else fb();
  }
  function list(){
    addCss();
    var o=el('div'); o.id='afuqIdx'; var w=el('div','w'); o.appendChild(w);
    w.appendChild(el('h1',null,(D.title||'').replace(/^العرض التفاعلي\s*[–-]\s*/,'')||'الدروس'));
    var n=0; D.lessons.forEach(function(L){ n+=(L.slides||[]).length; });
    w.appendChild(el('p','s','اختر الدرس: «دخول» يفتحه لك بملاحظاتك، و«نسخ لمنصة نور» ينسخ رابط هذا الدرس وحده ليقرأه الطالب في البيت.'));
    var unit=null, units={}; (D.units||[]).forEach(function(u){ units[u.id]=u.name; });
    D.lessons.forEach(function(L){
      var un=L.unitName||units[L.unit]||'';
      if(un&&un!==unit){ unit=un; w.appendChild(el('h2',null,un)); }
      var r=el('div','r'), t=el('div','t');
      if(L.code) t.appendChild(el('span','c',L.code));
      t.appendChild(document.createTextNode((L.emo?L.emo+' ':'')+L.title)); t.appendChild(el('i',null,(L.slides||[]).length+' شريحة'));
      var a=el('div','a');
      {
        var go=el('a','b p','دخول'); go.href=here+'?l='+encodeURIComponent(L.id);
        var run=el('a','b','تشغيل'); run.href=studentUrl(L.id); run.target='_blank'; run.rel='noopener'; run.title='كما يراه الطالب';
        var cp=el('button','b n','نسخ لمنصة نور'); cp.type='button';
        cp.onclick=function(){ copy('اقرأ شرح درس «'+L.title+'» بالشرائح في البيت: افتح الرابط وتنقّل بين الشرائح.\n'+studentUrl(L.id),cp); };
        a.appendChild(go); a.appendChild(run); a.appendChild(cp);
      }
      r.appendChild(t); r.appendChild(a); w.appendChild(r);
    });
    { var all=el('a','all','عرض كل الشرائح متتابعة ('+n+' شريحة)'); all.href=here+'?all=1'; w.appendChild(all); }
    ['pointerdown','touchstart','mousedown','click','keydown'].forEach(function(ev){ o.addEventListener(ev,function(e){ e.stopPropagation(); }); });
    document.body.appendChild(o);
  }
  function closed(){   /* a student page opens one lesson only: without a valid ?l it shows no lesson list */
    addCss(); var o=el('div'); o.id='afuqIdx'; var w=el('div','w'); o.appendChild(w);
    w.appendChild(el('h1',null,'📘 شرح الدرس')); w.appendChild(el('p','s','افتح رابط الدرس كما أرسله معلمك في منصة نور.'));
    document.body.appendChild(o);
  }
  function back(){
    addCss();
    var a=el('a',null,'☰ الدروس'); a.id='afuqLs'; a.href=here; a.title='قائمة الدروس';
    ['pointerdown','touchstart','mousedown'].forEach(function(ev){ a.addEventListener(ev,function(e){ e.stopPropagation(); }); });
    document.body.appendChild(a);
  }
  function start(){
    var id=q.get('l'), ok=id&&D.lessons.some(function(L){ return L.id===id; });
    if(ok){ if(mode==='teacher') back(); }
    else if(mode==='student') closed();
    else if(!q.get('all')) list();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start); else start();
})();
