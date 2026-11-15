/* «العمل بدون إنترنت» (owner, 2026-11-15): a teacher opens a deck (عرض تفاعلي / عروض باور بوينت) once with internet and it is kept in this
   browser, so it opens again without internet. Registered from /assets/offline.js (decks and /p/). No file is made: the copy lives in the
   browser's Cache Storage, on the subscriber's own device.
   Kept: the pages /, /p/, /<grade>/<subject>/ (portal) and /<grade>/<subject>/(slides|interactive)/, and the same-origin /assets/ files they use.
   Network first (always the newest copy when online); when the network does not answer within 3.5 s, or there is none, the saved copy opens.
   Everything else (other sections, /afuq/, apps, the admin tool, other origins) is left alone. Bump CACHE when this file's rules change. */
const CACHE = 'afuq-offline-v1';
const PAGE = /^\/(?:(?:\d+\/[a-z]+\/(?:(?:slides|interactive)\/)?)|(?:p\/))?$/;
const DECK = /^\/(\d+)\/([a-z]+)\/(?:slides|interactive)\/$/;
const SUBJ = {math:'الرياضيات',advmath:'الرياضيات المتقدمة',basicmath:'الرياضيات الأساسية',english:'اللغة الإنجليزية',arabic:'اللغة العربية',science:'العلوم',physics:'الفيزياء',chemistry:'الكيمياء',biology:'الأحياء',islamic:'التربية الإسلامية',social:'الدراسات الاجتماعية',arts:'الفنون',homeland:'هذا وطني',envsci:'العلوم البيئية',it:'تقنية المعلومات',pe:'التربية البدنية',sport:'الرياضة المدرسية',geography:'الجغرافيا الاقتصادية'};
const MAX = 150;

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(k => Promise.all(k.filter(x => x.startsWith('afuq-offline-') && x !== CACHE).map(x => caches.delete(x)))).then(() => self.clients.claim())));

function kind(req) {
  if (req.method !== 'GET') return null;
  const u = new URL(req.url);
  if (u.origin !== location.origin) return null;
  if (req.mode === 'navigate' && PAGE.test(u.pathname)) return 'page';
  if (/^\/assets\//.test(u.pathname) && /^(font|image|script|style)$/.test(req.destination)) return 'asset';
  return null;
}
const keyOf = (url, k) => { const u = new URL(url); return k === 'page' ? u.origin + u.pathname : u.href; };

async function trim(cache) {
  const ks = await cache.keys();
  for (let i = 0; i < ks.length - MAX; i++) await cache.delete(ks[i]);
}

async function netFirst(req, k) {
  const cache = await caches.open(CACHE), key = keyOf(req.url, k), hit = await cache.match(key);
  const net = fetch(req).then(res => {
    if (res && res.ok && res.type === 'basic') cache.put(key, res.clone()).then(() => trim(cache)).catch(() => {});
    return res;
  });
  if (!hit) return net.catch(() => offline(k));
  return Promise.race([net.catch(() => hit), new Promise(r => setTimeout(() => r(hit), 3500))]);
}

async function offline(k) {
  if (k !== 'page') return Response.error();
  const cache = await caches.open(CACHE), saved = [];
  for (const r of await cache.keys()) { const m = DECK.exec(new URL(r.url).pathname); if (m) saved.push([m[1], m[2], new URL(r.url).pathname]); }
  const li = saved.map(([g, s, p]) => '<li><a href="' + p + '">' + (SUBJ[s] || s) + ' – الصف ' + g + (/interactive/.test(p) ? ' (العرض التفاعلي)' : ' (العروض)') + '</a></li>').join('');
  return new Response('<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>بدون اتصال</title>' +
    '<style>body{margin:0;font-family:Tahoma,system-ui,sans-serif;background:#F3F6FB;color:#16213A;line-height:1.8;padding:24px 16px}main{max-width:560px;margin:0 auto;background:#fff;border:1px solid #DCE3EE;border-radius:18px;padding:20px}' +
    'h1{font-size:20px;margin:0 0 8px}a{color:#2F6FB3;font-weight:700}li{margin:6px 0}</style></head><body><main><h1>لا يوجد اتصال بالإنترنت</h1>' +
    '<p>هذه الصفحة لم تُحفظ على جهازك بعد. افتحها مرة واحدة والإنترنت متصل، ثم تعمل بدونه.</p>' +
    (li ? '<p><b>العروض المحفوظة على جهازك:</b></p><ul>' + li + '</ul>' : '<p>لا توجد عروض محفوظة بعد.</p>') + '</main></body></html>',
    { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}

self.addEventListener('fetch', e => { const k = kind(e.request); if (k) e.respondWith(netFirst(e.request, k)); });

/* the page asks to keep itself and the /assets/ files it already loaded (its first visit was not under this worker yet) */
self.addEventListener('message', e => {
  const d = e.data; if (!d || d.type !== 'save' || !Array.isArray(d.urls)) return;
  e.waitUntil((async () => {
    const cache = await caches.open(CACHE); let n = 0;
    for (const raw of d.urls.slice(0, 40)) {
      try {
        const u = new URL(raw, location.origin); if (u.origin !== location.origin) continue;
        const k = PAGE.test(u.pathname) ? 'page' : (/^\/assets\//.test(u.pathname) ? 'asset' : null); if (!k) continue;
        const res = await fetch(k === 'page' ? u.origin + u.pathname : u.href, { cache: 'no-cache' });
        if (res.ok && res.type === 'basic') { await cache.put(keyOf(u.href, k), res); n++; }
      } catch (err) {}
    }
    await trim(cache);
    if (e.source) e.source.postMessage({ type: 'saved', n });
  })());
});
