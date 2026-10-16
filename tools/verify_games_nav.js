#!/usr/bin/env node
/* Check every ?go= deep link of the game collections: open it in a fresh page and verify we landed where the map says
   (non-leaf: the next level lists exactly the mapped items; leaf: we left the list of its level).
   Usage: node tools/verify_games_nav.js [key ...]   BASE defaults to http://127.0.0.1:8765/afuq/  (serve the files repo there) */
const fs = require('fs'), path = require('path');
const {chromium} = require(process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright');
const NAV = JSON.parse(fs.readFileSync(process.env.NAVFILE || path.join(__dirname, 'games_nav.json'), 'utf8'));
// INJECT=1: test the plain open copies served at BASE=http://127.0.0.1:8765/_x/<key>/ by injecting the same loader that add_games.py ships
const INJECT = !!process.env.INJECT;
const LOADER = INJECT ? fs.readFileSync(path.join(__dirname, 'add_games.py'), 'utf8').match(/NAV_LOADER = \(r"""<script>([\s\S]*?)<\/script>"""\)/)[1] : '';
const BASE = process.env.BASE || 'http://127.0.0.1:8765/afuq/', only = process.argv.slice(2), SAMPLE = +(process.env.SAMPLE || 0);
const cnt = (page, sel) => page.evaluate(sel => [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e); return r.width > 4 && r.height > 4 && cs.visibility !== 'hidden' && cs.display !== 'none'; }).length, sel);
function* walk(nodes, prefix = []) { for (let i = 0; i < nodes.length; i++) { yield [prefix.concat(i), nodes[i]]; if (nodes[i].k) yield* walk(nodes[i].k, prefix.concat(i)); } }
(async () => {
  const b = await chromium.launch({executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium'}); let bad = 0, total = 0;
  for (const key of Object.keys(NAV)) {
    if (only.length && !only.includes(key)) continue; const nav = NAV[key]; const [g, s, sec] = key.split('_');
    const url = INJECT ? `${BASE}${key}/` : `${BASE}${g}/${s}/games/${sec}/`; let all = [...walk(nav.tree)]; if (SAMPLE && all.length > SAMPLE) { const step = all.length / SAMPLE; all = all.filter((_, i) => i % Math.ceil(step) === 0); }
    const ctx = await b.newContext({viewport: {width: 1100, height: 800}}); const errs = []; let fails = [];
    if (INJECT) await ctx.addInitScript(({nav, loader}) => { window.__NAV = {pre: nav.pre || [], levels: nav.levels}; document.addEventListener('DOMContentLoaded', () => { const sc = document.createElement('script'); sc.textContent = loader; document.body.appendChild(sc); }); }, {nav, loader: LOADER});
    for (const [p, node] of all) {
      const page = await ctx.newPage(); page.on('pageerror', e => errs.push(e.message));       // same context => storage stays dirty between links
      await page.goto(url + '?go=' + p.join('.')); await page.waitForTimeout(1200 + 800 * (p.length + (nav.pre || []).length));
      const d = p.length; let ok;
      if (node.k) ok = (await cnt(page, nav.levels[d])) === node.k.length;
      else ok = (await cnt(page, nav.levels[d - 1])) === 0 || (await cnt(page, nav.levels[d - 1])) !== (p.length > 1 ? 0 : 0) && !(await cnt(page, nav.levels[d - 1]));
      if (!node.k) ok = (await cnt(page, nav.levels[d - 1])) === 0;
      total++; if (!ok) { bad++; fails.push(p.join('.') + ' ' + node.t.slice(0, 30)); }
      await page.close();
    }
    console.log(key.padEnd(24), all.length, 'links', fails.length ? 'FAIL ' + fails.slice(0, 4).join(' | ') : 'ok', errs.length ? 'errs ' + errs.length : '');
    await ctx.close();
  }
  console.log('TOTAL', total, 'bad', bad); await b.close();
})();
