/* Prep pages: «فترة (٤٠ د)» / «فترتان (٣٥ د)». With two shifts a period is 35 minutes: every lesson plan whose step
   times add up to exactly 40 minutes is rescaled to 35 (same proportions, at least one minute a step, ranges such as
   «(10–20 د)» / «من الدقيقة 5 إلى 14» renumbered, totals «المجموع: 40 دقيقة» → 35). Anything that does not add up to 40
   is left as it is, except a single plan in one text whose steps add up to 36–45 minutes (an author's slip), scaled to 35 too. The data is changed before the page draws it, so the copy buttons copy the 35-minute version too.
   Loaded first in <head>; tools/add_shift.py wraps each page's data in AFUQ35(...). The choice is kept per device.
   Subjects with fewer weekly periods in two-shift schools carry a second copy of the data, AFUQ35(<one shift>, <two shifts>),
   with each lesson's periods merged to the bulletin's term total (tools/add_twoshift.py); «فترتان» shows that one. */
(function(G){
  'use strict';
  var KEY='afuq-prep-shift', on=false, two=false;
  try{ on=localStorage.getItem(KEY)==='2'; }catch(e){}
  var T=35, FROM=40;
  var AR='٠١٢٣٤٥٦٧٨٩';
  function toN(x){ return +String(x).replace(/[٠-٩]/g,function(d){ return AR.indexOf(d); }); }
  function like(n,orig){ return /[٠-٩]/.test(orig)?String(n).replace(/\d/g,function(d){ return AR[d]; }):String(n); }
  var D='[0-9٠-٩]+', SP='(?:\\s|&nbsp;|<[^>]{0,40}>)*';
  var RX=new RegExp(
    '(\\('+SP+'('+D+')'+SP+'د'+SP+':'+SP+'من الدقيقة'+SP+'('+D+')'+SP+'إلى'+SP+'('+D+')'+SP+'\\))'+                                  // 1: (4 د: من الدقيقة 0 إلى 4)
    '|((?:من الدقيقة|from minute)'+SP+'('+D+')'+SP+'(?:إلى|حتى|to)'+SP+'('+D+'))'+                                                       // 5: من الدقيقة 5 إلى 14
    '|(('+D+')'+SP+'[–\\-]'+SP+'('+D+')'+SP+'(?:د(?![\\u0600-\\u06FF])|دقيقة|دقائق|min(?:utes?)?\\b))'+                                // 8: (10–20 د)
    '|((?:المجموع|مجموع زمن الحصة|مجموع الزمن|زمن الحصة|الزمن الكلي|Total(?: time)?|Lesson time)'+SP+'[:：]?'+SP+'('+D+')'+SP+'(?:د(?![\\u0600-\\u06FF])|دقيقة|دقائق|minutes?|mins?\\b))'+ // 11: totals
    '|(('+D+')'+SP+'(?:دقيقتان|دقيقتين|دقائق|دقيقة|د(?![\\u0600-\\u06FF])|minutes?|mins?\\b))'+                              // 13: durations
    '|(('+D+')'+SP+'[–\\-]'+SP+'('+D+')'+SP+'('+D+')'+SP+'(?:دقيقتان|دقيقتين|دقائق|دقيقة|د(?![\\u0600-\\u06FF])|minutes?|mins?\\b))', 'gi');                // 15: table cell «30–40<br>10 دقائق»
  function tokens(s){
    var out=[], m; RX.lastIndex=0;
    while((m=RX.exec(s))){
      var t={i:m.index, s:m[0]};
      if(m[1]){ t.k='full'; t.d=toN(m[2]); t.a=toN(m[3]); t.b=toN(m[4]); }
      else if(m[15]){ t.k='range'; t.a=toN(m[16]); t.b=toN(m[17]); t.rd=toN(m[18]); if(t.rd!==t.b-t.a&&t.rd!==t.b-t.a+1){ RX.lastIndex=m.index+1; continue; } }
      else if(m[5]){ t.k='range'; t.a=toN(m[6]); t.b=toN(m[7]); }
      else if(m[8]){ t.k='range'; t.a=toN(m[9]); t.b=toN(m[10]); }
      else if(m[11]){ t.k='total'; t.v=toN(m[12]); }
      else { t.k='dur'; t.d=toN(m[14]); }
      out.push(t);
    }
    /* «(5 دقائق، من الدقيقة 0 إلى 5)» / «(من الدقيقة 0 إلى 5) التهيئة [5 دقائق]»: one step written twice */
    for(var i=0;i+1<out.length;i++){
      var x=out[i], y=out[i+1], r=x.k==='range'?x:y, u=x.k==='dur'?x:y;
      if(r===u||r.k!=='range'||u.k!=='dur') continue;
      var gap=s.slice(x.i+x.s.length,y.i);
      if(gap.length>40||/\n/.test(gap)||(u.d!==r.b-r.a&&u.d!==r.b-r.a+1)) continue;
      out.splice(i,2,{i:r.i, s:r.s, k:'range', a:r.a, b:r.b, du:u});
    }
    return out;
  }
  /* split the tokens into lesson plans that add up to exactly 40 minutes */
  function groups(tk){
    tk=tk.map(function(t){ var c={}; for(var k in t) c[k]=t[k]; return c; });   /* marks its own copies */
    var gs=[], cur=null, cum=0, incl=null;
    function reset(){ cur=null; cum=0; incl=null; }
    for(var i=0;i<tk.length;i++){
      var t=tk[i], d;
      if(t.k==='total'){
        if(t.v!==FROM){ reset(); continue; }
        if(cur&&cum===FROM){ cur.push(t); gs.push(cur); reset(); }
        else if(!cur||cum===0){ cur=[t]; cum=0; }
        else reset();
        continue;
      }
      if(t.k==='range'){
        if(cum>0){ var expect=incl?cum+1:cum; if(t.a!==expect){ reset(); } }
        if(cum===0){ if(t.a!==0&&t.a!==1){ reset(); continue; } incl=(t.a===1); }
        d=t.b-t.a+(incl?1:0);
      } else if(t.k==='full'){
        if(t.a!==cum){ reset(); if(t.a!==0) continue; }
        d=t.d; if(t.b!==t.a+d){ reset(); continue; }
      } else d=t.d;
      if(!(d>0)){ reset(); continue; }
      if(!cur) cur=[];
      t.dd=d; cur.push(t); cum+=d;
      if(cum>FROM){ reset(); continue; }
      if(cum===FROM){
        var nx=tk[i+1];
        if(nx&&(nx.k==='total'||nx.k==='dur')&&(nx.v===FROM||nx.d===FROM)){ nx.k='total'; nx.v=FROM; cur.push(nx); i++; }   /* the sum row «40 د» */
        gs.push(cur); reset();
      }
    }
    return gs;
  }
  function scale(ds){
    var tot=0; ds.forEach(function(x){ tot+=x; });
    var raw=ds.map(function(x){ return x*T/tot; }), r=raw.map(function(x){ return Math.max(1,Math.floor(x)); }), left=T;
    r.forEach(function(x){ left-=x; });
    var ord=raw.map(function(x,i){ return [x-Math.floor(x),i]; }).sort(function(a,b){ return b[0]-a[0]; });
    for(var k=0;left>0;k++){ r[ord[k%ord.length][1]]++; left--; }
    while(left<0){ var j=r.indexOf(Math.max.apply(null,r)); r[j]--; left++; }
    return r;
  }
  function rewrite(t,orig,vals){   /* replace the numbers of one token, in order */
    var k=0; return orig.replace(/<[^>]*>|[0-9٠-٩]+/g,function(n){ return n.charAt(0)==='<'||k>=vals.length?n:like(vals[k++],n); })   /* not colspan="2" */
      .replace(/([0-9٠-٩]+)((?:\s|&nbsp;|<[^>]{0,40}>)*)(دقائق|دقيقة)(?![\u0600-\u06FF])/g,function(m,n,sp,u){   /* 3–10 دقائق, 11+ دقيقة */
        var v=toN(n); return n+sp+(v>=3&&v<=10?'دقائق':v>10?'دقيقة':u); });
  }
  function fixText(s){
    if(typeof s!=='string'||s.length<8||!/[0-9٠-٩]/.test(s)) return s;
    var tk=tokens(s); if(!tk.length) return s;
    /* a time mentioned inside a step («يسجّل القراءات لمدة 10 دقائق») breaks the running sum: also try without plain
       durations (the plan is written with ranges) and without durations deep in a line (the plan's times head the lines) */
    var gs=groups(tk), rep=[];
    [function(t){ return t.k!=='dur'; },
     function(t){ return t.k!=='dur'||t.i-s.lastIndexOf('\n',t.i)<=45; }].forEach(function(f){
      var sub=tk.filter(f); if(sub.length===tk.length) return;
      var g2=groups(sub);
      if(g2.length>gs.length) gs=g2;
    });
    gs.forEach(function(g){
      var steps=g.filter(function(t){ return t.k!=='total'; }); if(steps.length<2) return;
      var r=scale(steps.map(function(t){ return t.dd; })), cum=0, incl=steps[0].k==='range'&&steps[0].a===1;
      var j=0;
      g.forEach(function(t){
        if(t.k==='total'){ rep.push([t.i,t.s,rewrite(t,t.s,[T])]); return; }
        var d=r[j++], a=cum+(incl?1:0), b=cum+d;
        if(t.k==='full') rep.push([t.i,t.s,rewrite(t,t.s,[d,cum,cum+d])]);
        else if(t.k==='range'){ rep.push([t.i,t.s,rewrite(t,t.s,t.rd?[a,b,d]:[a,b])]); if(t.du) rep.push([t.du.i,t.du.s,rewrite(t.du,t.du.s,[d])]); }
        else rep.push([t.i,t.s,rewrite(t,t.s,[d])]);
        cum+=d;
      });
    });
    if(!gs.length){
      var st=tk.filter(function(t){ return t.k==='dur'; }), sum=0; st.forEach(function(t){ sum+=t.d; });
      /* a lone «زمن الحصة: 40 دقيقة» in a string with no step times */
      if(!st.length&&tk.every(function(t){ return t.k==='total'; })) tk.forEach(function(t){ if(t.v===FROM) rep.push([t.i,t.s,rewrite(t,t.s,[T])]); });
      /* one plan per string whose steps add up to a little more or less than 40 (e.g. 5+12+10+10+5): still a whole period */
      else if(st.length>=3&&sum>=36&&sum<=45&&tk.every(function(t){ return t.k==='dur'||(t.k==='total'&&(t.v===sum||t.v===FROM)); })){
        var r2=scale(st.map(function(t){ return t.d; }));
        tk.forEach(function(t){ rep.push([t.i,t.s,rewrite(t,t.s,[t.k==='total'?T:r2[st.indexOf(t)]])]); });
      }
    }
    if(!rep.length) return s;
    rep.sort(function(a,b){ return b[0]-a[0]; });
    rep.forEach(function(x){ s=s.slice(0,x[0])+x[2]+s.slice(x[0]+x[1].length); });
    return s;
  }
  var MINK=/^(min|mins|minutes|dur|duration|time)$/;
  function walk(o){
    if(typeof o==='string') return fixText(o);
    if(Array.isArray(o)){
      /* [{min:5,…},{min:10,…},…] adding up to 40 */
      if(o.length>1&&o.every(function(x){ return x&&typeof x==='object'&&!Array.isArray(x); })){
        var key=null; Object.keys(o[0]).forEach(function(k){ if(MINK.test(k)&&typeof o[0][k]==='number') key=k; });
        if(key&&o.every(function(x){ return typeof x[key]==='number'; })){
          var sum=0; o.forEach(function(x){ sum+=x[key]; });
          if(sum===FROM){ var r=scale(o.map(function(x){ return x[key]; })); o=o.map(function(x,i){ var y={}; for(var k in x) y[k]=x[k]; y[key]=r[i]; return y; }); }
        }
      }
      return o.map(walk);
    }
    if(o&&typeof o==='object'){ var n={}; for(var k in o) n[k]=walk(o[k]); return n; }
    return o;
  }
  /* o2: the page's two-shift data (fewer periods per lesson, from the bulletin — tools/add_twoshift.py), when it has one */
  function AFUQ35(o,o2){ if(o2!==undefined) two=true; return on?walk(o2!==undefined?o2:o):o; }
  AFUQ35.text=fixText; AFUQ35.walk=walk; AFUQ35.tokens=tokens;
  /* a <script type="application/json"> block: rewrite its text before the page reads it */
  AFUQ35.el=function(el,o2){ if(o2!==undefined) two=true; if(!on||!el) return; try{ el.textContent=JSON.stringify(walk(o2!==undefined?o2:JSON.parse(el.textContent))).replace(/<\//g,'<\\/'); }catch(e){} };
  G.AFUQ35=AFUQ35;
  if(typeof document==='undefined') return;
  function ui(){
    if(document.getElementById('afuqShift')) return;
    /* a small bar at the very top of the page (in the flow, so it covers nothing) */
    var w=document.createElement('div'); w.id='afuqShiftBar';
    var b=document.createElement('div'); b.id='afuqShift'; b.setAttribute('role','group'); b.setAttribute('aria-label','مدة الحصة'); w.appendChild(b);
    b.innerHTML='<button type="button" data-v="1">فترة (٤٠ د)</button><button type="button" data-v="2">فترتان (٣٥ د)</button>';
    var st=document.createElement('style');
    st.textContent='#afuqShiftBar{display:flex;flex-wrap:wrap;justify-content:flex-start;direction:rtl;padding:6px 8px 0;max-width:100%;box-sizing:border-box}'+
      '#afuqShift{display:inline-flex;gap:2px;background:#fff;border:1px solid #CFD9E2;border-radius:999px;padding:2px;box-shadow:0 1px 4px #0001;font:12px/1.3 system-ui,Tahoma,sans-serif}'+
      '#afuqShift button{font:inherit;border:0;background:transparent;color:#5B6B7B;padding:4px 10px;border-radius:999px;cursor:pointer}'+
      '#afuqShift button.on{background:#2E6F73;color:#fff;font-weight:700}@media print{#afuqShiftBar{display:none}}';
    if(two){ var n=document.createElement('span'); n.id='afuqShiftNote'; n.textContent=on?'عدد الحصص حسب نشرة الفترتين 2026/2027':'عدد الحصص يقل في «فترتان» حسب النشرة'; w.appendChild(n); }
    st.textContent+='#afuqShiftNote{align-self:center;margin-inline-start:8px;font:11px/1.3 system-ui,Tahoma,sans-serif;color:#5B6B7B}';
    document.head.appendChild(st);
    Array.prototype.forEach.call(b.querySelectorAll('button'),function(x){
      if((x.getAttribute('data-v')==='2')===on) x.className='on';
      x.onclick=function(){ var v=x.getAttribute('data-v'); if((v==='2')===on) return; try{ localStorage.setItem(KEY,v); }catch(e){} location.reload(); };
    });
    document.body.insertBefore(w,document.body.firstChild);
  }
  /* the page's own heading text, e.g. «زمن الحصة 40 دقيقة» / «٤٠ دقيقة للحصة» under the title */
  function heads(){
    if(!on) return;
    var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,null), n, re=/(زمن الحصة\s*[:：]?\s*)(40|٤٠)(\s*دقيقة)|()(40|٤٠)(\s*دقيقة للحصة)/g;
    while((n=w.nextNode())) if(re.test(n.nodeValue)){ re.lastIndex=0; n.nodeValue=n.nodeValue.replace(re,function(m,a,x,c,a2,x2,c2){ return x?a+like(T,x)+c:like(T,x2)+c2; }); }
  }
  function start(){ ui(); heads(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start); else start();
})(typeof window!=='undefined'?window:globalThis);
