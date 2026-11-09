// Bischof Baumpflege – Bodenbelüftung. Ein Frame = render(t). Alles deterministisch.
import { C, W, H, el, rng, defs, vignette, smooth, wobble, inkStroke, line, hatch, blob, text, ease, clamp, prog, lerp, image, figure } from './lib.js';
import { drawTree, drawRoots, drawGround, TREE_CLUMPS } from './world.js';
import TIMING from './timing.json' with { type: 'json' };

export const DURATION = 89.0;
const GY = 1060, TREE_X = 360, TREE_S = 0.74, SEC_D = 300;
const CROWN_R = 277, SB_R = CROWN_R + 50;
const SUB_Y = 1440;
const sm = (a, b, t) => { const k = clamp((t - a) / (b - a)); return k * k * (3 - 2 * k); };
const W_ = (n, w) => { const L = TIMING[n].words; const f = L.find(x => x[0].replace(/[.,–?]/g, '').startsWith(w)); return f ? f[1] : 0; };

// ---------- Text-Messung ----------
const cv = document.createElement('canvas').getContext('2d');
function measure(str, size, family = 'BarlowCondensed', weight = 700, ls = 0) {
  cv.font = `${weight} ${size}px ${family}`;
  return cv.measureText(str).width + ls * size * str.length;
}
// Kinetische Headline: Buchstaben springen gestaffelt ein, gehen nach oben raus
function kinetic(parent, str, x, y, t, t0, t1, { size = 110, weight = 700, fill = C.ink, ls = 0.01, family = 'BarlowCondensed', maxW = 920, stagger = 0.028 } = {}) {
  if (t < t0 || t > t1 + 0.6) return;
  let s = size; while (measure(str, s, family, weight, ls) > maxW && s > 30) s -= 2;
  cv.font = `${weight} ${s}px ${family}`;
  let cx = x;
  const g = el('g', {}, parent);
  [...str].forEach((ch, i) => {
    const w = cv.measureText(ch).width + ls * s;
    const ki = clamp((t - t0 - i * stagger) / 0.42);
    const ko = clamp((t - t1 - i * stagger * 0.6) / 0.3);
    if (ki > 0 && ko < 1 && ch !== ' ') {
      const yo = (1 - ease.outBack(ki, 2.0)) * s * 0.55 - ease.inOutCubic(ko) * s * 0.5;
      const rot = (1 - ease.outCubic(ki)) * (i % 2 ? 8 : -6);
      const tx = el('text', { x: cx, y: y + yo, 'font-family': family, 'font-weight': weight, 'font-size': s, fill, opacity: clamp(ki * 4) * (1 - ko), transform: `rotate(${rot} ${cx + w / 2} ${y})` }, g);
      tx.textContent = ch;
    }
    cx += w;
  });
  return { w: cx - x, size: s };
}
function kicker(parent, str, t, t0, t1) {
  if (t < t0 || t > t1 + 0.5) return;
  const k = ease.outCubic(clamp((t - t0) / 0.5)), ko = ease.inOutCubic(clamp((t - t1) / 0.4));
  inkStroke(parent, [[80, 150], [80 + 60 * k * (1 - ko), 149]], { w: 7, color: C.orange, taper: false, seed: 90, filter: 'url(#marker)' });
  const g = el('g', { opacity: k * (1 - ko), transform: `translate(${(1 - k) * -30 - ko * 30},0)` }, parent);
  text(g, str, 162, 162, { size: 36, weight: 600, fill: C.orange, ls: 0.22 });
}
function underline(parent, x, y, w, t, t0, t1, seed = 91) {
  const k = ease.outCubic(clamp((t - t0) / 0.45)), ko = ease.inOutCubic(clamp((t - t1) / 0.35));
  if (k <= 0 || ko >= 1) return;
  const pts = wobble([[x, y], [x + w * 0.4, y - 5], [x + w, y + 2]], rng(seed), 2, 40);
  inkStroke(parent, pts, { w: 10, color: C.orange, seed, drawn: k * (1 - ko), filter: 'url(#marker)' });
}

// ---------- Untertitel ----------
function wrap(str, size, maxW) {
  const words = str.split(' '); const lines = []; let cur = '';
  for (const w of words) { const n = cur ? cur + ' ' + w : w; if (measure(n, size, 'Barlow', 500) > maxW && cur) { lines.push(cur); cur = w; } else cur = n; }
  if (cur) lines.push(cur); return lines;
}
function subtitles(parent, t, keys = [1, 2, 3, 4, 5, 6, 7]) {
  for (const n of keys) for (const [s, a, b] of TIMING[n].subs) {
    const t0 = a - 0.12, t1 = b + 0.25;
    if (t < t0 || t > t1 + 0.3) continue;
    const k = ease.outBack(clamp((t - t0) / 0.35), 1.6), ko = ease.inOutCubic(clamp((t - t1) / 0.25));
    const size = 34, lines = wrap(s.replace(' –', ''), size, 860);
    const bw = Math.max(...lines.map(l => measure(l, size, 'Barlow', 500))) + 56, bh = 26 + lines.length * 44;
    const y = Math.min(SUB_Y, 1535 - bh) + (1 - k) * 30 + ko * 16;
    const g = el('g', { opacity: clamp(k * 3) * (1 - ko) }, parent);
    const sg = el('g', { filter: 'url(#softShadow)' }, g);
    el('path', { d: `M${80 + 4},${y + 2} L${80 + bw - 3},${y} L${80 + bw + 1},${y + bh - 1} L${80 - 2},${y + bh + 2} Z`, fill: '#FBFAF6' }, sg);
    el('rect', { x: 78, y: y + 2, width: 7, height: bh - 2, fill: C.orange }, g);
    lines.forEach((l, i) => text(g, l, 80 + 30, y + 44 + i * 44, { size, family: 'Barlow', weight: 500, ls: 0 }));
  }
}

// =====================================================================
// Baumschutzfachliche Baubegleitung – Szenen
// =====================================================================
const paperImg = (g) => image(g, '../assets/paper.jpg', 0, 0, W, H);
function cam(g, cx, cy, z) { g.setAttribute('transform', `translate(${W / 2},${H / 2}) scale(${z}) translate(${-cx},${-cy})`); }
const K = (t, a, d = 0.6, e = ease.outCubic) => e(clamp((t - a) / d));
const note = (g, t, s, x, y, col, t0, { size = 50, rot = -3, arrow = null, bg = true } = {}) => {
  const k = ease.outBack(clamp((t - t0) / 0.45), 2); if (k <= 0) return;
  const gg = el('g', { transform: `translate(${x},${y}) scale(${k}) rotate(${rot})` }, g);
  if (bg) el('rect', { x: -10, y: -size * 0.82, width: measure(s, size, 'Caveat', 700) + 20, height: size * 1.1, fill: C.paper, rx: 6, opacity: 0.92 }, gg);
  text(gg, s, 0, 0, { size, family: 'Caveat', weight: 700, fill: col, ls: 0 });
  if (arrow) inkStroke(gg, arrow, { w: 3, color: col, seed: 220 + Math.round(x), drawn: clamp((t - t0 - 0.2) / 0.4), filter: col === C.ink ? 'url(#ink)' : 'url(#marker)' });
};
const card = (g, t, t0, t1, x, y, w, h, rot, draw) => {
  const k = ease.outBack(clamp((t - t0) / 0.5), 1.5), ko = ease.inOutCubic(clamp((t - t1) / 0.35));
  if (k <= 0 || ko >= 1) return;
  const cx = x + w / 2, cy = y + h / 2, s = k * (1 - ko);
  const G = el('g', { transform: `translate(${cx},${cy}) scale(${s}) rotate(${rot}) translate(${-cx},${-cy})` }, g);
  el('rect', { x, y, width: w, height: h, rx: 14, fill: '#FBFAF6', filter: 'url(#softShadow)' }, G);
  inkStroke(G, [[x, y], [x + w, y + 2], [x + w - 2, y + h], [x + 2, y + h - 1], [x, y]], { w: 3.2, seed: 980 + Math.round(x), taper: false });
  draw(G);
};
const check = (g, x, y, k, s = 1, col = C.orange) => { if (k <= 0) return; inkStroke(g, [[x - 14 * s, y], [x - 3 * s, y + 12 * s], [x + 18 * s, y - 16 * s]], { w: 6 * s, color: col, seed: 931 + Math.round(x), taper: false, drawn: k, filter: 'url(#marker)' }); };

// ---------- Boden (Seitenansicht) ----------
const SOIL = (() => {
  const r = rng(77), parts = [], pores = [];
  for (let i = 0; i < 300; i++) parts.push({ x: 50 + r() * 980, y: GY + 10 + r() * (SEC_D - 20), s: 4 + r() * 6, seed: 1000 + i, tone: r() < .5 ? '#CDB994' : '#E8DCC2' });
  for (let i = 0; i < 46; i++) pores.push({ x: 60 + r() * 960, y: GY + 24 + r() * (SEC_D - 48), rx: 12 + r() * 10, ry: 8 + r() * 5, seed: 2000 + i });
  const bottom = []; for (let x = 1040; x >= 40; x -= 30) bottom.push([x, GY + SEC_D + Math.sin(x * 0.05) * 6 + (r() - .5) * 10]);
  return { parts, pores, bottom };
})();
function soil(g, t, st) {
  const open = ease.outCubic(clamp(st.secOpen ?? 1)); if (open <= 0.01) return null;
  const D = SEC_D * open, x0 = 40, x1 = 1040;
  const bottom = SOIL.bottom.map(([x, y]) => [x, GY + (y - GY) * open]);
  const polyD = `M${x0},${GY} L${x1},${GY} L${bottom[0][0]},${bottom[0][1]} ` + smooth(bottom).replace(/^M[^C]*/, '') + ` L${x0},${GY} Z`;
  const id = 'so' + Math.round(t * 1000) + (st.id || '');
  const cp = el('clipPath', { id }, g); el('path', { d: polyD }, cp);
  const S = el('g', { opacity: st.secAlpha ?? 1 }, g);
  el('path', { d: polyD, fill: '#DCCDAE', opacity: 0.42 }, S);
  const zg = el('g', { 'clip-path': `url(#${id})` }, S);
  hatch(zg, [[x0, GY], [x1, GY], [x1, GY + D], [x0, GY + D]], { gap: 19, angle: -35, opacity: 0.3, seed: 101 });
  const dn = st.dense; const inD = (x) => dn && dn.k > 0 && x > dn.a && x < dn.b ? dn.k : 0;
  if (dn && dn.k > 0) {
    const dg = el('g', { opacity: dn.k }, zg);
    hatch(dg, [[dn.a, GY], [dn.b, GY], [dn.b, GY + D * 0.75], [dn.a, GY + D * 0.75]], { gap: 7, angle: -35, opacity: 0.55, seed: 102, cross: true });
  }
  for (const p of SOIL.pores) { const py = GY + (p.y - GY) * open, c = inD(p.x), k = 1 - 0.9 * c; if (k < 0.15) continue; const b = blob(p.x, py, p.rx * k, p.ry * k, rng(p.seed), 9, 0.2); el('path', { d: smooth(b, true), fill: C.paper, stroke: C.ink, 'stroke-width': 1.4, filter: 'url(#ink)' }, zg); }
  for (const p of SOIL.parts) { const py = GY + (p.y - GY) * open, c = inD(p.x); const b = blob(p.x, py, p.s * (1 + 0.2 * c), p.s * (0.95 - 0.35 * c), rng(p.seed), 7, 0.25); el('path', { d: smooth(b, true), fill: p.tone, stroke: C.ink, 'stroke-width': 1.5, filter: 'url(#ink)' }, zg); }
  inkStroke(S, [[x0, GY], ...[...bottom].reverse(), [x1, GY]], { w: 3.2, seed: 7, taper: false, opacity: 0.9 });
  inkStroke(S, [[x0, GY], [x0 + 2, GY + D * 0.5], [x0, GY + D]], { w: 3.5, seed: 8 });
  inkStroke(S, [[x1, GY], [x1 - 2, GY + D * 0.5], [x1, GY + D]], { w: 3.5, seed: 9 });
  return `url(#${id})`;
}
// ---------- Bauzaun, Stammschutz, Gebäude, Material ----------
const FENCE_X = [52, 180, 308, 436, 564, 690];
function fence(g, k, t, { checks = 0 } = {}) {
  if (k <= 0) return;
  const top = GY - 235, bot = GY - 8;
  FENCE_X.forEach((x, i) => {
    const kp = ease.outBack(clamp(k * FENCE_X.length * 1.25 - i * 1.1), 2); if (kp <= 0) return;
    const yTop = lerp(bot, top, kp);
    el('rect', { x: x - 16, y: bot - 4, width: 32, height: 14, fill: '#BDB6A8', stroke: C.ink, 'stroke-width': 2, filter: 'url(#ink)' }, g);
    inkStroke(g, [[x, bot], [x, yTop]], { w: 5, seed: 300 + i, taper: false });
    if (i < FENCE_X.length - 1) {
      const kpanel = clamp(k * FENCE_X.length * 1.25 - i * 1.1 - 0.6); if (kpanel <= 0) return;
      const x2 = lerp(x, FENCE_X[i + 1], ease.outCubic(kpanel));
      const pg = el('g', {}, g);
      for (let xx = x + 14; xx < x2; xx += 14) el('line', { x1: xx, y1: top + 4, x2: xx, y2: bot - 6, stroke: '#3a3a36', 'stroke-width': 1.6, opacity: 0.55 }, pg);
      for (let yy = top + 24; yy < bot; yy += 38) el('line', { x1: x, y1: yy, x2: x2, y2: yy, stroke: '#3a3a36', 'stroke-width': 1.6, opacity: 0.55 }, pg);
      inkStroke(g, [[x, top], [x2, top]], { w: 3.5, seed: 320 + i, taper: false });
      inkStroke(g, [[x, bot - 4], [x2, bot - 4]], { w: 3.5, seed: 330 + i, taper: false });
    }
  });
  // Schild
  const ks = ease.outBack(clamp(k * 1.6 - 1.0), 2);
  if (ks > 0) {
    const sx = 500, sy = GY - 150;
    const sg = el('g', { transform: `translate(${sx},${sy}) scale(${ks}) rotate(-2)` }, g);
    el('rect', { x: -78, y: -28, width: 156, height: 56, rx: 4, fill: C.orange, stroke: C.ink, 'stroke-width': 2.5, filter: 'url(#ink)' }, sg);
    text(sg, 'BAUMSCHUTZ', 0, 9, { size: 26, weight: 700, fill: '#fff', anchor: 'middle', ls: 0.06 });
  }
  if (checks > 0) [116, 372, 627].forEach((x, i) => check(g, x, GY - 270, clamp(checks * 3 - i), 1.1));
}
function stammschutz(g, k) {
  if (k <= 0) return;
  const cx = TREE_X, y0 = GY - 30, y1 = GY - 205, n = 6, w = 15;
  for (let i = 0; i < n; i++) {
    const kk = ease.outBack(clamp(k * 2.2 - i * 0.2), 2); if (kk <= 0) continue;
    const x = cx - 46 + i * 17, yt = lerp(y0, y1, kk);
    el('rect', { x, y: yt, width: w, height: y0 - yt, fill: '#D8B98A', stroke: C.ink, 'stroke-width': 2.4, filter: 'url(#ink)' }, g);
    line(g, [[x + 5, yt + 10], [x + 6, y0 - 10]], { w: 1.2, opacity: 0.5 });
  }
  if (k > 0.8) { line(g, [[cx - 50, y1 + 30], [cx + 56, y1 + 30]], { w: 2.2, color: '#555', opacity: 0.9 }); line(g, [[cx - 50, y0 - 30], [cx + 56, y0 - 30]], { w: 2.2, color: '#555', opacity: 0.9 }); }
}
function building(g, t, { plan = 0, built = 0, finish = 0 } = {}) {
  const x0 = 735, x1 = 1040, yb = GY, yt = 560;
  if (plan > 0 && finish < 1) {
    const pg = el('g', { opacity: 1 - finish }, g);
    line(pg, [[x0, yb], [x0, yt], [x1, yt]], { w: 3, color: C.ink, dash: '14 12', drawn: plan, opacity: 0.8 });
    if (plan > 0.6 && built <= 0) note(pg, t, 'geplant', x0 + 40, yt + 70, C.graphite, 0, { size: 44, bg: false });
  }
  if (built > 0) {
    const h = (yb - yt) * Math.min(1, built), yy = yb - h;
    el('rect', { x: x0, y: yy, width: x1 - x0 + 20, height: h, fill: '#DCD3C3', opacity: 1 }, g);
    hatch(g, [[x0, yy], [x1 + 20, yy], [x1 + 20, yb], [x0, yb]], { gap: 11, angle: -50, opacity: 0.5 * (1 - finish), seed: 61 });
    if (finish < 1) for (let yy3 = yb - 60; yy3 > yy + 10; yy3 -= 60) line(g, [[x0 + 4, yy3], [x1 + 16, yy3]], { w: 1.6, color: C.ink, opacity: 0.45 * (1 - finish) });
    inkStroke(g, [[x0, yb], [x0, yy], [x1 + 20, yy]], { w: 4.5, seed: 62, taper: false });
    if (finish < 1) { const sg = el('g', { opacity: 1 - finish }, g); for (let yy2 = yb - 80; yy2 > yy; yy2 -= 80) line(sg, [[x0 - 30, yy2], [x0 + 6, yy2]], { w: 2.2, color: C.ink, opacity: 0.8 }); line(sg, [[x0 - 30, yb], [x0 - 30, yy - 10]], { w: 2.4, color: C.ink, opacity: 0.8 }); }
    if (finish > 0) {
      for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) {
        const kk = ease.outBack(clamp(finish * 3 - (r * 3 + c) * 0.12), 2); if (kk <= 0) continue;
        const wx = x0 + 34 + c * 90, wy = yt + 40 + r * 105;
        el('rect', { x: wx, y: wy, width: 58 * kk, height: 64 * kk, fill: '#CFD9DF', stroke: C.ink, 'stroke-width': 3, filter: 'url(#ink)' }, g);
      }
      inkStroke(g, [[x0 - 10, yt - 6], [x1 + 20, yt - 8]], { w: 6, seed: 63, taper: false, drawn: finish });
    }
  }
}
function pitDashed(g, k) { if (k <= 0) return; line(g, [[745, GY + 2], [760, GY + 190], [1030, GY + 190]], { w: 3, color: C.ink, dash: '12 10', drawn: k, opacity: 0.85 }); }
function materials(g, k) {
  if (k <= 0) return;
  const kk = ease.outBack(clamp(k), 1.8);
  const mg = el('g', { transform: `translate(980,${GY}) scale(${kk}) translate(-980,${-GY})` }, g);
  el('rect', { x: 900, y: GY - 70, width: 120, height: 66, fill: '#D8B98A', stroke: C.ink, 'stroke-width': 2.6, filter: 'url(#ink)' }, mg);
  line(mg, [[904, GY - 66], [1016, GY - 8]], { w: 2, color: C.ink, opacity: 0.6 }); line(mg, [[1016, GY - 66], [904, GY - 8]], { w: 2, color: C.ink, opacity: 0.6 });
  [[930, GY - 92], [965, GY - 92], [1000, GY - 92], [948, GY - 122], [983, GY - 122]].forEach(([x, y], i) => { el('circle', { cx: x, cy: y, r: 17, fill: '#B9C2C7', stroke: C.ink, 'stroke-width': 2.6, filter: 'url(#ink)' }, mg); el('circle', { cx: x, cy: y, r: 8, fill: 'none', stroke: C.ink, 'stroke-width': 1.6 }, mg); });
}
function excavator(g, x, { bob = 0, rot = 0 } = {}) {
  const Hh = 300, Ww = Hh * 1088 / 800;
  const G = el('g', { transform: `translate(${x},${GY + 6 + bob}) rotate(${rot})` }, g);
  image(G, '../assets/cut/bagger_1.png', -Ww / 2, -Hh, Ww, Hh);
  return Ww;
}
function loaderBack(g, x, s = 0.55) {
  const Hh = 250 * s, Ww = Hh * 2003 / 1213;
  image(g, '../assets/cut/radlader_1.png', x - Ww / 2, GY - 40 - Hh, Ww, Hh);
}
function site(g, t, st) {
  const pg = el('g', { opacity: 0.5 }, g); const pr = rng(11);
  for (let i = 0; i < 16; i++) { const x = (pr() * 1200 + t * (8 + pr() * 10)) % 1200 - 60, y = 480 + pr() * 520 + Math.sin(t * 0.8 + i) * 12; el('circle', { cx: x, cy: y, r: 1.5 + pr() * 2, fill: C.graphite, opacity: 0.35 }, pg); }
  building(g, t, st.bld || {});
  if (st.vehicle) loaderBack(g, st.vehicle.x, st.vehicle.s);
  const clip = soil(g, t, st);
  pitDashed(g, st.pit || 0);
  const rg = el('g', { opacity: st.secAlpha ?? 1 }, g);
  drawRoots(rg, { x: TREE_X, groundY: GY, s: 0.8, clip, drawn: st.rootsDrawn ?? 1, spread: 1.32 });
  if (st.orange > 0) {
    const oid = 'or' + Math.round(t * 1000); const oc = el('clipPath', { id: oid }, g); el('rect', { x: st.orX ?? 480, y: GY, width: 700, height: 400 }, oc);
    const og = el('g', { 'clip-path': `url(#${oid})`, opacity: st.orange }, g);
    drawRoots(og, { x: TREE_X, groundY: GY, s: 0.8, clip: null, drawn: 1, spread: 1.32, color: C.orange, filter: 'url(#marker)' });
  }
  drawTree(g, { x: TREE_X, groundY: GY, s: TREE_S, drawn: st.treeDrawn ?? 1, greens: st.greens ?? 1, sway: Math.sin(t * 1.1) * 0.6 + Math.sin(t * 2.3) * 0.25 });
  if (st.greenBoost > 0) { const gg = el('g', { style: 'mix-blend-mode:multiply', opacity: st.greenBoost }, g); const b = blob(TREE_X + 40, GY - 560, 70, 46, rng(5), 12, 0.18); el('path', { d: smooth(b, true), fill: C.green, opacity: 0.6, filter: 'url(#marker)' }, gg); }
  stammschutz(g, st.stamm || 0);
  drawGround(g, { y: GY, drawn: st.groundDrawn ?? 1 });
  materials(g, st.mat || 0);
}

// ---------- Plan (Draufsicht) ----------
const PC = [380, 900];
function plan(g, t, t0) {
  const k = (a, d = 0.6) => K(t, t0 + a, d);
  const x = 60, y = 500, w = 960, h = 820;
  el('rect', { x, y, width: w, height: h, rx: 10, fill: '#F1F3F0', filter: 'url(#softShadow)' }, g);
  const gr = el('g', { opacity: 0.55 }, g);
  for (let xx = x + 40; xx < x + w; xx += 40) el('line', { x1: xx, y1: y + 8, x2: xx, y2: y + h - 8, stroke: '#9FB3BE', 'stroke-width': 1 }, gr);
  for (let yy = y + 40; yy < y + h; yy += 40) el('line', { x1: x + 8, y1: yy, x2: x + w - 8, y2: yy, stroke: '#9FB3BE', 'stroke-width': 1 }, gr);
  inkStroke(g, [[x, y], [x + w, y + 2], [x + w - 2, y + h], [x + 2, y + h - 1], [x, y]], { w: 3.5, seed: 700, taper: false });
  text(g, 'BAUPLAN', x + 22, y + 44, { size: 30, weight: 700, fill: '#5C7380', ls: 0.2 });
  // Gebäude + Baugrube
  const kb = k(0.3, 0.8);
  if (kb > 0) {
    el('rect', { x: 690, y: 650, width: 290 * kb, height: 440, fill: '#DCE3E6', stroke: C.ink, 'stroke-width': 3, filter: 'url(#ink)' }, g);
    if (kb > 0.9) { hatch(g, [[690, 650], [980, 650], [980, 1090], [690, 1090]], { gap: 12, angle: 45, opacity: 0.35, seed: 701 }); text(g, 'Neubau', 835, 880, { size: 40, family: 'Caveat', weight: 700, fill: C.ink, anchor: 'middle', ls: 0 }); }
  }
  const kp = k(0.9, 0.8);
  if (kp > 0) { line(g, [[640, 610], [1020, 610], [1020, 1130], [640, 1130], [640, 610]], { w: 3, color: C.ink, dash: '12 10', drawn: kp, opacity: 0.85 }); if (kp > 0.9) text(g, 'Baugrubenrand', 1010, 1166, { size: 36, family: 'Caveat', weight: 700, fill: C.graphite, anchor: 'end', ls: 0 }); }
  // Baum (Draufsicht)
  const kt = k(0.0, 0.8);
  if (kt > 0) {
    const cr = blob(PC[0], PC[1], 235 * kt, 235 * kt, rng(71), 26, 0.06);
    el('path', { d: smooth(cr, true), fill: '#E3EBD8', opacity: 0.8 }, g);
    inkStroke(g, [...cr, cr[0]], { w: 3.6, seed: 702, taper: false });
    const gz = el('g', { style: 'mix-blend-mode:multiply' }, g);
    const zz = []; for (let i = 0; i < 7; i++) { const yy = PC[1] - 120 + i * 40; zz.push([PC[0] - 120, yy], [PC[0] + 110, yy + 18]); }
    inkStroke(gz, zz, { w: 12, color: C.green, seed: 703, opacity: 0.55 * kt, filter: 'url(#marker)' });
    el('circle', { cx: PC[0], cy: PC[1], r: 20 * kt, fill: '#8A6A4A', stroke: C.ink, 'stroke-width': 3 }, g);
  }
  return { k };
}
function planMarks(g, t, { tK, tS, tC, tF }) {
  // Kronentraufe
  const kk = K(t, tK, 0.8);
  if (kk > 0) {
    const pts = []; for (let a = 0; a <= 1.0001; a += 1 / 60) pts.push([PC[0] + Math.cos(a * 6.283 - 1.57) * 250, PC[1] + Math.sin(a * 6.283 - 1.57) * 250]);
    line(g, pts, { w: 3, color: C.ink, dash: '10 9', drawn: kk, opacity: 0.9 });
    note(g, t, 'Kronentraufe', PC[0] - 105, PC[1] - 175, C.ink, tK + 0.4, { size: 44, rot: -4 });
  }
  // Schutzbereich = Kronentraufe + 1,50 m
  const ks = K(t, tS, 0.8);
  if (ks > 0) {
    const pts = []; for (let a = 0; a <= 1.0001; a += 1 / 70) pts.push([PC[0] + Math.cos(a * 6.283 - 1.57) * 300, PC[1] + Math.sin(a * 6.283 - 1.57) * 300]);
    inkStroke(g, pts, { w: 6, color: C.orange, seed: 720, taper: false, drawn: ks, filter: 'url(#marker)' });
    const ka = K(t, tS + 0.5, 0.4);
    if (ka > 0) {
      const a = 2.5, p1 = [PC[0] + Math.cos(a) * 250, PC[1] + Math.sin(a) * 250], p2 = [PC[0] + Math.cos(a) * 300, PC[1] + Math.sin(a) * 300];
      inkStroke(g, [p1, [lerp(p1[0], p2[0], ka), lerp(p1[1], p2[1], ka)]], { w: 3, color: C.orange, seed: 721, taper: false, filter: 'url(#marker)' });
      note(g, t, '+ 1,50 m', p2[0] - 150, p2[1] + 70, C.orange, tS + 0.6, { size: 46, rot: -6 });
    }
    note(g, t, 'Schutzbereich', 84, 1238, C.orange, tS + 0.9, { size: 46, rot: -3 });
  }
  // Konflikt: Baugrube ragt in den Schutzbereich
  const kc = K(t, tC, 0.5);
  if (kc > 0) {
    const cid = 'cf' + Math.round(t * 1000); const cp = el('clipPath', { id: cid }, g); el('circle', { cx: PC[0], cy: PC[1], r: 300 }, cp);
    const cg = el('g', { 'clip-path': `url(#${cid})`, opacity: kc }, g);
    el('rect', { x: 640, y: 610, width: 400, height: 520, fill: C.orange, opacity: 0.25 }, cg);
    hatch(cg, [[640, 610], [700, 610], [700, 1130], [640, 1130]], { gap: 8, angle: 45, opacity: 0.8, seed: 722, color: C.orange });
    const kx = ease.outBack(clamp((t - tC) / 0.4), 3);
    const xg = el('g', { transform: `translate(625,760) scale(${kx})` }, g);
    el('circle', { cx: 0, cy: 0, r: 26, fill: C.orange, stroke: C.ink, 'stroke-width': 3 }, xg);
    text(xg, '!', 0, 13, { size: 38, weight: 700, fill: '#fff', anchor: 'middle' });
  }
  // Schutzmaßnahme: Baumschutzzaun um den Schutzbereich
  const kf = K(t, tF, 1.0, ease.inOutCubic);
  if (kf > 0) {
    const pts = []; for (let a = 0.25; a <= 0.25 + 0.86; a += 1 / 90) pts.push([PC[0] + Math.cos(a * 6.283) * 312, PC[1] + Math.sin(a * 6.283) * 312]);
    const n = Math.max(2, Math.floor(pts.length * kf));
    line(g, pts.slice(0, n), { w: 4, color: C.ink, opacity: 0.95 });
    for (let i = 0; i < n; i += 5) { const [px, py] = pts[i]; inkStroke(g, [[px - 7, py - 7], [px + 7, py + 7]], { w: 2.6, seed: 740 + i, taper: false }); inkStroke(g, [[px + 7, py - 7], [px - 7, py + 7]], { w: 2.6, seed: 760 + i, taper: false }); }
    note(g, t, 'Baumschutzzaun', 400, 1302, C.ink, tF + 0.5, { size: 44, rot: -2 });
    note(g, t, 'Lösung abstimmen', 640, 1240, C.orange, tF + 0.9, { size: 44, rot: -2, arrow: [[-20, -40], [-30, -150], [-10, -280]] });
  }
}

// ---------- Nahaufnahme Boden (Szenen 4–5) ----------
const NG = 780; // Bodenoberkante in der Nahaufnahme
const ROOTS = [{ y: 830, w: 24 }, { y: 900, w: 17 }, { y: 985, w: 13 }, { y: 1075, w: 10 }, { y: 1185, w: 7 }];
const TR = { x0: 590, x1: 800, bot: 1265 };
const NSOIL = (() => { const r = rng(55), p = []; for (let i = 0; i < 260; i++) p.push({ x: r() * 1080, y: NG + 10 + r() * 600, s: 6 + r() * 9, seed: 3000 + i, tone: r() < .5 ? '#CDB994' : '#E8DCC2' }); return p; })();
function rootPath(R, i) { const pts = []; for (let x = -40; x <= 1120; x += 60) pts.push([x, R.y + (x / 1080) * 40 + Math.sin(x * 0.01 + i * 1.7) * 14]); return pts; }
function closeSoil(g, t, { dig = 0, heap = 0, orange = 0, markers = 0, trace = 0, plannedK = 0 } = {}) {
  el('rect', { x: 0, y: NG, width: W, height: 640, fill: '#DCCDAE', opacity: 0.45 }, g);
  hatch(g, [[0, NG], [W, NG], [W, NG + 640], [0, NG + 640]], { gap: 18, angle: -35, opacity: 0.3, seed: 811 });
  const dy = lerp(NG, TR.bot, dig);
  for (const p of NSOIL) { if (dig > 0 && p.x > TR.x0 - 6 && p.x < TR.x1 + 6 && p.y < dy) continue; const b = blob(p.x, p.y, p.s, p.s * 0.85, rng(p.seed), 8, 0.22); el('path', { d: smooth(b, true), fill: p.tone, stroke: C.ink, 'stroke-width': 1.8, filter: 'url(#ink)' }, g); }
  // freigelegter Graben
  if (dig > 0) {
    el('rect', { x: TR.x0, y: NG, width: TR.x1 - TR.x0, height: dy - NG, fill: '#F7F4EC' }, g);
    inkStroke(g, [[TR.x0, NG], [TR.x0 + 4, dy]], { w: 3.5, seed: 812, taper: false });
    inkStroke(g, [[TR.x1, NG], [TR.x1 - 4, dy]], { w: 3.5, seed: 813, taper: false });
    inkStroke(g, [[TR.x0 + 4, dy], [TR.x1 - 4, dy]], { w: 3, seed: 814, taper: false, opacity: 0.8 });
    hatch(g, [[TR.x0 + 4, dy - 20], [TR.x1 - 4, dy - 20], [TR.x1 - 4, dy], [TR.x0 + 4, dy]], { gap: 7, angle: -40, opacity: 0.5, seed: 815 });
  }
  // Baumwurzeln (vom Baum links)
  ROOTS.forEach((R, i) => {
    const pts = rootPath(R, i);
    inkStroke(g, pts, { w: R.w, seed: 820 + i });
    const r = rng(830 + i);
    for (let j = 2; j < pts.length - 1; j += 2) { const [a, b] = pts[j], up = j % 4 ? -1 : 1, L = 20 + r() * 26; inkStroke(g, [[a, b], [a + 12, b + up * L * .6], [a + 22, b + up * L]], { w: 2.2, seed: 840 + i * 10 + j }); }
    if (dig > 0) { // freigelegt: hell hervorgehoben
      const id = 'tc' + i + Math.round(t * 1000); const cp = el('clipPath', { id }, g); el('rect', { x: TR.x0, y: NG, width: TR.x1 - TR.x0, height: dy - NG }, cp);
      const hg = el('g', { 'clip-path': `url(#${id})` }, g);
      inkStroke(hg, pts.map(([a, b]) => [a, b - R.w * 0.18]), { w: R.w * 0.35, seed: 850 + i, color: '#F3E7D2', opacity: 0.9, filter: null });
      if (orange > 0) inkStroke(hg, pts, { w: R.w + 8, seed: 860 + i, color: C.orange, opacity: 0.45 * orange, filter: 'url(#marker)' });
    }
  });
  // Wurzelstamm-Anlauf links
  inkStroke(g, [[-20, NG - 260], [40, NG - 120], [70, NG - 10], [110, NG + 30]], { w: 7, seed: 870 });
  hatch(g, [[-20, NG - 260], [36, NG - 120], [60, NG], [-20, NG]], { gap: 7, angle: -60, opacity: 0.5, seed: 871 });
  // Bodenoberkante + Gras
  inkStroke(g, [[0, NG], [TR.x0, NG + 2]], { w: 4.5, seed: 872, taper: false });
  inkStroke(g, [[TR.x1, NG + 2], [W, NG]], { w: 4.5, seed: 873, taper: false });
  if (dig <= 0) inkStroke(g, [[TR.x0, NG + 2], [TR.x1, NG + 2]], { w: 4.5, seed: 874, taper: false });
  const gr = rng(9); for (let x = 130; x < W; x += 30 + gr() * 30) { if (x > TR.x0 - 10 && x < TR.x1 + 10) continue; for (let k2 = 0; k2 < 3; k2++) line(g, [[x + k2 * 5, NG + 1], [x + k2 * 5 + 3, NG - 12 - gr() * 12]], { w: 2, color: C.ink, opacity: 0.85, filter: 'url(#ink)' }); }
  // geplante Leitung (gestrichelt)
  if (plannedK > 0 && dig < 0.05) { line(g, [[TR.x0, NG], [TR.x0, TR.bot], [TR.x1, TR.bot], [TR.x1, NG]], { w: 3.5, color: C.ink, dash: '14 10', drawn: plannedK, opacity: 0.85 }); }
  // Aushub
  if (heap > 0) { const hb = []; for (let a = 0; a <= 1.0001; a += 0.05) hb.push([lerp(820, 1000, a), NG - Math.sin(a * Math.PI) * 70 * heap]); el('path', { d: smooth(hb) + 'Z', fill: '#CDB994', opacity: 0.85 }, g); inkStroke(g, hb, { w: 3.5, seed: 880, taper: false }); }
  // Marker + Wurzelverlauf
  if (markers > 0) ROOTS.forEach((R, i) => {
    const pts = rootPath(R, i), mx = 695, my = R.y + (mx / 1080) * 40 + Math.sin(mx * 0.01 + i * 1.7) * 14;
    const km = ease.outBack(clamp(markers * 5 - i), 2.5); if (km <= 0) return;
    if (trace > 0) line(g, pts.filter(p => p[0] > TR.x1), { w: 3, color: C.orange, dash: '10 8', drawn: trace, opacity: 0.9, filter: 'url(#marker)' });
    const mg = el('g', { transform: `translate(${mx},${my - R.w / 2 - 22}) scale(${km})` }, g);
    el('circle', { cx: 0, cy: 0, r: 17, fill: '#fff', stroke: C.orange, 'stroke-width': 3.5 }, mg);
    text(mg, String(i + 1), 0, 8, { size: 24, weight: 700, fill: C.ink, anchor: 'middle' });
  });
}
function rootCurtain(g, t, t0) {
  // schematischer Wurzelvorhang: Wurzeln | Substrat | Vorhang | Baugrube
  const k = (a, d = 0.5) => K(t, t0 + a, d);
  el('rect', { x: 0, y: NG, width: W, height: 640, fill: '#F7F4EC' }, g);
  el('rect', { x: 0, y: NG, width: 520, height: 640, fill: '#DCCDAE', opacity: 0.45 }, g);
  hatch(g, [[0, NG], [520, NG], [520, NG + 640], [0, NG + 640]], { gap: 18, angle: -35, opacity: 0.3, seed: 901 });
  // Substrat
  const ks = k(0.5); if (ks > 0) { el('rect', { x: 470, y: NG, width: 70, height: 560 * ks, fill: '#E2C98F', opacity: 0.85 }, g); const r = rng(5); for (let i = 0; i < 70 * ks; i++) el('circle', { cx: 474 + r() * 62, cy: NG + 6 + r() * 548 * ks, r: 2 + r() * 2.5, fill: '#8C6B3E', opacity: 0.8 }, g); }
  ROOTS.forEach((R, i) => { const pts = rootPath(R, i).filter(p => p[0] <= 520); pts.push([520, pts[pts.length - 1][1] + 2]); inkStroke(g, pts, { w: R.w, seed: 820 + i }); const e = pts[pts.length - 1]; for (let f = 0; f < 3; f++) inkStroke(g, [e, [e[0] + 10 + f * 6, e[1] - 10 + f * 10]], { w: 1.8, seed: 950 + i * 3 + f, drawn: k(1.0 + i * 0.1) }); });
  // Vorhang: Pfähle, Gitter, Jute
  const kv = k(1.0, 0.9);
  if (kv > 0) {
    const yb = NG + 560 * kv;
    el('rect', { x: 540, y: NG, width: 22, height: yb - NG, fill: '#B98C55', opacity: 0.85 }, g);
    hatch(g, [[540, NG], [562, NG], [562, yb], [540, yb]], { gap: 6, angle: 45, opacity: 0.6, seed: 902, color: '#5a3a1a', cross: true });
    inkStroke(g, [[540, NG - 30], [540, yb]], { w: 4, seed: 903, taper: false }); inkStroke(g, [[562, NG - 30], [562, yb]], { w: 4, seed: 904, taper: false });
    for (let y = NG - 30; y < yb; y += 140) el('rect', { x: 536, y, width: 30, height: 18, fill: '#8a6a4a', stroke: C.ink, 'stroke-width': 2 }, g);
  }
  // Baugrube
  const kg = k(1.6, 0.6); if (kg > 0) { inkStroke(g, [[564, NG + 560], [1080, NG + 560]], { w: 4, seed: 905, taper: false, drawn: kg }); hatch(g, [[564, NG + 560], [1080, NG + 560], [1080, NG + 640], [564, NG + 640]], { gap: 9, angle: -40, opacity: 0.45 * kg, seed: 906 }); }
  inkStroke(g, [[0, NG], [540, NG + 2]], { w: 4.5, seed: 907, taper: false });
  note(g, t, 'zu erhaltende Wurzeln', 40, NG + 300, C.ink, t0 + 0.4, { size: 42, rot: -2 });
  note(g, t, 'Substrat', 360, NG + 470, '#8C6B3E', t0 + 0.9, { size: 42, rot: -4, arrow: [[150, -10], [170, -30], [125, -50]] });
  note(g, t, 'Wurzelvorhang', 600, NG + 120, C.orange, t0 + 1.3, { size: 46, rot: -3, arrow: [[-10, 10], [-30, 30], [-44, 60]] });
  note(g, t, 'Baugrube', 760, NG + 420, C.graphite, t0 + 1.8, { size: 44, rot: -2 });
  note(g, t, 'mögliche Maßnahme', 600, NG + 510, C.orange, t0 + 2.3, { size: 40, rot: -2 });
  note(g, t, 'zur Schadensminimierung', 600, NG + 556, C.orange, t0 + 2.4, { size: 40, rot: -2 });
}

// ---------- Szene-Zustände (Seitenansicht) ----------
function stS1(t) {
  const tB = W_(1, 'Bauarbeiten'), tBe = W_(1, 'beschädigen'), tV = W_(1, 'verdichten');
  return {
    treeDrawn: clamp((t + 0.15) / 2.2), greens: clamp((t - 1.9) / 0.8), groundDrawn: ease.outCubic(clamp((t + 0.35) / 1.0)),
    secOpen: clamp((t - 0.5) / 1.0), secAlpha: 0.82, rootsDrawn: clamp((t - 0.9) / 1.6),
    bld: { plan: K(t, W_(1, 'Bauprojekt') - 0.1, 1.1, ease.inOutCubic) }, pit: K(t, W_(1, 'Bauprojekt') + 0.6, 0.9, ease.inOutCubic),
    orange: K(t, tBe - 0.1, 0.7), orX: 470, dense: { a: 440, b: 860, k: K(t, tV - 0.15, 0.7) },
  };
}
function excavatorX(t) { const t0 = W_(1, 'Bauarbeiten') - 0.9; return lerp(1350, 640, ease.outCubic(clamp((t - t0) / 1.6))); }
function stSite(t, phase) {
  const s = { treeDrawn: 1, greens: 1, groundDrawn: 1, secOpen: 1, secAlpha: 1, rootsDrawn: 1, bld: { plan: 1 }, pit: 1 };
  if (phase === 3) {
    s.fence = K(t, W_(3, 'Schutzbereichen') - 0.4, 2.2, ease.linear || (x => x));
    s.stamm = K(t, W_(3, 'Stamm') - 0.2, 0.8);
    s.mat = K(t, W_(3, 'Vorgaben') - 0.2, 0.5);
    s.vehicle = { x: lerp(1300, 880, ease.outCubic(clamp((t - 25.2) / 2.2))), s: 0.5 };
  }
  if (phase === 6) { s.fence = 1; s.stamm = 1; s.mat = 1; s.vehicle = { x: 880, s: 0.5 }; s.bld = { plan: 1, built: 0.55 }; s.pit = 0; }
  if (phase === 7) {
    const kf = K(t, 73.4, 2.0, ease.inOutCubic);
    s.fence = 1 - K(t, 74.0, 0.9, ease.inOutCubic); s.stamm = 1 - K(t, 74.2, 0.8, ease.inOutCubic); s.mat = 1 - K(t, 73.8, 0.6, ease.inOutCubic);
    s.vehicle = { x: lerp(880, 1400, K(t, 73.5, 1.2, ease.inOutCubic)), s: 0.5 }; s.pit = 0;
    s.bld = { plan: 1, built: lerp(0.55, 1, kf), finish: K(t, 74.6, 1.6) };
    s.greenBoost = K(t, W_(7, 'wertvolle') - 0.2, 1.2);
  }
  return s;
}
function drawFencePhase(g, t, s, checks = 0) { fence(g, s.fence || 0, t, { checks }); }

// ---------- Hauptrender ----------
export function render(svg, t) {
  svg.innerHTML = '';
  const fr = Math.round(t * 30);
  defs(svg, 1 + Math.floor(fr / 3) % 6);
  paperImg(svg);
  const stage = el('g', {}, svg), ui = el('g', {}, svg);

  // ===== Szene 1 (0 – 13.6) + Zurückspulen =====
  if (t < 14.7) {
    const rw = clamp((t - 12.35) / 1.2);                // Zurückspulen
    const ts = t < 12.35 ? t : lerp(12.35, 4.6, ease.inOutCubic(rw));
    const fold = ease.inOutCubic(clamp((t - 13.55) / 0.6)); // Umklappen in den Plan
    const g = el('g', { transform: `translate(0,${GY}) scale(1,${1 - fold}) translate(0,${-GY})` }, stage);
    const cg = el('g', {}, g); cam(cg, 540, 960, lerp(1, 1.025, clamp(t / 12)) + (rw > 0 && rw < 1 ? Math.sin(t * 80) * 0.003 : 0));
    const st = stS1(ts);
    site(cg, ts, st);
    if (ts > W_(1, 'Bauarbeiten') - 1.0) {
      const ex = excavatorX(ts), bob = Math.abs(Math.sin(ts * 9)) * (ex > 645 ? 2 : 0) + (ts > W_(1, 'verdichten') - 0.2 ? Math.sin(clamp((ts - W_(1, 'verdichten') + 0.2) / 0.4) * Math.PI) * 5 : 0);
      excavator(cg, ex, { bob });
      const tV = W_(1, 'verdichten');
      if (ts > tV - 0.2 && ts < tV + 1.6) { const k = clamp((ts - tV + 0.2) / 0.4) * (1 - clamp((ts - tV - 1.1) / 0.5)); [ex - 130, ex + 120].forEach((ax, i) => { const ag = el('g', { opacity: k }, cg); inkStroke(ag, [[ax, GY + 20], [ax, GY + 20 + 60 * k]], { w: 6, seed: 120 + i }); inkStroke(ag, [[ax - 14, GY + 62 * k + 4], [ax, GY + 22 + 62 * k], [ax + 14, GY + 62 * k + 4]], { w: 5, seed: 130 + i }); }); }
    }
    // Fragezeichen am Baum
    const tq = W_(1, 'passiert') - 0.2; if (ts > tq && ts < 8.2) { const k = ease.outBack(clamp((ts - tq) / 0.45), 2.5) * (1 - clamp((ts - 7.6) / 0.4)); const qg = el('g', { transform: `translate(${TREE_X + 300},${GY - 640}) scale(${k}) rotate(8)` }, cg); text(qg, '?', 0, 0, { size: 150, family: 'Caveat', weight: 700, fill: C.orange, anchor: 'middle' }); }
    // Zurückspul-Symbol
    if (rw > 0 && rw < 1) { const ig = el('g', { transform: 'translate(900,520)', opacity: Math.sin(rw * Math.PI) }, ui); [0, 46].forEach((o, i) => el('path', { d: `M${o + 40},-34 L${o},0 L${o + 40},34 Z`, fill: C.orange, stroke: C.ink, 'stroke-width': 3 }, ig)); const sl = el('g', { opacity: 0.5 * Math.sin(rw * Math.PI) }, ui); for (let i = 0; i < 9; i++) { const y = 520 + i * 100 + (t * 900 % 100); line(sl, [[60 + (i % 3) * 300, y], [260 + (i % 3) * 300, y]], { w: 2, color: C.graphite }); } }
    kicker(ui, '01 · AUSGANGSLAGE', t, 4.8, 12.2);
    kinetic(ui, 'BAUARBEITEN', 76, 290, t, W_(1, 'Bauarbeiten') - 0.1, 12.1, { size: 118 });
    const h2 = kinetic(ui, 'IM WURZELBEREICH', 76, 410, t, W_(1, 'Bauarbeiten') + 0.25, 12.15, { size: 118 });
    if (h2) underline(ui, 80, 440, h2.w, t, W_(1, 'Wurzeln') + 0.2, 12.15, 91);
  }
  // ===== Szene 2 (13.55 – 24.9): Bauplan =====
  if (t >= 13.55 && t < 24.95) {
    const unfold = ease.outBack(clamp((t - 14.05) / 0.6), 1.2);
    const wipe = ease.inOutCubic(clamp((t - 24.2) / 0.7));
    const g = el('g', { transform: `translate(0,${GY}) scale(1,${unfold}) translate(0,${-GY})` }, stage);
    if (wipe > 0) { const m = el('mask', { id: 'w2', maskUnits: 'userSpaceOnUse', x: 0, y: 0, width: W, height: H }, svg); const ex = lerp(-500, 1700, wipe); el('path', { d: `M${ex + 300},-10 L${W + 20},-10 L${W + 20},${H + 10} L${ex - 300},${H + 10} Z`, fill: '#fff' }, m); g.setAttribute('mask', 'url(#w2)'); }
    const cg = el('g', {}, g); cam(cg, 540, 960, lerp(1.0, 1.03, clamp((t - 14) / 10)));
    plan(cg, t, 14.05);
    planMarks(cg, t, { tK: W_(2, 'beurteilen') - 0.3, tS: W_(2, 'mögliche') - 0.1, tC: W_(2, 'Auswirkungen') + 0.1, tF: W_(2, 'entwickeln') - 0.1 });
    const tp = 15.0; if (t > tp) { const k = ease.outBack(clamp((t - tp) / 0.55), 1.4); figure(cg, 'bp_3', lerp(1350, 930, k), 1432, 520); }
    if (wipe > 0 && wipe < 1) { const ex = lerp(-500, 1700, wipe); inkStroke(svg, [[ex + 300, -40], [ex - 300, H + 40]], { w: 120, color: C.orange, seed: 501, taper: false, filter: 'url(#marker)', opacity: 0.95 }); }
    kicker(ui, '02 · PLANUNG', t, 14.2, 23.9);
    kinetic(ui, 'BAUMSCHUTZ BEGINNT', 76, 290, t, W_(2, 'Baumschutz') - 0.1, 23.8, { size: 104 });
    const h2 = kinetic(ui, 'BEI DER PLANUNG', 76, 410, t, W_(2, 'Planung') - 0.25, 23.85, { size: 104 });
    if (h2) underline(ui, 80, 440, h2.w, t, W_(2, 'Planung') + 0.3, 23.85, 92);
  }
  // ===== Szene 3 (24.2 – 35.9): Schutz auf der Baustelle =====
  if (t >= 24.2 && t < 35.95) {
    const g = el('g', {}, stage);
    if (t < 24.9) stage.insertBefore(g, stage.firstChild);
    paperImg(g);
    const dive = ease.inOutQuint(clamp((t - 35.0) / 0.95));
    const cg = el('g', {}, g); cam(cg, lerp(540, 700, dive), lerp(860, GY + 140, dive), lerp(1.0, 1.035, clamp((t - 24.5) / 10)) * lerp(1, 3.2, dive));
    const s = stSite(t, 3);
    site(cg, t, s);
    fence(cg, s.fence, t);
    // Bauleiter + Baumpfleger mit Plan
    const tp = W_(3, 'Vorgaben') - 0.6;
    if (t > tp) { const k = ease.outBack(clamp((t - tp) / 0.6), 1.3); figure(cg, 'bl_3', lerp(-200, 790, k), GY + 4, 300); figure(cg, 'bp_3', lerp(1400, 975, k), GY + 4, 300); }
    // Ausnahme: lastverteilender Überfahrschutz
    card(ui, t, W_(3, 'Boden') - 0.9, 34.9, 560, 470, 470, 300, 2, (G) => {
      text(G, 'Ausnahme nach Abstimmung:', 584, 515, { size: 30, weight: 600, fill: C.graphite, ls: 0.02 });
      text(G, 'lastverteilender Überfahrschutz', 584, 553, { size: 34, weight: 700, fill: C.ink, ls: 0.01 });
      el('rect', { x: 590, y: 680, width: 410, height: 70, fill: '#DCCDAE', opacity: 0.5 }, G);
      hatch(G, [[590, 680], [1000, 680], [1000, 750], [590, 750]], { gap: 12, angle: -35, opacity: 0.35, seed: 760 });
      line(G, [[590, 676], [1000, 676]], { w: 3, color: '#6F8F4A', dash: '8 6' });
      [600, 690, 780, 870].forEach((x, i) => el('rect', { x, y: 650, width: 86, height: 24, fill: '#D8B98A', stroke: C.ink, 'stroke-width': 2.5, filter: 'url(#ink)' }, G));
      el('circle', { cx: 790, cy: 612, r: 36, fill: '#555', stroke: C.ink, 'stroke-width': 3 }, G); el('circle', { cx: 790, cy: 612, r: 14, fill: '#aaa' }, G);
      [-1, 0, 1].forEach((d, i) => inkStroke(G, [[790 + d * 20, 690], [790 + d * 110, 745]], { w: 3, color: C.orange, seed: 770 + i, taper: false, filter: 'url(#marker)' }));
    });
    kicker(ui, '03 · BAUPHASE', t, 24.9, 34.8);
    kinetic(ui, 'SCHÜTZEN STATT', 76, 290, t, W_(3, 'Schutzbereichen') - 0.2, 34.7, { size: 118 });
    const h2 = kinetic(ui, 'REPARIEREN', 76, 410, t, W_(3, 'Schutzbereichen') + 0.15, 34.75, { size: 118 });
    if (h2) underline(ui, 80, 440, h2.w, t, W_(3, 'Baumschutzzäunen') + 0.2, 34.75, 93);
  }
  // ===== Szene 4+5 (35.9 – 64.2): Nahaufnahme Boden =====
  if (t >= 35.9 && t < 64.25) {
    const g = el('g', {}, stage);
    const settle = ease.outCubic(clamp((t - 35.9) / 0.9));
    const shrink = ease.inOutCubic(clamp((t - 63.4) / 0.85)); // schrumpft ins Tablet (Szene 6)
    if (shrink > 0) { const tx = 820, ty = 620; g.setAttribute('transform', `translate(${lerp(0, tx, shrink)},${lerp(0, ty, shrink)}) scale(${1 - shrink * 0.97}) `); }
    paperImg(g);
    const cg = el('g', {}, g); cam(cg, lerp(690, 540, settle), lerp(1050, 960, settle), lerp(1.7, 1, settle) * (1 + 0.012 * clamp((t - 36) / 27)));
    const tPl = W_(4, 'geplant') - 0.3, tD0 = W_(4, 'erforderlich') + 0.4, tD1 = W_(4, 'Verlauf') - 0.3;
    const dig = ease.inOutCubic(clamp((t - tD0) / (tD1 - tD0)));
    const tM = W_(4, 'untersuchen') + 0.1;
    const lens = ease.inOutCubic(clamp((t - 59.2) / 0.9));
    closeSoil(cg, t, { dig, heap: dig, plannedK: K(t, tPl, 0.8), markers: K(t, tM, 1.0, x => x), trace: K(t, tM + 0.6, 1.2), orange: K(t, W_(5, 'Eingriffe'), 0.6) * (1 - lens) });
    // Figur: kniend mit Handschaufel → stehend mit Tablet
    const tSw = W_(4, 'Grundlage') - 0.6;
    if (t > tD0 - 0.8 && t < tSw) { const k = ease.outBack(clamp((t - tD0 + 0.8) / 0.5), 1.3); const dg = el('g', { transform: `rotate(${Math.sin(t * 7) * 1.6} 520 ${NG})` }, cg); figure(dg, 'bp_4', lerp(-260, 470, k), NG + 6, 270, { flip: true, label: false }); }
    if (t >= tSw && lens < 0.5) { const k = ease.outBack(clamp((t - tSw) / 0.5), 1.4); figure(cg, 'bp_1', lerp(1400, 945, k), NG + 4, 330); }
    // Dokumentation: Wurzellage auf dem Tablet
    card(ui, t, tSw + 0.3, W_(5, 'Eingriffe') - 0.3, 60, 470, 470, 290, -2, (G) => {
      text(G, 'Wurzellage', 86, 518, { size: 38, weight: 700, fill: C.ink, ls: 0.02 });
      line(G, [[300, 545], [300, 735], [400, 735], [400, 545]], { w: 2.5, color: C.graphite, dash: '8 6' });
      [0, 1, 2, 3, 4].forEach(i => { const y = 565 + i * 38; line(G, [[90, y], [500, y + 12]], { w: 7 - i, color: C.ink }); el('circle', { cx: 350, cy: y + 7, r: 10, fill: '#fff', stroke: C.orange, 'stroke-width': 3 }, G); });
      check(G, 470, 512, clamp((t - tSw - 0.9) / 0.4), 1);
    });
    // Szene 5: Lösungen
    card(ui, t, W_(5, 'geänderte') - 0.25, W_(5, 'angepasste') - 0.1, 60, 470, 470, 290, -2, (G) => {
      text(G, 'Bauablauf anpassen', 86, 518, { size: 38, weight: 700, fill: C.ink, ls: 0.02 });
      const sw = ease.inOutCubic(clamp((t - W_(5, 'geänderte') - 0.3) / 0.7));
      [['1', 0], ['2', 2], ['3', 1]].forEach(([n, to], i) => { const x = lerp(100 + i * 140, 100 + to * 140, sw), y = 600 - Math.sin(sw * Math.PI) * (i === 1 ? 40 : i === 2 ? -40 : 0); el('rect', { x, y, width: 100, height: 90, rx: 10, fill: i === 0 ? '#fff' : '#FDE9DC', stroke: C.ink, 'stroke-width': 3 }, G); text(G, n, x + 50, y + 60, { size: 46, weight: 700, fill: C.ink, anchor: 'middle' }); });
    });
    card(ui, t, W_(5, 'angepasste') + 0.15, 59.3, 60, 470, 470, 290, -2, (G) => {
      text(G, 'Leitungsführung anpassen', 86, 518, { size: 36, weight: 700, fill: C.ink, ls: 0.01 });
      const cx = 250, cy = 650; el('circle', { cx, cy, r: 70, fill: '#E3EBD8', stroke: C.ink, 'stroke-width': 3 }, G); el('circle', { cx, cy, r: 92, fill: 'none', stroke: C.orange, 'stroke-width': 5 }, G); el('circle', { cx, cy, r: 9, fill: '#8A6A4A' }, G);
      line(G, [[90, 650], [500, 650]], { w: 4, color: C.graphite, dash: '10 8' });
      const kx = K(t, W_(5, 'angepasste') + 0.2, 0.4); if (kx > 0) { inkStroke(G, [[230, 620], [270, 680]], { w: 5, seed: 990, taper: false, drawn: kx }); inkStroke(G, [[270, 620], [230, 680]], { w: 5, seed: 991, taper: false, drawn: kx }); }
      const kn = K(t, W_(5, 'Leitungsführungen') - 0.1, 0.9, ease.inOutCubic); if (kn > 0) inkStroke(G, [[90, 650], [140, 650], [170, 560], [250, 535], [330, 560], [360, 650], [500, 650]], { w: 6, color: C.orange, seed: 992, taper: false, drawn: kn, filter: 'url(#marker)' });
    });
    // Linse in den schematischen Wurzelvorhang
    if (lens > 0) {
      const R = lerp(0, 1300, lens), cx = 695, cy = 1000;
      const m = el('mask', { id: 'wv', maskUnits: 'userSpaceOnUse', x: 0, y: 0, width: W, height: H }, svg); el('circle', { cx, cy, r: Math.max(0.1, R), fill: '#fff' }, m);
      const lg = el('g', { mask: 'url(#wv)' }, g);
      paperImg(lg);
      const lc = el('g', {}, lg); cam(lc, 540, 960, lerp(1.4, 1, ease.outCubic(lens)));
      rootCurtain(lc, t, 59.6);
      figure(lc, 'bp_1', 300, NG + 4, 330, { flip: true });
      if (R > 1 && R < 1290) { inkStroke(svg, blob(cx, cy, R, R, rng(9), 40, 0.01).concat([[cx + R, cy]]), { w: 7, seed: 600, taper: false }); inkStroke(svg, blob(cx, cy, R + 14, R + 14, rng(10), 40, 0.01).concat([[cx + R + 14, cy]]), { w: 2.5, seed: 601, taper: false, color: C.orange, filter: 'url(#marker)' }); }
    }
    kicker(ui, '04 · WURZELSUCHGRABUNG', t, 36.0, 48.9);
    kinetic(ui, 'WURZELSCHONENDE', 76, 290, t, W_(4, 'Wurzelsuchgrabungen') - 0.1, 48.8, { size: 118 });
    const h2 = kinetic(ui, 'FREILEGUNG', 76, 410, t, W_(4, 'Wurzelsuchgrabungen') + 0.25, 48.85, { size: 118 });
    if (h2) underline(ui, 80, 440, h2.w, t, W_(4, 'möglichst') - 0.1, 48.85, 94);
    kicker(ui, '05 · LÖSUNGEN', t, 49.4, 63.3);
    kinetic(ui, 'EINGRIFFE MINIMIEREN', 76, 290, t, W_(5, 'Eingriffe') - 0.1, 63.2, { size: 104 });
    const h4 = kinetic(ui, 'WURZELN SCHÜTZEN', 76, 410, t, W_(5, 'vollständig') - 0.1, 63.25, { size: 104 });
    if (h4) underline(ui, 80, 440, h4.w, t, W_(5, 'Lösungen') - 0.1, 63.25, 95);
  }
  // ===== Szene 6 + 7 (63.4 – Ende): Baustelle → fertiges Gebäude → Logo =====
  if (t >= 63.4) {
    const g = el('g', {}, stage); stage.insertBefore(g, stage.firstChild);
    paperImg(g);
    const cg = el('g', {}, g);
    const zin = ease.outCubic(clamp((t - 63.4) / 1.4));
    cam(cg, 540, 860, lerp(1.12, 1.0, zin) * lerp(1, 1.03, clamp((t - 65) / 14)));
    const phase = t < 73.4 ? 6 : 7;
    const s = stSite(t, phase);
    site(cg, t, s);
    fence(cg, s.fence, t, { checks: phase === 6 ? K(t, W_(6, 'Schutzmaßnahmen') - 0.4, 1.0, x => x) : 0 });
    if (phase === 6) {
      figure(cg, 'bl_2', 785, GY + 4, 300);
      const tPh = W_(6, 'dokumentieren') - 0.2;
      figure(cg, t < tPh ? 'bp_3' : 'bp_2', 980, GY + 4, 300);
      if (t > tPh + 0.3 && t < tPh + 0.6) { const k = Math.sin(clamp((t - tPh - 0.3) / 0.3) * Math.PI); el('circle', { cx: 900, cy: GY - 250, r: 90 * k, fill: '#fff', opacity: 0.85 * k }, cg); }
      const tb = W_(6, 'beraten') - 0.1; // Gesprächsblasen
      [[740, GY - 360, 0], [990, GY - 380, 0.35]].forEach(([bx, by, d], i) => { const k = ease.outBack(clamp((t - tb - d) / 0.4), 2) * (1 - clamp((t - tb - 2.2) / 0.3)); if (k <= 0) return; const bg = el('g', { transform: `translate(${bx},${by}) scale(${k})` }, cg); el('ellipse', { cx: 0, cy: 0, rx: 60, ry: 38, fill: '#FBFAF6', stroke: C.ink, 'stroke-width': 3, filter: 'url(#ink)' }, bg); el('path', { d: i ? 'M10,34 L30,64 L-14,36' : 'M-10,34 L-30,64 L14,36', fill: '#FBFAF6', stroke: C.ink, 'stroke-width': 3 }, bg); [-22, 0, 22].forEach(x => el('circle', { cx: x, cy: 0, r: 5, fill: C.ink }, bg)); });
      card(ui, t, tPh + 0.55, 73.0, 590, 470, 440, 300, 2, (G) => {
        text(G, 'Dokumentation', 612, 515, { size: 36, weight: 700, fill: C.ink, ls: 0.02 });
        el('rect', { x: 612, y: 540, width: 180, height: 200, fill: '#F1F3F0', stroke: C.ink, 'stroke-width': 2.5 }, G); el('circle', { cx: 700, cy: 640, r: 60, fill: 'none', stroke: C.orange, 'stroke-width': 4 }, G); el('circle', { cx: 700, cy: 640, r: 44, fill: '#E3EBD8', stroke: C.ink, 'stroke-width': 2 }, G);
        el('rect', { x: 812, y: 540, width: 190, height: 130, fill: '#E9E4D8', stroke: C.ink, 'stroke-width': 2.5 }, G); inkStroke(G, [[905, 655], [905, 600]], { w: 4, seed: 801 }); el('circle', { cx: 905, cy: 585, r: 30, fill: '#cfe0b8', stroke: C.ink, 'stroke-width': 2 }, G);
        const kc = clamp((t - tPh - 1.1) / 0.4); if (kc > 0) { el('rect', { x: 812, y: 685, width: 190, height: 55, rx: 8, fill: '#FDE9DC', stroke: C.orange, 'stroke-width': 3 }, G); text(G, 'geprüft', 880, 722, { size: 34, family: 'Caveat', weight: 700, fill: C.orange, anchor: 'middle', ls: 0 }); check(G, 975, 708, kc, 0.8); }
      });
      kicker(ui, '06 · BAUBEGLEITUNG', t, 64.0, 72.9);
      kinetic(ui, 'KONTROLLIEREN', 76, 262, t, W_(6, 'begleiten') - 0.1, 72.8, { size: 88 });
      kinetic(ui, 'BERATEN', 76, 352, t, W_(6, 'beraten') - 0.1, 72.85, { size: 88 });
      const h3 = kinetic(ui, 'DOKUMENTIEREN', 76, 442, t, W_(6, 'dokumentieren') - 0.1, 72.9, { size: 88 });
      if (h3) underline(ui, 80, 466, h3.w, t, W_(6, 'dokumentieren') + 0.4, 72.9, 96);
    } else {
      const k = ease.outBack(clamp((t - 73.9) / 0.6), 1.3);
      figure(cg, 6, lerp(1300, 640, k), GY + 4, 300);
      const tn = W_(7, 'langfristig') - 0.2;
      note(cg, t, 'ggf. Nachsorge & Kontrollen', 60, 520, C.orange, tn, { size: 42, rot: -3, arrow: [[180, 20], [230, 70], [250, 120]] });
      kicker(ui, '07 · DAS ZIEL', t, 73.9, 79.1);
      kinetic(ui, 'BAUEN UND', 76, 290, t, W_(7, 'Bauvorhaben') - 0.2, 79.0, { size: 118 });
      const h2 = kinetic(ui, 'BÄUME ERHALTEN', 76, 410, t, W_(7, 'wertvolle') - 0.2, 79.05, { size: 118 });
      if (h2) underline(ui, 80, 440, h2.w, t, W_(7, 'erhalten') - 0.2, 79.05, 97);
    }
    // Logo-Seite (Kreis aus der Krone)
    const lk = ease.inOutCubic(clamp((t - 79.3) / 0.9));
    if (lk > 0) {
      const m = el('mask', { id: 'lg', maskUnits: 'userSpaceOnUse', x: 0, y: 0, width: W, height: H }, svg);
      const bcx = TREE_X, bcy = GY - 470, R = lerp(0, 1500, lk);
      el('circle', { cx: bcx, cy: bcy, r: Math.max(0.1, R), fill: '#fff' }, m);
      const lg = el('g', { mask: 'url(#lg)' }, svg);
      paperImg(lg);
      if (R < 1480) inkStroke(svg, blob(bcx, bcy, R, R, rng(12), 40, 0.01).concat([[bcx + R, bcy]]), { w: 3, seed: 900, taper: false, color: C.orange, filter: 'url(#marker)' });
      const k = ease.outBack(clamp((t - 79.7) / 0.8), 1.4), ls = 600 * k;
      if (ls > 1) { const rot = (1 - ease.outCubic(clamp((t - 79.7) / 1.2))) * -10; const gl = el('g', { transform: `rotate(${rot} 540 700)` }, lg); el('circle', { cx: 540, cy: 708, r: ls / 2 + 6, fill: '#000', opacity: 0.08, filter: 'url(#softShadow)' }, gl); image(gl, '../assets/logo-circle.png', 540 - ls / 2, 700 - ls / 2, ls, ls); }
      const tb = W_(8, 'Bischof');
      const uk = ease.outCubic(clamp((t - tb) / 0.7)); if (uk > 0) inkStroke(lg, wobble([[230, 1060], [540, 1054], [850, 1061]], rng(4), 2, 50), { w: 10, color: C.orange, seed: 901, drawn: uk, filter: 'url(#marker)' });
      const nm = 'BISCHOF BAUMPFLEGE GMBH'; let s2 = 74; while (measure(nm, s2, 'BarlowCondensed', 700, 0.04) > 900) s2 -= 2; const nw = measure(nm, s2, 'BarlowCondensed', 700, 0.04);
      kinetic(lg, nm, 540 - nw / 2, 1155, t, tb + 0.1, 99, { size: s2, ls: 0.04, stagger: 0.02 });
      const sl = 'Ihr Profi für den Baum'; const sw = measure(sl, 64, 'BarlowCondensed', 500, 0.02);
      kinetic(lg, sl, 540 - sw / 2, 1240, t, TIMING[8].subs[1][1] - 0.05, 99, { size: 64, weight: 500, ls: 0.02, fill: C.orange, stagger: 0.03 });
    }
  }
  subtitles(ui, t);
  vignette(svg);
  image(svg, `../assets/grain${fr % 4}.png`, 0, 0, W, H);
}
