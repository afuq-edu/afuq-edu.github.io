/* Kahoot question-type chooser: objective (اختياري) / written (مقالي) / mixed (مزج).
   Loaded before a game's own scripts. data-e lists the type codes of written questions in that file,
   data-o the objective ones. window.__afuqQF(data) is wrapped around the game's question literals and
   JSON.parse is patched so JSON data blocks pass through it too; it drops questions of the other type
   according to ?qt=o|e in the URL (no parameter = mixed). A chooser appears before the game starts. */
(function(){
  var s=document.currentScript, E={}, O={};
  (s.getAttribute('data-e')||'').split(',').forEach(function(c){ if(c) E[c]=1; });
  (s.getAttribute('data-o')||'').split(',').forEach(function(c){ if(c) O[c]=1; });
  var m=/[?&]qt=([oem])\b/.exec(location.search), mode=m?m[1]:'';
  var TK=['t','y','k','type','kind'], counts={o:0,e:0};
  function isCode(v){ return typeof v==='string' && v.length<=6 && (E[v]||O[v]); }
  function hasText(a){ for(var i=0;i<a.length;i++) if(typeof a[i]==='string' && a[i].length>6) return true; return false; }
  function codeOf(x){
    if(Array.isArray(x)){ if(x.length<3 || !hasText(x)) return null; for(var i=0;i<3;i++) if(isCode(x[i])) return x[i]; return null; }
    if(x && typeof x==='object'){ var vals=[]; for(var key in x) vals.push(x[key]); if(!hasText(vals)) return null; for(var j=0;j<TK.length;j++) if(isCode(x[TK[j]])) return x[TK[j]]; }
    return null;
  }
  function walk(v,c,d){
    if(d>10 || !v || typeof v!=='object') return v;
    if(Array.isArray(v)){
      var hit=false, out=[];
      for(var i=0;i<v.length;i++){
        var code=codeOf(v[i]);
        if(code){ hit=true; var t=E[code]?'e':'o'; c[t]++; if(mode==='o'&&t!=='o' || mode==='e'&&t!=='e') continue; out.push(v[i]); }
        else out.push(walk(v[i],c,d+1));
      }
      if(!hit){ for(var k=0;k<v.length;k++) v[k]=out[k]; return v; }
      return out;
    }
    for(var key in v) if(Object.prototype.hasOwnProperty.call(v,key)) v[key]=walk(v[key],c,d+1);
    return v;
  }
  window.__afuqQF=function(data){
    var c={o:0,e:0}, r=walk(data,c,0);
    if(c.o+c.e>counts.o+counts.e){ counts=c; window.__afuqQC=c; }
    return r;
  };
  var P=JSON.parse;
  JSON.parse=function(){ var r=P.apply(this,arguments); return (r && typeof r==='object') ? window.__afuqQF(r) : r; };

  var LABEL={o:'اختياري',e:'مقالي',m:'مزج'};
  function go(q){ var u=new URL(location.href); if(q==='m') u.searchParams.delete('qt'); else u.searchParams.set('qt',q); location.replace(u.href); }
  var CSS='#afuqQt{position:fixed;inset:0;z-index:2147483646;background:#0b1220cc;display:grid;place-items:center;padding:16px;font-family:system-ui,"Segoe UI",Tahoma,"Noto Sans Arabic",Arial,sans-serif;direction:rtl}'+
    '#afuqQt .bx{background:#fff;color:#16213A;border-radius:18px;padding:22px;width:min(440px,100%);box-shadow:0 20px 60px #0007}'+
    '#afuqQt h2{margin:0 0 4px;font-size:22px}#afuqQt p{margin:0 0 14px;color:#5B6782;font-size:15px}'+
    '#afuqQt button{display:block;width:100%;text-align:start;margin:0 0 10px;padding:12px 16px;border-radius:14px;border:2px solid #DCE3EE;background:#F3F6FB;color:#16213A;font:inherit;cursor:pointer}'+
    '#afuqQt button b{display:block;font-size:19px}#afuqQt button small{color:#5B6782;font-size:14px}'+
    '#afuqQt button:hover:not(:disabled){border-color:#2F6FB3}#afuqQt button.cur{border-color:#2F6FB3;background:#E7F0FA}#afuqQt button:disabled{opacity:.5;cursor:not-allowed}'+
    '#afuqQtChip{position:fixed;bottom:10px;left:10px;z-index:2147483645;background:#16213Aee;color:#fff;border:0;border-radius:999px;padding:7px 12px;font:600 13px/1.2 system-ui,Tahoma,"Noto Sans Arabic",sans-serif;cursor:pointer;direction:rtl;opacity:.85}';
  function chooser(){
    if(document.getElementById('afuqQt')) return;
    var cur=mode||'m', w=document.createElement('div'); w.id='afuqQt';
    var bx=document.createElement('div'); bx.className='bx'; w.appendChild(bx);
    bx.innerHTML='<h2>نوع الأسئلة</h2><p>اختر نوع أسئلة المسابقة قبل البدء.</p>';
    [['o','اختياري','اختيار من متعدد، وصواب وخطأ، وغيرها',counts.o],['e','مقالي','يكتب الطلاب الإجابة بأنفسهم',counts.e],['m','مزج','جميع الأنواع معًا',counts.o+counts.e]].forEach(function(x){
      var b=document.createElement('button'); b.type='button'; if(x[0]===cur) b.className='cur';
      var t=document.createElement('b'); t.textContent=x[1]; var sm=document.createElement('small'); sm.textContent=x[2]+' — '+x[3]+' سؤال';
      b.appendChild(t); b.appendChild(sm); if(!x[3]) b.disabled=true;
      b.addEventListener('click',function(){ if(x[0]===cur){ w.remove(); chip(); } else go(x[0]); });
      bx.appendChild(b);
    });
    document.body.appendChild(w);
  }
  function chip(){
    if(document.getElementById('afuqQtChip')) return;
    var c=document.createElement('button'); c.id='afuqQtChip'; c.type='button'; c.textContent='الأسئلة: '+LABEL[mode||'m']+' — تغيير';
    c.addEventListener('click',chooser); document.body.appendChild(c);
  }
  function init(){
    var st=document.createElement('style'); st.textContent=CSS; document.head.appendChild(st);
    if(!counts.e || !counts.o) return;
    if(mode) chip(); else chooser();
  }
  function later(){ setTimeout(init,0); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',later); else later();
})();
