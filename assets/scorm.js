/* SCORM 1.2 packages for منصة نور, built in the teacher's browser (written by tools/build_scorm.py — edit it there).
   A «.scorm-dl» button (data-g, data-s, data-l) builds the zip of that lesson from files already on the site — the lesson page
   data (/afuq/q/<g>/<s>/), the quiz engine and the certificate font — so the site stores no zips. */
(function(){
'use strict';
var WRAP="(function(){\n/* SCORM 1.2 wrapper (tools/build_scorm.py): finds the LMS API, reports progress from the lesson engine's afuq-q events */\nvar C=window.SCORM_CFG||{},A=null,on=false,done=false,t0=Date.now();\nfunction find(w){for(var n=0;w&&n<15;n++){try{if(w.API)return w.API;}catch(e){} if(w.parent&&w.parent!==w)w=w.parent;else break;}return null;}\nA=find(window);if(!A&&window.opener)A=find(window.opener);\nfunction get(k){try{return String(A.LMSGetValue(k)||'');}catch(e){return '';}}\nfunction set(k,v){try{A.LMSSetValue(k,String(v));}catch(e){}}\nfunction commit(){try{A.LMSCommit('');}catch(e){}}\nif(A){try{var r=A.LMSInitialize('');on=(r===true||r==='true');}catch(e){}}\nif(!on) return;\nvar st=get('cmi.core.lesson_status');done=(st==='completed'||st==='passed');\nif(!st||st==='not attempted') set('cmi.core.lesson_status','incomplete');\nset('cmi.core.score.min',0);set('cmi.core.score.max',100);\ntry{ /* progress from an earlier session (another device) */\n  var sd=get('cmi.suspend_data');if(sd&&!localStorage.getItem(C.key))localStorage.setItem(C.key,sd);\n  if(!localStorage.getItem('afuq-q-name')){var nm=get('cmi.core.student_name').trim();\n    if(nm.indexOf(',')>0){var p=nm.split(',');nm=(p[1]+' '+p[0]).trim();}\n    if(nm)localStorage.setItem('afuq-q-name',nm);}\n}catch(e){}\ncommit();\nwindow.addEventListener('afuq-q',function(ev){var d=ev.detail||{};\n  if(d.st){set('cmi.suspend_data',JSON.stringify(d.st).slice(0,4000));\n    set('cmi.core.score.raw',Math.round((d.total||0)*100/(d.max||40)));}\n  if(d.done&&!done){done=true;set('cmi.core.lesson_status','completed');}\n  commit();});\nfunction fin(){if(!on)return;var s=Math.round((Date.now()-t0)/1000),h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;\n  function p(n,w){n=String(n);while(n.length<w)n='0'+n;return n;}\n  set('cmi.core.session_time',p(h,4)+':'+p(m,2)+':'+p(x,2));set('cmi.core.exit',done?'':'suspend');commit();\n  try{A.LMSFinish('');}catch(e){}on=false;}\nwindow.addEventListener('pagehide',fin);window.addEventListener('beforeunload',fin);\n})();", MAN="<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<manifest identifier=\"afuq-%(id)s\" version=\"1.0\"\n  xmlns=\"http://www.imsproject.org/xsd/imscp_rootv1p1p2\"\n  xmlns:adlcp=\"http://www.adlnet.org/xsd/adlcp_rootv1p2\"\n  xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n  xsi:schemaLocation=\"http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd http://www.imsglobal.org/xsd/imsmd_rootv1p2p1 imsmd_rootv1p2p1.xsd http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd\">\n  <metadata><schema>ADL SCORM</schema><schemaversion>1.2</schemaversion></metadata>\n  <organizations default=\"org\">\n    <organization identifier=\"org\">\n      <title>%(title)s</title>\n      <item identifier=\"item1\" identifierref=\"res1\" isvisible=\"true\">\n        <title>%(title)s</title>\n        <adlcp:masteryscore>50</adlcp:masteryscore>\n      </item>\n    </organization>\n  </organizations>\n  <resources>\n    <resource identifier=\"res1\" type=\"webcontent\" adlcp:scormtype=\"sco\" href=\"index.html\">\n%(files)s\n    </resource>\n  </resources>\n</manifest>\n";
var CRC=(function(){var t=[];for(var n=0;n<256;n++){var c=n;for(var k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
function crc32(b){var c=0xFFFFFFFF;for(var i=0;i<b.length;i++)c=CRC[(c^b[i])&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0;}
function zip(files){ /* [[name, Uint8Array]] → Blob (stored, no compression) */
  var enc=new TextEncoder(),parts=[],cen=[],off=0,D=((2026-1980)<<9)|(1<<5)|1;
  files.forEach(function(f){var nm=enc.encode(f[0]),d=f[1],c=crc32(d),h=new DataView(new ArrayBuffer(30));
    h.setUint32(0,0x04034b50,true);h.setUint16(4,20,true);h.setUint16(10,0,true);h.setUint16(12,D,true);
    h.setUint32(14,c,true);h.setUint32(18,d.length,true);h.setUint32(22,d.length,true);h.setUint16(26,nm.length,true);
    parts.push(new Uint8Array(h.buffer),nm,d);
    var e=new DataView(new ArrayBuffer(46));e.setUint32(0,0x02014b50,true);e.setUint16(4,20,true);e.setUint16(6,20,true);
    e.setUint16(14,D,true);e.setUint32(16,c,true);e.setUint32(20,d.length,true);e.setUint32(24,d.length,true);
    e.setUint16(28,nm.length,true);e.setUint32(38,0o644<<16,true);e.setUint32(42,off,true);cen.push(new Uint8Array(e.buffer),nm);
    off+=30+nm.length+d.length;});
  var cs=cen.reduce(function(a,x){return a+x.length;},0),z=new DataView(new ArrayBuffer(22));
  z.setUint32(0,0x06054b50,true);z.setUint16(8,files.length,true);z.setUint16(10,files.length,true);z.setUint32(12,cs,true);z.setUint32(16,off,true);
  return new Blob(parts.concat(cen,[new Uint8Array(z.buffer)]),{type:'application/zip'});}
function esc(x){return String(x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function js(o){return JSON.stringify(o).replace(/<\//g,'<\\/');}
function txt(u){return fetch(u,{cache:'no-cache'}).then(function(r){if(!r.ok)throw new Error(u);return r.text();});}
function bin(u){return fetch(u).then(function(r){if(!r.ok)throw new Error(u);return r.arrayBuffer();}).then(function(b){return new Uint8Array(b);});}
var cache={};
function build(g,s,l){
  var page=cache[g+'/'+s]||(cache[g+'/'+s]=txt('/afuq/q/'+g+'/'+s+'/'));
  return Promise.all([page,txt('/afuq/q/engine.js'),txt('/afuq/q/engine.css')]).then(function(r){
    var h=r[0],i=h.indexOf('window.QZ=')+10,d=JSON.parse(h.slice(i,h.indexOf(';</script>',i)));
    var L=d.L[l-1],fonts=[],css=r[2].replace(/url\(\/assets\/f\/([0-9a-f]+\.(?:ttf|woff2?|otf))\)/g,function(m,f){if(fonts.indexOf(f)<0)fonts.push(f);return 'url(fonts/'+f+')';});
    var title='ألعاب ونشاط الدرس – '+d.sn+' – الصف '+d.gn+' – '+L.t, dd=Object.assign({},d,{l:l});
    var doc='<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<title>'+esc(title)+
      '</title>\n<style>'+css+'</style></head><body><div id="app"></div>\n<script>window.SCORM_CFG='+js({key:'afuq-q:'+d.g+'/'+d.s+'/'+l})+';</script>\n<script>'+WRAP+
      '</script>\n<script>window.QZ='+js(dd)+';</script>\n<script>'+r[1].replace(/<\//g,'<\\/')+'</script></body></html>\n';
    return Promise.all(fonts.map(function(f){return bin('/assets/f/'+f);})).then(function(fb){
      var enc=new TextEncoder(),files=[['index.html',enc.encode(doc)]];fonts.forEach(function(f,k){files.push(['fonts/'+f,fb[k]]);});
      var names=files.map(function(f){return f[0];}).sort();
      var man=MAN.replace('%(id)s',g+'-'+s+'-L'+(l<10?'0':'')+l).split('%(title)s').join(esc(title))
        .replace('%(files)s',names.map(function(n){return '      <file href="'+n+'"/>';}).join('\n'));
      return zip([['imsmanifest.xml',enc.encode(man)]].concat(files.sort(function(a,b){return a[0]<b[0]?-1:1;})));});});}
document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('.scorm-dl');if(!b||b.disabled)return;e.preventDefault();
  var lab=b.innerHTML,g=b.dataset.g,s=b.dataset.s,l=+b.dataset.l;b.disabled=true;b.textContent='⏳ جارٍ التجهيز…';
  build(g,s,l).then(function(blob){var a=document.createElement('a'),u=URL.createObjectURL(blob);a.href=u;
    a.download='Afuq-'+s.toUpperCase()+'-G'+g+'-L'+(l<10?'0':'')+l+'.zip';document.body.appendChild(a);a.click();a.remove();
    setTimeout(function(){URL.revokeObjectURL(u);},4000);b.innerHTML='✔ تم التنزيل';setTimeout(function(){b.innerHTML=lab;b.disabled=false;},2500);})
  .catch(function(){b.innerHTML='⚠️ تعذّر التجهيز، حاول مرة أخرى';setTimeout(function(){b.innerHTML=lab;b.disabled=false;},3000);});});
window.afuqScorm=build;
})();
