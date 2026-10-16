#!/usr/bin/env node
/* Second check for the ?go= deep links: open each sampled link, then reach the same place by clicking by hand in a fresh
   context, and compare a signature of both screens (hash, visible headings, visible counts per level, active tabs/steps).
   Works for apps where tabs/steps stay visible after the leaf click (where verify_games_nav.js gives false FAILs).
   Usage: SAMPLE=8 node tools/verify_games_nav2.js [key ...]   BASE defaults to http://127.0.0.1:8765/afuq/ */
const fs = require('fs'), path = require('path');
const {chromium} = require(process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright');
const NAV = JSON.parse(fs.readFileSync(process.env.NAVFILE || path.join(__dirname, 'games_nav.json'), 'utf8'));
const BASE = process.env.BASE || 'http://127.0.0.1:8765/afuq/', only = process.argv.slice(2), SAMPLE = +(process.env.SAMPLE || 8);
function* walk(nodes, prefix = []) { for (let i = 0; i < nodes.length; i++) { yield [prefix.concat(i), nodes[i]]; if (nodes[i].k) yield* walk(nodes[i].k, prefix.concat(i)); } }
const sig = (page, levels) => page.evaluate(levels => {
  const vis = e => { const r = e.getBoundingClientRect(), c = getComputedStyle(e); return r.width > 4 && r.height > 4 && c.visibility !== 'hidden' && c.display !== 'none'; };
  const txt = e => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60);
  const h = [...document.querySelectorAll('h1,h2,h3,h4')].filter(vis).map(txt).join('|');
  const n = levels.map(s => [...document.querySelectorAll(s)].filter(vis).length).join(',');
  const act = [...document.querySelectorAll('[class*="active"],[class*=" on"],[class$="on"],[aria-selected="true"],[class*="current"],[class*=" sel"]')].filter(vis).map(txt).filter(Boolean).slice(0, 6).join('|');
  return location.hash + ' #' + h + ' #' + n + ' #' + act;
}, levels);
async function clickPath(page, steps) {
  for (const s of steps) {
    let done = false;
    for (let t = 0; t < 48 && !done; t++) {
      const ok = await page.evaluate(({sel, idx}) => { const l = [...document.querySelectorAll(sel)].filter(e => { const r = e.getBoundingClientRect(), c = getComputedStyle(e); return r.width > 4 && r.height > 4 && c.visibility !== 'hidden' && c.display !== 'none'; });
        if (l.length > idx) { l[idx].scrollIntoView({block: 'center'}); l[idx].click(); return true; } return false; }, s);
      if (ok) done = true; else await page.waitForTimeout(250);
    }
    if (!done) return false; await page.waitForTimeout(700);
  }
  return true;
}
(async () => {
  const b = await chromium.launch({executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium'}); let bad = 0, total = 0;
  for (const key of Object.keys(NAV)) {
    if (only.length && !only.includes(key)) continue; const nav = NAV[key]; const [g, s, sec] = key.split('_');
    const url = `${BASE}${g}/${s}/games/${sec}/`; let all = [...walk(nav.tree)];
    if (SAMPLE && all.length > SAMPLE) { const st = all.length / SAMPLE; all = all.filter((_, i) => Math.floor(i % st) === 0).slice(0, SAMPLE); }
    const fails = [];
    for (const [p, node] of all) {
      const wait = 1500 + 900 * (p.length + (nav.pre || []).length);
      const c1 = await b.newContext({viewport: {width: 1100, height: 800}}); const a = await c1.newPage();
      await a.goto(url + '?go=' + p.join('.')); await a.waitForTimeout(wait); const s1 = await sig(a, nav.levels); await c1.close();
      const c2 = await b.newContext({viewport: {width: 1100, height: 800}}); const m = await c2.newPage();
      await m.goto(url); await m.waitForTimeout(900);
      const steps = (nav.pre || []).map(x => ({sel: x.sel, idx: x.idx || 0})).concat(p.map((v, i) => ({sel: nav.levels[i], idx: v})));
      const reached = await clickPath(m, steps); await m.waitForTimeout(800); const s2 = await sig(m, nav.levels); await c2.close();
      total++; if (!reached || s1 !== s2) { bad++; fails.push(p.join('.') + (reached ? '' : ' (manual path failed)') + '\n     link: ' + s1.slice(0, 160) + '\n     hand: ' + s2.slice(0, 160)); }
    }
    console.log(key.padEnd(24), all.length, 'links', fails.length ? 'FAIL\n   ' + fails.join('\n   ') : 'ok');
  }
  console.log('TOTAL', total, 'bad', bad); await b.close();
})();
