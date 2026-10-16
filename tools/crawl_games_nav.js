#!/usr/bin/env node
/* Map the navigation of the ready-made game collections (explorer / numbers apps) so every lesson and activity
   can get its own permanent link.  For each collection it replays clicks from a fresh page and records, per level,
   the visible items' titles.  The result goes to tools/games_nav.json (read by tools/add_games.py).
   Config (hand-written): tools/games_nav_levels.json  { "<g>_<subject>_<section>": { "levels": ["css", ...], "pre": [{"sel":"css","idx":0}] } }
   A level selector must match, among the *visible* elements of that screen, exactly the clickable items of that level.
   Usage: node tools/crawl_games_nav.js [OPEN_COPIES_DIR=/path/with/<key>/index.html] [key ...]
   Needs playwright (npm i playwright / chromium).  Open copies are served by `python3 -m http.server` on :8765 under /_x/ . */
const fs = require('fs'), path = require('path');
const {chromium} = require(process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright');
const ROOT = path.resolve(__dirname, '..'), BASE = process.env.BASE || 'http://127.0.0.1:8765/_x/';
const CFG = JSON.parse(fs.readFileSync(process.env.CFG || path.join(ROOT, 'tools/games_nav_levels.json'), 'utf8'));
const OUT = process.env.OUT || path.join(ROOT, 'tools/games_nav.json');   // CFG / OUT can point elsewhere (parallel runs)
const only = process.argv.slice(2);
const clean = s => s.replace(/\s+/g, ' ').replace(/[☆★⭐]+/g, '').replace(/[0-9٠-٩]+\s*\/\s*[0-9٠-٩]+/g, '').replace(/[0-9٠-٩]+\s*%/g, '')
  .replace(/لم يكتمل بعد|مكتمل|✔|✅/g, '').replace(/\s+/g, ' ').trim();
async function vis(page, sel) { return page.evaluateHandle(sel => [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e); return r.width > 4 && r.height > 4 && cs.visibility !== 'hidden' && cs.display !== 'none'; }), sel); }
async function count(page, sel) { return page.evaluate(sel => [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e); return r.width > 4 && r.height > 4 && cs.visibility !== 'hidden' && cs.display !== 'none'; }).length, sel); }
async function clickIdx(page, sel, idx) {
  for (let t = 0; t < 40; t++) {
    if (await count(page, sel) > idx) {
      const h = await vis(page, sel); const el = (await h.getProperties()).get(String(idx)).asElement();
      await el.scrollIntoViewIfNeeded(); await el.click({timeout: 5000}); await page.waitForTimeout(700); return true;
    }
    await page.waitForTimeout(250);
  }
  return false;
}
async function openPath(page, key, cfg, prefix) {
  await page.goto(BASE + key + '/', {waitUntil: 'load'}); await page.waitForTimeout(900);
  for (const p of cfg.pre || []) if (!await clickIdx(page, p.sel, p.idx || 0)) return false;
  for (let d = 0; d < prefix.length; d++) if (!await clickIdx(page, cfg.levels[d], prefix[d])) return false;
  return true;
}
async function titles(page, sel) {
  return page.evaluate(sel => [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e); return r.width > 4 && r.height > 4 && cs.visibility !== 'hidden' && cs.display !== 'none'; }).map(e => e.innerText || e.textContent || ''), sel);
}
async function walk(page, key, cfg, prefix, depth) {
  if (!await openPath(page, key, cfg, prefix)) return [];
  const ts = (await titles(page, cfg.levels[depth])).map(clean);
  const nodes = ts.map(t => ({t}));
  if (depth + 1 < cfg.levels.length)
    for (let i = 0; i < nodes.length; i++) { const kids = await walk(page, key, cfg, prefix.concat(i), depth + 1); if (kids.length) nodes[i].k = kids; }
  return nodes;
}
(async () => {
  const b = await chromium.launch({executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium'});
  const res = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : {};
  for (const key of Object.keys(CFG)) {
    if (only.length && !only.includes(key)) continue; const cfg = CFG[key]; if (!cfg.levels) continue;
    const ctx = await b.newContext({viewport: {width: 1100, height: 800}}); await ctx.addInitScript(() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} });
    const page = await ctx.newPage(); const errs = []; page.on('pageerror', e => errs.push(e.message));
    const t0 = Date.now();
    try { const tree = await walk(page, key, cfg, [], 0); res[key] = {levels: cfg.levels, pre: cfg.pre || [], tree};
      const n0 = tree.length, n1 = tree.reduce((a, x) => a + (x.k ? x.k.length : 0), 0), n2 = tree.reduce((a, x) => a + (x.k ? x.k.reduce((c, y) => c + (y.k ? y.k.length : 0), 0) : 0), 0);
      console.log(key.padEnd(24), 'L0', n0, 'L1', n1, 'L2', n2, ((Date.now() - t0) / 1000).toFixed(0) + 's', 'errs', errs.length);
    } catch (e) { console.log(key, 'ERR', e.message.slice(0, 120)); }
    await ctx.close(); fs.writeFileSync(OUT, JSON.stringify(res, null, 1));
  }
  await b.close();
})();
