// Bischof Baumpflege – Bodenbelüftung. Ein Frame = render(t). Alles deterministisch.
import { C, W, H, el, rng, defs, vignette, smooth, wobble, inkStroke, line, hatch, blob, text, ease, clamp, prog, lerp, image, figure } from './lib.js';
import { drawTree, drawRoots, drawGround } from './world.js';
import TIMING from './timing.json' with { type: 'json' };

export const DURATION = 70.0;
const GY = 1060, SEC_D = 300, TREE_X = 420, TREE_S = 0.72, INJ_X = 690, INJ_Y = GY + 175;
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
function subtitles(parent, t) {
  for (const n of [1, 2, 3, 4, 5]) for (const [s, a, b] of TIMING[n].subs) {
    const t0 = a - 0.12, t1 = b + 0.25;
    if (t < t0 || t > t1 + 0.3) continue;
    const k = ease.outBack(clamp((t - t0) / 0.35), 1.6), ko = ease.inOutCubic(clamp((t - t1) / 0.25));
    const size = 34, lines = wrap(s.replace(' –', ''), size, 860);
    const bw = Math.max(...lines.map(l => measure(l, size, 'Barlow', 500))) + 56, bh = 26 + lines.length * 44;
    const y = SUB_Y + (1 - k) * 30 + ko * 16;
    const g = el('g', { opacity: clamp(k * 3) * (1 - ko) }, parent);
    const sg = el('g', { filter: 'url(#softShadow)' }, g);
    el('path', { d: `M${80 + 4},${y + 2} L${80 + bw - 3},${y} L${80 + bw + 1},${y + bh - 1} L${80 - 2},${y + bh + 2} Z`, fill: '#FBFAF6' }, sg);
    el('rect', { x: 78, y: y + 2, width: 7, height: bh - 2, fill: C.orange }, g);
    lines.forEach((l, i) => text(g, l, 80 + 30, y + 44 + i * 44, { size, family: 'Barlow', weight: 500, ls: 0 }));
  }
}

// ---------- Boden-Querschnitt (Übersicht) mit festen Partikeln ----------
const SEC = (() => {
  const r = rng(77), parts = [], pores = [];
  for (let i = 0; i < 300; i++) parts.push({ x: 50 + r() * 980, y: GY + 10 + r() * (SEC_D - 20), s: 4 + r() * 6, seed: 1000 + i, tone: r() < .5 ? '#CDB994' : '#E8DCC2' });
  for (let i = 0; i < 46; i++) pores.push({ x: 60 + r() * 960, y: GY + 24 + r() * (SEC_D - 48), rx: 12 + r() * 10, ry: 8 + r() * 5, seed: 2000 + i });
  const bottom = []; for (let x = 1040; x >= 40; x -= 30) bottom.push([x, GY + SEC_D + Math.sin(x * 0.05) * 6 + (r() - .5) * 10]);
  return { parts, pores, bottom };
})();
function compaction(x, y, st) {
  let c = x < st.compactX ? 1 : clamp(1 - (x - st.compactX) / 40);
  if (st.loosenR > 0) { const d = Math.hypot(x - INJ_X, (y - INJ_Y) * 1.25); c *= sm(st.loosenR * 0.6, st.loosenR, d); }
  return c;
}
function section(g, st) {
  const open = ease.outCubic(clamp(st.secOpen));
  if (open <= 0.01) return null;
  const D = SEC_D * open, x0 = 40, x1 = 1040;
  const bottom = SEC.bottom.map(([x, y]) => [x, GY + (y - GY) * open]);
  const polyD = `M${x0},${GY} L${x1},${GY} L${bottom[0][0]},${bottom[0][1]} ` + smooth(bottom).replace(/^M[^C]*/, '') + ` L${x0},${GY} Z`;
  const id = 'sc' + Math.round(st.t * 1000);
  const cp = el('clipPath', { id }, g); el('path', { d: polyD }, cp);
  el('path', { d: polyD, fill: '#DCCDAE', opacity: 0.42 }, g);
  const zg = el('g', { 'clip-path': `url(#${id})` }, g);
  hatch(zg, [[x0, GY], [x1, GY], [x1, GY + D], [x0, GY + D]], { gap: 19, angle: -35, opacity: 0.32, seed: 101 });
  // dichte Kreuzschraffur = Verdichtung (Maske: links bis compactX, minus Lockerungszone)
  if (st.compactX > 40) {
    const mid = 'dm' + id; const mk = el('mask', { id: mid, maskUnits: 'userSpaceOnUse', x: 0, y: 0, width: W, height: H }, zg);
    el('rect', { x: 0, y: 0, width: Math.min(1100, st.compactX), height: H, fill: '#fff' }, mk);
    if (st.compactX < 1100) el('rect', { x: st.compactX, y: 0, width: 40, height: H, fill: '#888' }, mk);
    if (st.loosenR > 0) {
      const p = blob(INJ_X, INJ_Y, st.loosenR, st.loosenR * 0.8, rng(5), 18, 0.1);
      el('path', { d: smooth(p, true), fill: '#000', filter: 'url(#marker)' }, mk);
    }
    const dg = el('g', { mask: `url(#${mid})` }, zg);
    hatch(dg, [[x0, GY], [x1, GY], [x1, GY + D], [x0, GY + D]], { gap: 7, angle: -35, opacity: 0.55, seed: 102, cross: true });
  }
  if (st.loosenR > 0) {
    const p = blob(INJ_X, INJ_Y, st.loosenR * 0.95, st.loosenR * 0.76, rng(5), 18, 0.1);
    el('path', { d: smooth(p, true), fill: C.orange, opacity: 0.13, style: 'mix-blend-mode:multiply', filter: 'url(#marker)' }, zg);
  }
  // Poren (Luft) schrumpfen bei Verdichtung
  for (const p of SEC.pores) {
    const py = GY + (p.y - GY) * open; const c = compaction(p.x, py, st); const k = 1 - 0.9 * c;
    if (k < 0.12) continue;
    const b = blob(p.x, py, p.rx * k, p.ry * k, rng(p.seed), 9, 0.2);
    el('path', { d: smooth(b, true), fill: C.paper, stroke: C.ink, 'stroke-width': 1.4, filter: 'url(#ink)' }, zg);
  }
  // Körner: flach gedrückt, dichter
  for (const p of SEC.parts) {
    const py = GY + (p.y - GY) * open; const c = compaction(p.x, py, st);
    const yy = GY + (py - GY) * (1 - 0.1 * c);
    const b = blob(p.x, yy, p.s * (1 + 0.2 * c), p.s * (0.95 - 0.35 * c), rng(p.seed), 7, 0.25);
    el('path', { d: smooth(b, true), fill: p.tone, stroke: C.ink, 'stroke-width': 1.5, filter: 'url(#ink)' }, zg);
  }
  inkStroke(g, [[x0, GY], ...[...bottom].reverse(), [x1, GY]], { w: 3.2, seed: 7, taper: false, opacity: 0.9 });
  inkStroke(g, [[x0, GY], [x0 + 2, GY + D * 0.5], [x0, GY + D]], { w: 3.5, seed: 8 });
  inkStroke(g, [[x1, GY], [x1 - 2, GY + D * 0.5], [x1, GY + D]], { w: 3.5, seed: 9 });
  return `url(#${id})`;
}
function pulseRings(g, t, starts, { x = INJ_X, y = INJ_Y, maxR = 170, persist = 0 } = {}) {
  const G = el('g', { style: 'mix-blend-mode:multiply' }, g);
  starts.forEach((t0, i) => {
    const k = (t - t0) / 1.6; if (k < 0) return;
    const kk = clamp(k);
    const R = maxR * (0.35 + 0.65 * ease.outCubic(kk)) * (0.7 + i * 0.15);
    const op = (1 - kk) * 0.9;
    if (op > 0.02) { const p = blob(x, y, R, R * 0.74, rng(40 + i), 22, 0.06); inkStroke(G, [...p, p[0]], { w: 3.4, color: C.orange, seed: 300 + i, taper: false, opacity: op, filter: 'url(#marker)' }); }
  });
  // Haarrisse wachsen mit jedem Impuls und bleiben (persist) leicht sichtbar
  const grow = starts.reduce((a, t0, i) => a + ease.outCubic(clamp((t - t0) / 0.9)) / starts.length, 0);
  const vis = Math.max(grow, persist);
  if (vis <= 0) return;
  const r = rng(3);
  for (let i = 0; i < 11; i++) {
    const a = (i / 11) * Math.PI * 2 + r() * 0.4, len = maxR * (0.7 + r() * 0.5) * vis;
    const pts = [[x, y]]; let cx = x, cy = y, ang = a;
    for (let s = 0; s < 6; s++) { ang += (r() - .5) * 0.7; cx += Math.cos(ang) * len / 6; cy += Math.sin(ang) * len / 6 * 0.72; pts.push([cx, cy]); }
    inkStroke(G, pts, { w: 2.2, color: C.orange, seed: 400 + i, opacity: 0.85, filter: 'url(#marker)' });
    const m = pts[3], a2 = ang + (r() > .5 ? .8 : -.8);
    inkStroke(G, [m, [m[0] + Math.cos(a2) * len * .25, m[1] + Math.sin(a2) * len * .18]], { w: 1.6, color: C.orange, seed: 450 + i, opacity: 0.75, filter: 'url(#marker)' });
  }
}

// ---------- Übersicht (Szenen 1, 3, 5) ----------
function overview(g, t, st) {
  st.t = t;
  // Hintergrund-Ebene: schwebende Pollen (langsamer als Vordergrund)
  const bg = el('g', { opacity: 0.5 }, g);
  const pr = rng(11);
  for (let i = 0; i < 18; i++) {
    const x = (pr() * 1200 + t * (8 + pr() * 10)) % 1200 - 60, y = 480 + pr() * 520 + Math.sin(t * 0.8 + i) * 12;
    el('circle', { cx: x, cy: y, r: 1.5 + pr() * 2, fill: C.graphite, opacity: 0.35 }, bg);
  }
  const clip = section(g, st);
  drawRoots(g, { x: TREE_X, groundY: GY, s: 0.8, clip, drawn: st.rootsDrawn ?? 1 });
  if (st.pulses) pulseRings(g, t, st.pulses, { persist: st.persist || 0 });
  drawTree(g, { x: TREE_X, groundY: GY, s: TREE_S, drawn: st.treeDrawn, greens: st.greens, sway: Math.sin(t * 1.1) * 0.6 + Math.sin(t * 2.3) * 0.25 });
  drawGround(g, { y: GY, drawn: st.groundDrawn });
}

// Lanze im Boden + über Boden
function lance(g, t, { x = INJ_X, depthK = 0, push = 0, reveal = 1 } = {}) {
  const Hl = 330, Wl = Hl * 579 / 1447;
  if (depthK > 0) {
    const tipY = GY + (INJ_Y - GY + 10) * depthK;
    inkStroke(g, [[x, GY + 2], [x, tipY]], { w: 5, seed: 5, taper: false });
    inkStroke(g, [[x - 6, tipY - 14], [x, tipY + 8], [x + 6, tipY - 14]], { w: 3, seed: 6 });
  }
  const id = 'lr' + Math.round(t * 1000);
  const cp = el('clipPath', { id }, g); el('rect', { x: x - 200, y: GY - Hl - 20, width: 400, height: (Hl + 40) * reveal, }, cp);
  image(el('g', { 'clip-path': `url(#${id})` }, g), '../assets/cut/injector_2.png', x - Wl * 0.52, GY - Hl * 0.875 + push, Wl, Hl);
  // Reveal-Strich (wird "gezeichnet")
  if (reveal > 0 && reveal < 1) inkStroke(g, [[x - 90, GY - Hl - 20 + (Hl + 40) * reveal], [x + 90, GY - Hl - 18 + (Hl + 40) * reveal]], { w: 3, seed: 7, color: C.graphite, opacity: 0.6 });
}
function cart(g, x, { flip = true, label = true, bob = 0 } = {}) {
  const Hc = 290, Wc = Hc * 1015 / 1480;
  const G = el('g', { transform: `translate(${x},${GY + 4 + bob})` }, g);
  const I = el('g', { transform: flip ? 'scale(-1,1)' : '' }, G);
  image(I, '../assets/cut/injector_1.png', -Wc / 2, -Hc, Wc, Hc);
  if (label) {
    // "VOGT" auf der weißen Gehäusefläche (Code, nie KI)
    const s = Hc / 1480; const bx = flip ? -(-Wc / 2 + 581 * s) : (-Wc / 2 + 581 * s);
    text(G, 'VOGT', bx, -Hc + 905 * s, { size: 30, weight: 700, fill: '#2B4A9E', anchor: 'middle', ls: 0.02 });
  }
}
function loaderImg(g, x, y, rot = 0, shake = 0) {
  const Hh = 250, Ww = Hh * 2003 / 1213;
  const G = el('g', { transform: `translate(${x + shake},${y}) rotate(${rot} 0 0)` }, g);
  image(G, '../assets/cut/radlader_1.png', -Ww / 2, -Hh + 8, Ww, Hh);
  return Ww;
}

// ---------- Makro (Szenen 2, 4) ----------
function grains(seed, x0, y0, w, h, cell) {
  const r = rng(seed), out = [];
  for (let yy = y0 + cell * 0.4; yy < y0 + h + cell; yy += cell * 0.86) for (let xx = x0 + ((Math.round(yy) / cell) % 2 ? cell * 0.5 : 0); xx < x0 + w + cell; xx += cell) {
    out.push({ x: xx + (r() - .5) * cell * 0.3, y: yy + (r() - .5) * cell * 0.3, r: cell * (0.36 + r() * 0.1), seed: Math.floor(r() * 1e5), tone: r() < .55 ? '#D9C49C' : '#E9DCC0' });
  }
  return out;
}
function drawGrains(g, list, { spread = 1, cx, cy, grow = 1, shade = true } = {}) {
  for (const p of list) {
    const x = cx + (p.x - cx) * spread, y = cy + (p.y - cy) * spread;
    const b = blob(x, y, p.r * grow, p.r * grow * 0.88, rng(p.seed), 11, 0.14);
    el('path', { d: smooth(b, true), fill: p.tone, stroke: C.ink, 'stroke-width': 3, filter: 'url(#ink)' }, g);
    if (shade) {
      const s = p.r * grow;
      line(g, [[x + s * .1, y + s * .55], [x + s * .5, y + s * .25]], { w: 1.6, opacity: 0.5 });
      line(g, [[x - s * .1, y + s * .62], [x + s * .58, y + s * .05]], { w: 1.6, opacity: 0.5 });
    }
  }
}
function panel(g, x, y, w, h, seed) {
  const pts = [[x, y], [x + w, y + 2], [x + w - 2, y + h], [x + 2, y + h - 1], [x, y]];
  inkStroke(g, pts, { w: 4.5, seed, taper: false });
}
function rootLine(g, x0, x1, y, seed, { hairs = 1, color = C.ink } = {}) {
  const r = rng(seed); const pts = [];
  for (let x = x0; x <= x1; x += 60) pts.push([x, y + Math.sin(x * 0.012 + seed) * 18]);
  inkStroke(g, pts, { w: 9, seed, color });
  inkStroke(g, pts.map(([a, b]) => [a, b + 6]), { w: 2, seed: seed + 1, color: C.paper, opacity: 0.6, taper: true });
  if (hairs > 0) for (let i = 1; i < pts.length - 1; i++) {
    const [a, b] = pts[i]; const up = i % 2 ? -1 : 1; const L = (22 + r() * 30) * hairs;
    inkStroke(g, [[a, b], [a + 10, b + up * L * .6], [a + 18 + r() * 8, b + up * L]], { w: 2.2, seed: seed + 10 + i, color });
  }
}
// Luftpfeil entlang Pfad
function airArrow(g, pts, k, { color = C.orange, len = 0.22, blocked = false } = {}) {
  // pts: polyline; k: 0..1 Position
  const P = (u) => { const n = pts.length - 1; const f = clamp(u) * n; const i = Math.min(n - 1, Math.floor(f)); const l = f - i; return [lerp(pts[i][0], pts[i + 1][0], l), lerp(pts[i][1], pts[i + 1][1], l)]; };
  const seg = []; for (let s = 0; s <= 8; s++) seg.push(P(k - len + len * s / 8));
  inkStroke(g, seg, { w: 7, color, seed: 700, taper: true, filter: 'url(#marker)', opacity: blocked ? 0.6 : 0.95 });
  const a = P(k), b = P(k - 0.02); const ang = Math.atan2(a[1] - b[1], a[0] - b[0]);
  const hl = 22; const l1 = [a[0] - Math.cos(ang - .5) * hl, a[1] - Math.sin(ang - .5) * hl], l2 = [a[0] - Math.cos(ang + .5) * hl, a[1] - Math.sin(ang + .5) * hl];
  inkStroke(g, [l1, a, l2], { w: 6, color, seed: 701, taper: false, filter: 'url(#marker)', opacity: blocked ? 0.6 : 0.95 });
}
function drop(g, x, y, s = 1, op = 1) {
  const d = `M${x},${y - 16 * s} C${x + 4 * s},${y - 8 * s} ${x + 11 * s},${y} ${x + 11 * s},${y + 6 * s} A${11 * s},${11 * s} 0 1 1 ${x - 11 * s},${y + 6 * s} C${x - 11 * s},${y} ${x - 4 * s},${y - 8 * s} ${x},${y - 16 * s} Z`;
  el('path', { d, fill: C.water, opacity: 0.85 * op, stroke: C.ink, 'stroke-width': 2, filter: 'url(#ink)' }, g);
}

const MAC_TOP = grains(31, 90, 540, 900, 380, 104);
const MAC_BOT = grains(32, 90, 980, 900, 380, 84);
const MAC4 = grains(33, 80, 520, 920, 860, 92);

function scene2(g, t) {
  // Panels: oben locker, unten verdichtet
  const k0 = ease.outCubic(clamp((t - 10.4) / 0.6));
  const pt = { x: 80, y: 520, w: 920, h: 410 }, pb = { x: 80, y: 960, w: 920, h: 410 };
  const comp = ease.inOutCubic(clamp((t - W_(2, 'Porenraum') - 0.1) / 0.9));
  const mk = (p, id) => { const c = el('clipPath', { id }, g); el('rect', { x: p.x, y: p.y, width: p.w, height: p.h }, c); return el('g', { 'clip-path': `url(#${id})` }, g); };
  const gt = mk(pt, 'm2t'), gb = mk(pb, 'm2b');
  el('rect', { x: pt.x, y: pt.y, width: pt.w, height: pt.h, fill: '#EFE7D6' }, gt);
  el('rect', { x: pb.x, y: pb.y, width: pb.w, height: pb.h, fill: '#EFE7D6' }, gb);
  // Wasser in Poren (oben fließt, unten Stau)
  const tW = W_(2, 'Wasserbewegung');
  rootLine(gt, 60, 1040, 760, 51, { hairs: 1 });
  drawGrains(gt, MAC_TOP, { spread: 1.18, cx: 540, cy: 725 });
  const hairs = 1 - 0.75 * ease.inOutCubic(clamp((t - W_(2, 'erschwert')) / 1.2));
  rootLine(gb, 60, 1040, 1180, 52, { hairs, color: hairs < 0.6 ? '#4a4844' : C.ink });
  drawGrains(gb, MAC_BOT, { spread: lerp(1.3, 0.98, comp), cx: 540, cy: 1165, grow: lerp(0.9, 1.12, comp) });
  // Luft: oben frei, unten blockiert
  const tA = W_(2, 'Gasaustausch') - 0.1;
  if (t > tA) {
    const pathT = [[60, 640], [250, 600], [420, 680], [600, 620], [790, 700], [1040, 650]];
    for (let i = 0; i < 2; i++) { const k = ((t - tA) * 0.32 + i * 0.5) % 1.25; if (k < 1.1) airArrow(gt, pathT, k); }
    const pathB = [[40, 1080], [200, 1060], [300, 1075]];
    const kb = clamp((t - tA - 0.2) / 0.9);
    const shake = kb >= 1 ? Math.sin((t - tA) * 40) * Math.max(0, 1 - (t - tA - 1.1) * 2) * 6 : 0;
    const gbA = el('g', { transform: `translate(${shake},0)` }, gb);
    airArrow(gbA, pathB, ease.outCubic(kb) * 0.98, { blocked: kb >= 1 });
    if (kb >= 1) { const xg = el('g', { opacity: clamp((t - tA - 1.1) * 3) }, gb); inkStroke(xg, [[318, 1050], [348, 1086]], { w: 6, seed: 9, color: C.ink }); inkStroke(xg, [[348, 1050], [318, 1086]], { w: 6, seed: 10, color: C.ink }); }
  }
  if (t > tW) {
    for (let i = 0; i < 4; i++) { const k = ((t - tW) * 0.45 + i * 0.27) % 1; const x = 180 + i * 210, y = 530 + k * 420; drop(gt, x + Math.sin(k * 9 + i) * 14, y, 1, clamp(k * 6) * clamp((1 - k) * 6)); }
    for (let i = 0; i < 5; i++) { const k = ease.outBack(clamp((t - tW - i * 0.12) / 0.5), 2.5); drop(gb, 200 + i * 150, 958 + k * 26 + Math.sin(t * 5 + i) * 1.5, 1); }
  }
  panel(g, pt.x, pt.y, pt.w, pt.h, 61); panel(g, pb.x, pb.y, pb.w, pb.h, 62);
  // Etiketten
  const lab = (s, x, y, col, t0) => { const k = ease.outBack(clamp((t - t0) / 0.4), 2); if (k <= 0) return; const gg = el('g', { transform: `translate(${x},${y}) scale(${k}) rotate(-3)` }, g); el('rect', { x: -10, y: -42, width: measure(s, 50, 'Caveat', 700) + 20, height: 56, fill: C.paper, rx: 6 }, gg); text(gg, s, 0, 0, { size: 50, family: 'Caveat', weight: 700, fill: col, ls: 0 }); };
  lab('locker', 100, 515, C.ink, 10.8); lab('verdichtet', 100, 955, C.ink, 11.2);
  return k0;
}
function scene4(g, t) {
  const p = { x: 80, y: 500, w: 920, h: 880 };
  const c = el('clipPath', { id: 'm4' }, g); el('rect', { x: p.x, y: p.y, width: p.w, height: p.h }, c);
  const G = el('g', { 'clip-path': 'url(#m4)' }, g);
  el('rect', { x: p.x, y: p.y, width: p.w, height: p.h, fill: '#EFE7D6' }, G);
  const relax = ease.inOutCubic(clamp((t - W_(4, 'Bodenstruktur') + 0.6) / 1.4));
  rootLine(G, 40, 1040, 1150, 53, { hairs: 1 });
  drawGrains(G, MAC4, { spread: lerp(0.97, 1.22, relax), cx: 540, cy: 940, grow: lerp(1.12, 0.92, relax) });
  // Injektionskanal (Mitte, von oben)
  const ch = el('g', { opacity: 0.9 }, G);
  line(ch, [[540, 500], [545, 700], [538, 900]], { w: 3, color: C.orange, dash: '10 12', filter: 'url(#marker)', opacity: 0.8 * relax });
  // Luft: Kanäle
  const tA = W_(4, 'Gasaustausch') - 0.3;
  if (t > tA) {
    const paths = [[[60, 620], [260, 680], [460, 610], [700, 700], [1040, 640]], [[60, 860], [300, 800], [520, 900], [760, 830], [1040, 900]], [[60, 1060], [280, 1010], [500, 1090], [800, 1020], [1040, 1080]]];
    paths.forEach((pp, i) => { for (let j = 0; j < 2; j++) { const k = ((t - tA) * 0.3 + j * 0.55 + i * 0.2) % 1.2; if (k < 1.1) airArrow(G, pp, k); } });
  }
  const tWt = W_(4, 'verbessern') - 0.4;
  if (t > tWt) for (let i = 0; i < 5; i++) { const k = ((t - tWt) * 0.4 + i * 0.21) % 1; drop(G, 170 + i * 175 + Math.sin(k * 8 + i) * 16, 510 + k * 860, 1, clamp(k * 6) * clamp((1 - k) * 6)); }
  // Bodenhilfsstoffe: Körnchen rieseln durch den Kanal und verteilen sich
  const tH = W_(4, 'Bodenhilfsstoffe') - 0.3;
  if (t > tH) {
    const r = rng(88);
    for (let i = 0; i < 26; i++) {
      const d = i * 0.07; const k = ease.outCubic(clamp((t - tH - d) / 1.6));
      if (k <= 0) continue;
      const tx = 540 + (r() - .5) * 520, ty = 760 + r() * 380;
      const x = lerp(540 + (r() - .5) * 10, tx, k), y = lerp(500, ty, k);
      const s = 9 + r() * 5;
      el('rect', { x: x - s / 2, y: y - s / 2, width: s, height: s, rx: 3, fill: '#8C9A5A', stroke: C.ink, 'stroke-width': 1.6, transform: `rotate(${r() * 90} ${x} ${y})`, filter: 'url(#ink)' }, G);
    }
  }
  panel(g, p.x, p.y, p.w, p.h, 63);
  // Notiz "je nach Standort" (gestrichelt)
  const tN = W_(4, 'Standort') - 0.15;
  if (t > tN) {
    const k = ease.outBack(clamp((t - tN) / 0.45), 2);
    const gg = el('g', { transform: `translate(700,560) scale(${k}) rotate(4)` }, g);
    el('rect', { x: -14, y: -50, width: 300, height: 72, rx: 10, fill: C.paper, stroke: C.orange, 'stroke-width': 3, 'stroke-dasharray': '12 9', filter: 'url(#marker)' }, gg);
    text(gg, 'je nach Standort', 4, 4, { size: 50, family: 'Caveat', weight: 700, fill: C.orange, ls: 0 });
  }
  const k = ease.outBack(clamp((t - 34.0) / 0.4), 2);
  if (k > 0) { const gg = el('g', { transform: `translate(100,495) scale(${k}) rotate(-3)` }, g); el('rect', { x: -10, y: -42, width: 200, height: 56, fill: C.paper, rx: 6 }, gg); text(gg, 'gelockert', 0, 0, { size: 50, family: 'Caveat', weight: 700, fill: C.orange, ls: 0 }); }
}

// ---------- Szenen-Inhalte ----------
function sceneOverview(root, t, which) {
  const world = el('g', {}, root);
  const st = { treeDrawn: 1, greens: 1, groundDrawn: 1, secOpen: 1, compactX: 1100, loosenR: 0 };
  if (which === 1) {
    st.groundDrawn = ease.outCubic(clamp((t + 0.35) / 1.1));
    st.treeDrawn = clamp((t + 0.1) / 2.6);
    st.greens = clamp((t - 2.5) / 0.9);
    st.secOpen = clamp((t - 3.4) / 1.0);
    st.rootsDrawn = clamp((t - 3.9) / 1.4);
    const tv = W_(1, 'verdichten') - 0.3;
    st.compactX = lerp(40, 1100, ease.inOutCubic(clamp((t - tv) / 1.0)));
    overview(world, t, st);
    // Radlader fährt ein, federt nach, presst bei "verdichten"
    const t0 = W_(1, 'Baufahrzeuge') - 0.2, t1 = t0 + 2.0;
    const kx = ease.outCubic(clamp((t - t0) / (t1 - t0)));
    const x = lerp(-420, 175, kx);
    const bounce = t > t1 ? Math.sin((t - t1) * 14) * Math.exp(-(t - t1) * 3.5) * 2.2 : (kx < 1 ? Math.sin(t * 30) * 0.4 : 0);
    const press = t > tv ? Math.sin(clamp((t - tv) / 0.5) * Math.PI) * 6 : 0;
    const lw = 412;
    if (t > t0 - 0.1) {
      // Abgaswölkchen
      const pg = el('g', {}, world);
      for (let i = 0; i < 5; i++) { const age = ((t - t0) * 0.9 + i * 0.2) % 1; const px = x - lw * 0.33 - age * 40, py = GY - 210 - age * 110; el('circle', { cx: px, cy: py, r: 8 + age * 22, fill: 'none', stroke: C.graphite, 'stroke-width': 2, opacity: (1 - age) * 0.45, filter: 'url(#pencil)' }, pg); }
      loaderImg(world, x, GY + press, bounce, kx < 1 ? Math.sin(t * 60) * 0.8 : 0);
      // Druckpfeile unter den Reifen
      if (t > tv - 0.1 && t < tv + 1.6) {
        const k = clamp((t - tv + 0.1) / 0.4) * (1 - clamp((t - tv - 1.1) / 0.5));
        [x - 120, x + 110].forEach((ax, i) => { const ag = el('g', { opacity: k }, world); inkStroke(ag, [[ax, GY + 20], [ax, GY + 20 + 60 * k]], { w: 6, seed: 120 + i, color: C.ink }); inkStroke(ag, [[ax - 14, GY + 62 * k + 4], [ax, GY + 22 + 62 * k], [ax + 14, GY + 62 * k + 4]], { w: 5, seed: 130 + i }); });
      }
    }
    // Baumpfleger tritt rechts ein und zeigt
    const tp = W_(1, 'Doch') - 0.35;
    if (t > tp) { const k = ease.outBack(clamp((t - tp) / 0.6), 1.4); figure(world, 2, lerp(1250, 900, k), GY + 4, 330); }
  }
  if (which === 3) {
    st.loosenR = 0;
    const pulses = [26.08, 26.70, 27.33];
    st.pulses = pulses;
    st.loosenR = pulses.reduce((a, p, i) => a + 62 * ease.outCubic(clamp((t - p) / 1.0)), 0);
    overview(world, t, st);
    // Gerätewagen + Baumpfleger kommen von rechts
    const tc0 = 21.45, tc1 = 23.3;
    const kc = ease.outCubic(clamp((t - tc0) / (tc1 - tc0)));
    const cx = lerp(1250, 935, kc);
    const walking = kc < 1 || (t > tc1 && t < 24.3);
    const step = walking ? Math.abs(Math.sin(t * 7)) * 6 : 0;
    cart(world, cx, { bob: kc < 1 ? Math.abs(Math.sin(t * 9)) * 2 : 0 });
    const tSwap = 24.35;
    // Lanze wird gezeichnet, dann eingestochen
    const tg = W_(3, 'gezielt');
    const depth = ease.inOutCubic(clamp((t - tg) / 0.5));
    const jolt = pulses.reduce((a, p) => a + (t > p ? Math.sin(clamp((t - p) / 0.25) * Math.PI) * -4 : 0), 0);
    if (t > 23.7) lance(world, t, { depthK: depth, push: depth * 16 + jolt, reveal: ease.inOutCubic(clamp((t - 23.7) / 0.6)) });
    if (t < tSwap) {
      // geht vom Wagen zur Lanze
      const kw = ease.inOutCubic(clamp((t - 23.4) / 0.95));
      const fx = lerp(cx + 105, 798, kw);
      const fg = el('g', { transform: `translate(${fx},${GY + 4 - step}) scale(-1,1)` }, world);
      figure(fg, 3, 0, 0, 330, { label: false });
    } else {
      const sq = 1 + Math.sin(clamp((t - tSwap) / 0.16) * Math.PI) * 0.035;
      const fg = el('g', { transform: `translate(798,${GY + 4}) scale(${2 - sq},${sq}) translate(-798,${-(GY + 4)})` }, world);
      figure(fg, 4, 798, GY + 4 + depth * 2, 330);
    }
    // Produkt-Callout
    const tl = W_(3, 'VOGT') - 0.2, tlo = 27.6;
    if (t > tl && t < tlo + 0.5) {
      const k = ease.outBack(clamp((t - tl) / 0.5), 1.8), ko = ease.inOutCubic(clamp((t - tlo) / 0.4));
      const lg = el('g', { opacity: 1 - ko, transform: `translate(${(1 - k) * 30},0)` }, world);
      inkStroke(lg, [[770, GY - 470], [800, GY - 400], [880, GY - 330]], { w: 3.2, color: C.orange, seed: 211, drawn: k, filter: 'url(#marker)' });
      inkStroke(lg, [[862, GY - 344], [882, GY - 328], [858, GY - 320]], { w: 3.2, color: C.orange, seed: 212, drawn: clamp(k * 2 - 1), filter: 'url(#marker)' });
      text(lg, 'VOGT', 745, GY - 545, { size: 50, weight: 700, fill: '#2B4A9E', ls: 0.03 });
      text(lg, 'Geo Injector Maxi', 745, GY - 497, { size: 40, weight: 600, fill: C.ink, ls: 0.01 });
    }
    // Hand-Notizen
    const ann = (s, x, y, col, t0, arrow) => { const k = ease.outBack(clamp((t - t0) / 0.45), 2); if (k <= 0) return; const gg = el('g', { transform: `translate(${x},${y}) scale(${k}) rotate(-4)` }, world); text(gg, s, 0, 0, { size: 52, family: 'Caveat', weight: 700, fill: col, ls: 0 }); if (arrow) inkStroke(gg, arrow, { w: 3, color: col, seed: 220 + x, drawn: clamp((t - t0 - 0.2) / 0.4), filter: col === C.ink ? 'url(#ink)' : 'url(#marker)' }); };
    ann('verdichtet', 70, GY - 60, C.ink, W_(3, 'verdichtete') - 0.1, [[70, 18], [80, 60], [92, 100]]);
    ann('gelockert', 760, GY + 380, C.orange, W_(3, 'gelockert') - 0.1, [[60, -50], [20, -110], [-30, -150]]);
  }
  if (which === 5) {
    st.loosenR = 186; st.pulses = []; st.persist = 0.55;
    overview(world, t, st);
    pulseRings(world, t, [], { persist: 0.5 });
    // ruhige Luftpunkte im gelockerten Bereich
    const ag = el('g', { style: 'mix-blend-mode:multiply' }, world);
    const r = rng(19);
    for (let i = 0; i < 9; i++) { const a = r() * 6.28, rr = 40 + r() * 120; const k = (t * 0.2 + r()) % 1; const x = INJ_X + Math.cos(a) * rr + k * 30, y = INJ_Y + Math.sin(a) * rr * 0.7 - k * 30; el('circle', { cx: x, cy: y, r: 5, fill: C.orange, opacity: Math.sin(k * Math.PI) * 0.8 }, ag); }
    figure(world, 6, 880, GY + 4, 340);
  }
  return world;
}

const paperImg = (g) => image(g, '../assets/paper.jpg', 0, 0, W, H);
// ---------- Kamera ----------
function cam(g, cx, cy, z) { g.setAttribute('transform', `translate(${W / 2},${H / 2}) scale(${z}) translate(${-cx},${-cy})`); }

// ---------- Hauptrender ----------
export function render(svg, t) {
  svg.innerHTML = '';
  const fr = Math.round(t * 30);
  defs(svg, 1 + Math.floor(fr / 3) % 6);
  paperImg(svg);
  const stage = el('g', {}, svg);
  const ui = el('g', {}, svg);

  // ===== Szene 1 (0 – 10.4) + Match-Cut-Zoom =====
  if (t < 10.42) {
    const g = el('g', {}, stage);
    const zk = ease.inOutQuint(clamp((t - 9.35) / 1.07));
    const z = lerp(1, 16, zk) * lerp(1, 1.02, clamp(t / 9));
    cam(g, lerp(540, 300, zk), lerp(960, GY + 150, zk), z);
    sceneOverview(g, t, 1);
    kicker(ui, '01 · DAS PROBLEM', t, 4.9, 9.1);
    const hk = kinetic(ui, 'BODENVERDICHTUNG', 76, 300, t, W_(1, 'verdichten') - 0.05, 9.0, { size: 118 });
    if (hk) underline(ui, 80, 330, hk.w, t, W_(1, 'verdichten') + 0.5, 9.0);
  }
  // ===== Szene 2 (10.4 – 21.6) =====
  if (t >= 10.4 && t < 21.62) {
    const g = el('g', {}, stage);
    const zk = ease.outCubic(clamp((t - 10.4) / 1.1));
    cam(g, lerp(330, 540, zk), lerp(1180, 945, zk), lerp(3.2, 1, zk) * (1 + 0.012 * (t - 10.4) / 11));
    scene2(g, t);
    kicker(ui, '02 · IM BODEN', t, 10.9, 20.7);
    const a = W_(2, 'Porenraum') - 0.1;
    const h1 = kinetic(ui, 'WENIGER PORENRAUM', 76, 290, t, a, 20.6, { size: 104 });
    if (h1) underline(ui, 80, 318, h1.w, t, a + 0.55, 20.6, 92);
    kinetic(ui, 'BEEINTRÄCHTIGTER', 76, 392, t, W_(2, 'Gasaustausch') - 0.1, 20.7, { size: 60, weight: 600 });
    kinetic(ui, 'GAS- UND WASSERHAUSHALT', 76, 458, t, W_(2, 'Wasserbewegung') - 0.1, 20.75, { size: 60, weight: 600 });
    const tp = 17.2; if (t > tp) { const k = ease.outBack(clamp((t - tp) / 0.55), 1.5); figure(g, 2, lerp(1300, 985, k), 1408, 380); }
  }
  // ===== Szene 3 (21.0 – 34.2), Wisch-Übergang =====
  if (t >= 21.0 && t < 34.25) {
    const wk = ease.inOutCubic(clamp((t - 21.0) / 0.62));
    const g = el('g', {}, stage);
    let mask = null;
    if (wk < 1) {
      const id = 'wipe3'; const m = el('mask', { id, maskUnits: 'userSpaceOnUse', x: 0, y: 0, width: W, height: H }, svg);
      const ex = lerp(-500, 1700, wk);
      el('path', { d: `M-10,-10 L${ex + 300},-10 L${ex - 300},${H + 10} L-10,${H + 10} Z`, fill: '#fff' }, m);
      g.setAttribute('mask', `url(#${id})`); mask = ex;
    }
    const inner = el('g', {}, g);
    paperImg(inner);
    const cg = el('g', {}, inner);
    // Lens-Zoom am Ende (Übergang zu 4)
    const lk = ease.inOutCubic(clamp((t - 33.25) / 0.95));
    cam(cg, lerp(540, INJ_X, lk), lerp(960, INJ_Y, lk), lerp(1.0, 2.2, lk) * lerp(1, 1.03, clamp((t - 21) / 12)));
    sceneOverview(cg, t, 3);
    if (mask !== null) inkStroke(svg, [[mask + 300, -40], [mask - 300, H + 40]], { w: 70, color: C.orange, seed: 501, taper: false, filter: 'url(#marker)', opacity: 0.95 });
    kicker(ui, '03 · DIE LÖSUNG', t, 21.6, 32.9);
    const a = W_(3, 'Druckluftimpulse') - 0.05;
    kinetic(ui, 'BODENBELÜFTUNG', 76, 290, t, a, 32.8, { size: 118 });
    const h2 = kinetic(ui, 'MIT DRUCKLUFT', 76, 410, t, a + 0.35, 32.85, { size: 118 });
    if (h2) underline(ui, 80, 440, h2.w, t, a + 0.8, 32.85, 93);
  }
  // ===== Szene 4 (33.3 – 45.2), Linsen-Maske aus dem Injektionspunkt =====
  if (t >= 33.3 && t < 45.25) {
    const open = ease.inOutCubic(clamp((t - 33.3) / 0.95));
    const close = ease.inOutCubic(clamp((t - 44.15) / 1.0));
    const R = lerp(0, 1250, open) * (1 - close);
    const sx = lerp(INJ_X, 540, open), sy = lerp(INJ_Y, 940, open);
    const cxp = close > 0 ? lerp(540, INJ_X, close) : sx, cyp = close > 0 ? lerp(940, INJ_Y, close) : sy;
    const id = 'lens4'; const m = el('mask', { id, maskUnits: 'userSpaceOnUse', x: 0, y: 0, width: W, height: H }, svg);
    el('circle', { cx: cxp, cy: cyp, r: Math.max(0.1, R), fill: '#fff' }, m);
    const g = el('g', { mask: `url(#${id})` }, stage);
    paperImg(g);
    const cg = el('g', {}, g);
    cam(cg, 540, 940, lerp(1.7, 1, ease.outCubic(open)) * (1 + 0.015 * clamp((t - 34) / 10)) * lerp(1, 0.6, close));
    scene4(cg, t);
    if (R > 1 && R < 1240) {
      inkStroke(svg, blob(cxp, cyp, R, R, rng(9), 40, 0.01).concat([[cxp + R, cyp]]), { w: 7, seed: 600, taper: false });
      inkStroke(svg, blob(cxp, cyp, R + 14, R + 14, rng(10), 40, 0.01).concat([[cxp + R + 14, cyp]]), { w: 2.5, seed: 601, taper: false, color: C.orange, filter: 'url(#marker)' });
    }
    kicker(ui, '04 · DIE WIRKUNG', t, 34.3, 43.8);
    const a = W_(4, 'Bodenstruktur') - 0.1;
    kinetic(ui, 'BODENSTRUKTUR', 76, 290, t, a, 43.7, { size: 118 });
    const h2 = kinetic(ui, 'VERBESSERN', 76, 410, t, a + 0.3, 43.75, { size: 118, fill: C.ink });
    if (h2) underline(ui, 80, 440, h2.w, t, a + 0.7, 43.75, 94);
    const tp = 35.1; if (t > tp && close < 0.5) { const k = ease.outBack(clamp((t - tp) / 0.55), 1.5); figure(cg, 2, lerp(1350, 1000, k), 1418, 360); }
  }
  // ===== Szene 5 (44.15 – 55.3), Kamerafahrt heraus =====
  if (t >= 44.15 && t < 55.4) {
    const g = el('g', {}, stage);
    const ok = ease.inOutCubic(clamp((t - 44.15) / 1.6));
    // Seiten-Umblättern am Ende
    const pk = ease.inOutCubic(clamp((t - 54.45) / 0.9));
    if (pk > 0) g.setAttribute('transform', `translate(0,0) matrix(${1 - pk},${-0.18 * pk},0,1,0,${0})`);
    const cg = el('g', {}, g);
    cam(cg, lerp(INJ_X, 540, ok), lerp(INJ_Y, 930, ok), lerp(2.6, 1, ok) * lerp(1, 1.05, clamp((t - 45.5) / 9)));
    sceneOverview(cg, t, 5);
    if (pk > 0) {
      const fx = W * (1 - pk);
      const sh = el('linearGradient', { id: 'pshade', x1: 0, x2: 1, y1: 0, y2: 0 }, svg);
      el('stop', { offset: 0, 'stop-color': '#000', 'stop-opacity': 0 }, sh); el('stop', { offset: 1, 'stop-color': '#3a2f1c', 'stop-opacity': 0.25 }, sh);
      el('rect', { x: 0, y: 0, width: W, height: H, fill: 'url(#pshade)', transform: `matrix(${1 - pk},${-0.18 * pk},0,1,0,0)` }, g);
      el('rect', { x: fx, y: -200, width: 60, height: H + 400, fill: '#000', opacity: 0.12 * Math.sin(pk * Math.PI), filter: 'url(#softShadow)' }, svg);
      if (pk < 0.98) inkStroke(svg, [[fx, -0.18 * pk * W], [fx + 2, H * 0.5 - 0.18 * pk * W], [fx, H - 0.18 * pk * W]], { w: 4, seed: 777, taper: false });
    }
    kicker(ui, '05 · DAS ZIEL', t, 45.4, 54.0);
    kinetic(ui, 'GESUNDER BODEN', 76, 290, t, W_(5, 'funktionsfähiger') - 0.05, 53.9, { size: 118 });
    const h2 = kinetic(ui, 'BESSERE WACHSTUMSBEDINGUNGEN', 76, 376, t, W_(5, 'langfristige') - 0.6, 53.95, { size: 62, weight: 600, fill: C.ink });
    if (h2) underline(ui, 80, 404, h2.w, t, W_(5, 'Entwicklung') - 0.2, 53.95, 95);
  }
  // ===== Szene 6 (54.45 – 70): Rückenansicht → Logo → Partner =====
  if (t >= 54.45) {
    const g = el('g', {}, stage);
    // unter die umblätternde Seite legen
    stage.insertBefore(g, stage.firstChild);
    paperImg(g);
    const cg = el('g', {}, g);
    const zb = lerp(1.14, 1.0, ease.outCubic(clamp((t - 54.6) / 4)));
    cam(cg, 520, 1000, zb);
    // großer Baum rechts (gleiche Zeichnung wie im ganzen Film)
    const tr = el('g', {}, cg);
    drawTree(tr, { x: 860, groundY: 1520, s: 1.95, sway: Math.sin(t * 1.1) * 0.4 });
    drawGround(tr, { y: 1520, x0: -60, x1: 1140 });
    figure(cg, 5, 430, 1524, 1180);
    // Kreis-Maske aus dem Rückendruck → Logo-Seite
    const lk = ease.inOutCubic(clamp((t - 57.9) / 0.9));
    if (lk > 0) {
      const id = 'logo6'; const m = el('mask', { id, maskUnits: 'userSpaceOnUse', x: 0, y: 0, width: W, height: H }, svg);
      const bcx = 430, bcy = 610; const R = lerp(0, 1400, lk);
      el('circle', { cx: bcx, cy: bcy, r: Math.max(0.1, R), fill: '#fff' }, m);
      const lg = el('g', { mask: `url(#${id})` }, svg);
      paperImg(lg);
      if (R < 1380) inkStroke(svg, blob(bcx, bcy, R, R, rng(12), 40, 0.01).concat([[bcx + R, bcy]]), { w: 3, seed: 900, taper: false, color: C.orange, filter: 'url(#marker)' });
      // Logo
      const k = ease.outBack(clamp((t - 58.3) / 0.8), 1.4);
      const ls = 560 * k;
      if (ls > 1) {
        const rot = (1 - ease.outCubic(clamp((t - 58.3) / 1.2))) * -10;
        const gl = el('g', { transform: `rotate(${rot} 540 640)` }, lg);
        el('circle', { cx: 540, cy: 648, r: ls / 2 + 6, fill: '#000', opacity: 0.08, filter: 'url(#softShadow)' }, gl);
        image(gl, '../assets/logo-circle.png', 540 - ls / 2, 640 - ls / 2, ls, ls);
      }
      const tb = W_(6, 'Bischof');
      const uk = ease.outCubic(clamp((t - tb) / 0.7));
      if (uk > 0) inkStroke(lg, wobble([[230, 990], [540, 984], [850, 991]], rng(4), 2, 50), { w: 10, color: C.orange, seed: 901, drawn: uk, filter: 'url(#marker)' });
      // Firmenname zentriert, gestaffelt
      const nm = 'BISCHOF BAUMPFLEGE GMBH'; let s = 74; while (measure(nm, s, 'BarlowCondensed', 700, 0.04) > 900) s -= 2;
      const nw = measure(nm, s, 'BarlowCondensed', 700, 0.04);
      kinetic(lg, nm, 540 - nw / 2, 1085, t, tb + 0.1, 99, { size: s, ls: 0.04, stagger: 0.02 });
      const sl = 'Ihr Profi für den Baum'; const sw = measure(sl, 64, 'BarlowCondensed', 500, 0.02);
      kinetic(lg, sl, 540 - sw / 2, 1168, t, 60.6, 99, { size: 64, weight: 500, ls: 0.02, fill: C.orange, stagger: 0.03 });
      // Partner terrafit
      const pk2 = ease.outCubic(clamp((t - 63.7) / 0.6));
      if (pk2 > 0) {
        const pg = el('g', { opacity: clamp(pk2 * 2), transform: `translate(0,${(1 - pk2) * 30})` }, lg);
        const kt = 'PARTNER VON'; const kw = measure(kt, 30, 'BarlowCondensed', 600, 0.24);
        text(pg, kt, 540 - kw / 2, 1262, { size: 30, weight: 600, fill: C.graphite, ls: 0.24 });
        inkStroke(pg, [[540 - kw / 2 - 70, 1252], [540 - kw / 2 - 20, 1251]], { w: 3, color: C.graphite, seed: 910, taper: false });
        inkStroke(pg, [[540 + kw / 2 + 20, 1252], [540 + kw / 2 + 70, 1251]], { w: 3, color: C.graphite, seed: 911, taper: false });
        const tw = 400 * lerp(0.92, 1, ease.outBack(pk2)), th = tw * 439 / 705;
        image(pg, '../assets/terrafit.png', 540 - tw / 2, 1300, tw, th);
      }
    }
  }
  subtitles(ui, t);
  vignette(svg);
  // feines, wechselndes Korn
  image(svg, `../assets/grain${fr % 4}.png`, 0, 0, W, H);
}

export function grainDefs(svg) {}
