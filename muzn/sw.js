const C='muzn-field1-183e035aee';
const CORE=['./','index.html','manifest.webmanifest','icons/icon-192.png','icons/icon-512.png','icons/apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(CORE.map(u=>new Request(u,{cache:'reload'})))).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const r=e.request; if(r.method!=='GET') return;
  const u=new URL(r.url);
  // the page itself: network first (so updates arrive on the next open), saved copy when offline
  if(r.mode==='navigate' || (u.origin===location.origin && /\/(index\.html)?$/.test(u.pathname))){
    e.respondWith(fetch(r,{cache:'no-cache'}).then(res=>{ if(res&&res.ok){ const cp=res.clone(); caches.open(C).then(c=>c.put('./',cp)); } return res; })
      .catch(()=>caches.match(r,{ignoreSearch:true}).then(h=>h||caches.match('./'))));
    return;
  }
  // everything else: saved copy first, refreshed in the background
  e.respondWith(caches.match(r).then(hit=>{
    const net=fetch(r).then(res=>{ if(res && (res.ok||res.type==='opaque')){ const cp=res.clone(); caches.open(C).then(c=>c.put(r,cp)); } return res; }).catch(()=>hit);
    return hit||net;
  }));
});
