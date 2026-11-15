/* «العمل بدون إنترنت» (owner, 2026-11-15): registers /sw-offline.js (see it for the rules) and makes sure this page and the /assets/ files it uses are kept
   in the browser. On a deck (عرض تفاعلي / عروض باور بوينت) the first time it is kept, a small notice says so.
   Usage: <script src="/assets/offline.js" defer></script> in the decks and /p/ (tools/add_offline.py). Nothing here changes how the page works. */
(function () {
  'use strict';
  if (!('serviceWorker' in navigator) || !/^https?:$/.test(location.protocol) || !window.caches) return;
  var CN = 'afuq-offline-v1', path = location.pathname, isDeck = /^\/\d+\/[a-z]+\/(?:slides|interactive)\/$/.test(path), flag = 'afuq-off:' + path, flagged = false;
  try { flagged = localStorage.getItem(flag) === '1'; } catch (e) {}
  function done() {
    if (flagged) return; flagged = true; try { localStorage.setItem(flag, '1'); } catch (e) {}
    if (!isDeck) return;
    var t = document.createElement('div'); t.textContent = '✅ هذا العرض محفوظ على جهازك، ويعمل بدون إنترنت';
    t.setAttribute('role', 'status');
    t.style.cssText = 'position:fixed;left:50%;bottom:14px;transform:translateX(-50%);z-index:2147483000;background:#1F7A4D;color:#fff;font:700 14px/1.5 Tahoma,system-ui,sans-serif;padding:9px 16px;border-radius:999px;box-shadow:0 6px 20px #0004;direction:rtl;pointer-events:none;max-width:92vw;text-align:center;opacity:0;transition:opacity .3s';
    document.body.appendChild(t); setTimeout(function () { t.style.opacity = '1'; }, 30);
    setTimeout(function () { t.style.opacity = '0'; setTimeout(function () { t.remove(); }, 400); }, 6000);
  }
  function urls() {
    var u = [location.origin + path];
    try { performance.getEntriesByType('resource').forEach(function (e) { try { var x = new URL(e.name); if (x.origin === location.origin && /^\/assets\//.test(x.pathname)) u.push(x.href); } catch (_) {} }); } catch (_) {}
    return u.filter(function (x, i) { return u.indexOf(x) === i; });
  }
  function check(reg) {
    caches.open(CN).then(function (c) { return c.match(location.origin + path); }).then(function (hit) {
      if (hit) return done();
      var sw = reg.active || navigator.serviceWorker.controller; if (!sw) return;
      navigator.serviceWorker.addEventListener('message', function (e) { if (e.data && e.data.type === 'saved') done(); });
      sw.postMessage({ type: 'save', urls: urls() });
    }).catch(function () {});
  }
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/sw-offline.js', { scope: '/' }).then(function () { return navigator.serviceWorker.ready; })
      .then(function (reg) { setTimeout(function () { check(reg); }, 1500); }).catch(function () {});
  });
})();
