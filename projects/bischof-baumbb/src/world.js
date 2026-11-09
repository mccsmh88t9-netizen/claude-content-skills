// Wiederverwendbare Welt-Bausteine: Baum, Boden, Wurzeln, Querschnitt
import { C, el, rng, smooth, wobble, inkStroke, line, hatch, blob, cloudOutline, prog, ease, lerp, clamp } from './lib.js';

// ---------------- Baum ----------------
// Krone als Verbund aus Laubballen (Kringel-Kontur, papiergefüllt, verdeckt die Äste)
function leafClump(cx, cy, rx, ry, r) {
  const pts = []; const n = Math.round((rx + ry) / 9);
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    const bump = Math.abs(Math.sin(i * 1.7 + r() * 0.6)) * 0.07 + (i % 2 ? 0.05 : 0) + (r() - .5) * 0.03;
    pts.push([cx + Math.cos(a) * rx * (1 + bump), cy + Math.sin(a) * ry * (1 + bump)]);
  }
  return pts;
}
export const TREE_CLUMPS = [
  // cx, cy, rx, ry  (relativ zum Stammfuß), Reihenfolge = Zeichenreihenfolge (hinten → vorne)
  [-150, -560, 150, 120], [150, -590, 160, 125], [0, -700, 170, 120], [-240, -450, 120, 95], [250, -460, 125, 95],
  [-90, -440, 150, 105], [100, -450, 155, 105], [0, -560, 150, 110],
];
export function drawTree(g, { x = 400, groundY = 1180, s = 1, drawn = 1, greens = 1, seed = 4, sway = 0 } = {}) {
  const r = rng(seed);
  const T = el('g', { transform: `translate(${x},${groundY}) scale(${s})` }, g);
  const ph = (a, b) => ease.outCubic(prog(drawn, a, b));
  // Stamm mit Wurzelanlauf
  const L = [[-70, 2], [-46, -18], [-36, -70], [-34, -160], [-30, -250], [-34, -320], [-70, -380], [-120, -430]];
  const R = [[74, 2], [48, -20], [37, -80], [35, -170], [31, -250], [36, -310], [80, -360], [140, -400]];
  inkStroke(T, wobble(L, r, 1.5, 30), { w: 6.5, drawn: ph(0, .22), seed: 11 });
  inkStroke(T, wobble(R, r, 1.5, 30), { w: 6.5, drawn: ph(0.02, .24), seed: 12 });
  const bark = el('g', { opacity: ph(.15, .35) }, T);
  for (let i = 0; i < 14; i++) {
    const yy = -30 - i * 22 - r() * 8, xx = -22 + r() * 40;
    line(bark, [[xx, yy], [xx + (r() - .5) * 5, yy - 14 - r() * 16]], { w: 1.8, opacity: 0.55 });
  }
  if (ph(.2, .4) > 0) hatch(T, [[10, 0], [44, -20], [33, -170], [30, -280], [12, -320], [8, -150]], { gap: 6.5, angle: -62, opacity: 0.55 * ph(.2, .4), seed: 9 });
  // Äste (verschwinden in der Krone)
  const br = [
    [[-30, -320], [-90, -400], [-170, -470], [-230, -520]],
    [[-20, -330], [-40, -440], [-60, -560]],
    [[24, -320], [70, -420], [90, -540]],
    [[34, -330], [120, -400], [200, -450], [260, -480]],
    [[0, -330], [6, -460], [10, -620]],
  ];
  const mid = 'cm' + seed + '_' + Math.round(x);
  const mk = el('mask', { id: mid, maskUnits: 'userSpaceOnUse', x: -600, y: -1000, width: 1200, height: 1100 }, T);
  el('rect', { x: -600, y: -1000, width: 1200, height: 1100, fill: '#fff' }, mk);
  if (ph(.38, .9) > 0) TREE_CLUMPS.forEach(([cx, cy, rx, ry], i) => { if (i >= 5) el('path', { d: smooth(leafClump(cx, cy, rx * .97, ry * .97, rng(500 + i)), true), fill: '#000' }, mk); });
  const brG = el('g', { mask: `url(#${mid})` }, T);
  br.forEach((b, i) => inkStroke(brG, wobble(b, r, 2.5, 25), { w: 6 - i * 0.5, drawn: ph(.2 + i * .03, .45 + i * .03), seed: 20 + i }));
  // Krone: Papierfüllungen, dann nur die äußere Silhouette + offene Innenbögen
  const crown = el('g', { transform: `rotate(${sway} 0 -330)` }, T);
  const shapes = TREE_CLUMPS.map(([cx, cy, rx, ry], i) => ({ cx, cy, rx, ry, pts: leafClump(cx, cy, rx, ry, rng(500 + i)) }));
  const inside = (q, sh, m = 0.97) => Math.pow((q[0] - sh.cx) / (sh.rx * m), 2) + Math.pow((q[1] - sh.cy) / (sh.ry * m), 2) < 1;
  const kc = ph(.38, .9);
  if (kc > 0) {
    // Schatten-Schraffur im unteren Kronenbereich
    shapes.forEach((sh, i) => {
      const { cx, cy, rx, ry } = sh;
      if (i < 5) return;
      const area = [[cx - rx * .6, cy + ry * .25], [cx + rx * .9, cy + ry * .1], [cx + rx * .7, cy + ry * .85], [cx - rx * .2, cy + ry * .95]];
      hatch(crown, area, { gap: 7.5, angle: -40, opacity: 0.4 * ph(.8, 1), seed: 70 + i });
    });
    // äußere Silhouette in Läufen
    let runIdx = 0;
    shapes.forEach((sh, i) => {
      let run = [];
      const flush = () => { if (run.length > 2) inkStroke(crown, run, { w: 4.8, drawn: ease.outCubic(prog(kc, Math.min(runIdx * 0.025, 0.4), Math.min(runIdx * 0.025, 0.4) + 0.5)), seed: 31 + runIdx, taper: true }); runIdx++; run = []; };
      const P = [...sh.pts, sh.pts[0]];
      P.forEach(q => { const hidden = shapes.some((o, j) => j !== i && inside(q, o)); if (hidden) flush(); else run.push(q); });
      flush();
    });
    // offene Innenbögen der vorderen Ballen (Volumen)
    shapes.forEach((sh, i) => {
      if (i < 5) return;
      const { cx, cy, rx, ry } = sh; const arc = [];
      for (let a = 0.35; a <= 2.6; a += 0.12) arc.push([cx + Math.cos(a) * rx * 0.98, cy + Math.sin(a) * ry * 0.98]);
      const vis = arc.filter(q => !shapes.slice(i + 1).some(o => inside(q, o, 1.0)));
      if (vis.length > 3) inkStroke(crown, vis, { w: 3.2, drawn: ph(.7 + (i - 5) * .05, .95), seed: 140 + i, opacity: 0.9 });
    });
    // Blatt-Häkchen
    const leaves = el('g', { opacity: ph(.8, 1) }, crown);
    const rr = rng(33);
    for (let j = 0; j < 22; j++) {
      const sh = shapes[Math.floor(rr() * shapes.length)];
      const a = rr() * Math.PI * 2, d = 0.3 + rr() * 0.5;
      const q = [sh.cx + Math.cos(a) * sh.rx * d, sh.cy + Math.sin(a) * sh.ry * d];
      if (shapes.slice(shapes.indexOf(sh) + 1).some(o => inside(q, o, 1.05))) continue;
      line(leaves, [[q[0] - 8, q[1] + 3], [q[0], q[1] - 4], [q[0] + 8, q[1] + 2]], { w: 2.4, color: C.ink, opacity: .7, filter: 'url(#ink)' });
    }
  }
  // Grüne Akzente: Marker-Zickzack in einzelnen Ballen
  if (greens > 0) {
    const gg = el('g', { style: 'mix-blend-mode:multiply' }, crown);
    [[2, 0.0], [4, 0.15], [6, 0.3]].forEach(([ci, dl]) => {
      const k = ease.outCubic(clamp((greens - dl) / 0.5));
      if (k <= 0) return;
      const [cx, cy, rx, ry] = TREE_CLUMPS[ci];
      const rr = rng(600 + ci);
      const zz = []; const rows = 6; const ox = rx * 0.12, oy = -ry * 0.12;
      for (let j = 0; j <= rows * k; j++) {
        const u = j / rows, yy = cy + oy - ry * .45 + u * ry * .9;
        const half = Math.sqrt(Math.max(0, 1 - Math.pow((yy - cy - oy) / (ry * .55), 2))) * rx * .48;
        zz.push([cx + ox - half + rr() * 8, yy], [cx + ox + half - rr() * 8, yy + ry * .07]);
      }
      const tg = el('g', { transform: `rotate(-24 ${cx} ${cy})` }, gg);
      if (zz.length > 2) inkStroke(tg, zz, { w: 12, color: C.green, seed: 610 + ci, taper: true, opacity: 0.78, filter: 'url(#marker)' });
    });
  }
  return T;
}

// ---------------- Wurzeln (flach, Hauptmasse in oberen Schichten) ----------------
export function drawRoots(g, { x = 430, groundY = 1130, s = 1, drawn = 1, seed = 8, spread = 1, clip = null, color = '#1B1C1A', opacity = 1, filter = 'url(#ink)' } = {}) {
  const r = rng(seed);
  const host = clip ? el('g', { 'clip-path': clip }, g) : g;
  const G = el('g', { transform: `translate(${x},${groundY}) scale(${s})` }, host);
  const ph = (a, b) => ease.outCubic(prog(drawn, a, b));
  const mains = [
    [-1, 0, 420, 70], [-1, 10, 300, 140], [-1, 20, 180, 200], [1, 0, 460, 60], [1, 12, 330, 130], [1, 22, 200, 210], [-0.2, 30, 60, 230], [0.25, 30, 80, 240],
  ];
  mains.forEach(([dir, y0, len, depth], i) => {
    const L = len * spread;
    const pts = [[dir * 30, y0 + 8]];
    for (let k = 1; k <= 6; k++) {
      const u = k / 6;
      pts.push([dir * (30 + L * u) + (r() - .5) * 18, y0 + 10 + depth * Math.pow(u, 0.75) + Math.sin(u * 5 + i) * 10]);
    }
    const d = ph(i * .04, .55 + i * .04);
    inkStroke(G, pts, { w: 7 - Math.abs(i % 3) * 1.6, drawn: d, seed: 60 + i, color, opacity, filter });
    // Feinwurzeln
    for (let f = 1; f < 5; f++) {
      const a = pts[Math.min(6, f + 1)];
      const ang = (dir >= 0 ? 0.6 : Math.PI - 0.6) + (r() - .5) * 1.4;
      const fl = 30 + r() * 50;
      const fpts = [a, [a[0] + Math.cos(ang) * fl * .5, a[1] + Math.abs(Math.sin(ang)) * fl * .5 + 6], [a[0] + Math.cos(ang) * fl, a[1] + Math.abs(Math.sin(ang)) * fl + 14]];
      inkStroke(G, wobble(fpts, r, 3, 12), { w: 2.2, drawn: ph(.5 + f * .08, .8 + f * .05), seed: 90 + i * 7 + f, opacity: 0.9 * opacity, color, filter });
    }
  });
  return G;
}

// ---------------- Bodenlinie + Gras ----------------
export function drawGround(g, { y = 1130, x0 = 30, x1 = 1050, drawn = 1, seed = 2 } = {}) {
  const r = rng(seed);
  const pts = []; for (let x = x0; x <= x1; x += 40) pts.push([x, y + Math.sin(x * 0.01) * 4 + (r() - .5) * 3]);
  inkStroke(g, pts, { w: 5, drawn, seed: 3, taper: true });
  const tufts = el('g', { opacity: clamp(drawn * 1.4 - 0.4) }, g);
  for (let x = x0 + 20; x < x0 + (x1 - x0) * drawn; x += 26 + r() * 40) {
    const n = 2 + Math.floor(r() * 3);
    for (let k = 0; k < n; k++) {
      const bx = x + k * 5, h = 10 + r() * 16, lean = (r() - .4) * 10;
      line(tufts, [[bx, y + 1], [bx + lean * .5, y - h * .6], [bx + lean, y - h]], { w: 2, color: C.ink, opacity: 0.85, filter: 'url(#ink)' });
    }
  }
}

// ---------------- Boden-Querschnitt ----------------
// zones: [{x0,x1, density 0..1 (1 = verdichtet)}]
export function drawSection(g, { y = 1130, x0 = 40, x1 = 1040, depth = 330, open = 1, zones = [{ x0: 40, x1: 1040, density: .3 }], seed = 5, clear = null } = {}) {
  const r = rng(seed);
  const D = depth * ease.outCubic(clamp(open));
  if (D < 2) return;
  // Abrisskante unten (gerissenes Papier-Profil)
  const bottom = []; for (let x = x1; x >= x0; x -= 30) bottom.push([x, y + D + Math.sin(x * 0.05) * 6 + (r() - .5) * 10]);
  const poly = [[x0, y], [x1, y], ...bottom];
  const polyD = `M${x0},${y} L${x1},${y} L${bottom[0][0]},${bottom[0][1]} ` + smooth(bottom).slice(1).replace(/^[^C]*/, '') + ` L${x0},${y} Z`;
  el('path', { d: polyD, fill: '#DCCDAE', opacity: 0.42 }, g);
  // Zonen: Schraffur + Partikel
  zones.forEach((z, zi) => {
    const zp = [[z.x0, y], [z.x1, y], [z.x1, y + D + 10], [z.x0, y + D + 10]];
    const id = 'zc' + zi + '_' + seed;
    const cp = el('clipPath', { id }, g); el('path', { d: polyD }, cp);
    const zg = el('g', { 'clip-path': `url(#${id})` }, g);
    const gap = lerp(20, 6.5, z.density);
    hatch(zg, zp, { gap, angle: -35, opacity: lerp(0.35, 0.6, z.density), seed: 100 + zi, cross: z.density > 0.6 });
    // Bodenkörner: verdichtet = dicht, klein, flach gedrückt
    const rr = rng(200 + zi);
    const count = Math.round((z.x1 - z.x0) * D / lerp(2600, 700, z.density));
    for (let i = 0; i < count; i++) {
      const px = z.x0 + rr() * (z.x1 - z.x0), py = y + 8 + rr() * (D - 12);
      const sz = lerp(9, 6, z.density) * (0.6 + rr() * 0.8);
      if (clear && Math.hypot(px - clear.x, (py - clear.y) * 1.3) < clear.r) continue;
      const p = blob(px, py, sz, sz * lerp(0.9, 0.6, z.density), rr, 7, 0.25);
      el('path', { d: smooth(p, true), fill: rr() < 0.5 ? '#CDB994' : '#E8DCC2', stroke: C.ink, 'stroke-width': 1.6, opacity: 0.9, filter: 'url(#ink)' }, zg);
    }
    // Poren (helle Lufträume) nur im lockeren Boden
    if (z.density < 0.6) {
      const pc = Math.round((z.x1 - z.x0) * D / 9000 * (1 - z.density));
      for (let i = 0; i < pc; i++) {
        const px = z.x0 + rr() * (z.x1 - z.x0), py = y + 20 + rr() * (D - 40);
        if (clear && Math.hypot(px - clear.x, (py - clear.y) * 1.3) < clear.r) continue;
        const p = blob(px, py, 14 + rr() * 10, 9 + rr() * 6, rr, 9, 0.2);
        el('path', { d: smooth(p, true), fill: C.paper, stroke: C.ink, 'stroke-width': 1.4, opacity: 0.95, filter: 'url(#ink)' }, zg);
      }
    }
  });
  const sid = 'sec' + seed; const scp = el('clipPath', { id: sid }, g); el('path', { d: polyD }, scp);
  // Schnittkante (Tusche)
  inkStroke(g, [[x0, y], ...[...bottom].reverse(), [x1, y]].slice(0), { w: 3.2, seed: 7, taper: false, opacity: 0.9 });
  inkStroke(g, [[x0, y], [x0 + 2, y + D * 0.5], [x0, y + D]], { w: 3.5, seed: 8 });
  inkStroke(g, [[x1, y], [x1 - 2, y + D * 0.5], [x1, y + D]], { w: 3.5, seed: 9 });
  return `url(#${sid})`;
}

// Druckluft-Impuls: weiche, atmende Ringe + feine orange Haarrisse
export function drawPulse(g, { x, y, k = 1, seed = 3, rings = 3, maxR = 170 } = {}) {
  const r = rng(seed);
  const G = el('g', { style: 'mix-blend-mode:multiply' }, g);
  for (let i = 0; i < rings; i++) {
    const kk = clamp(k * 1.4 - i * 0.25);
    if (kk <= 0) continue;
    const R = maxR * (0.35 + 0.65 * (i + 1) / rings) * ease.outCubic(kk);
    const p = blob(x, y, R, R * 0.72, rng(seed + i), 22, 0.07);
    inkStroke(G, [...p, p[0]], { w: 3.4 - i * 0.6, color: C.orange, seed: 300 + i, taper: false, opacity: 0.85 - i * 0.18, filter: 'url(#marker)' });
  }
  // Haarrisse
  const cracks = 9;
  for (let i = 0; i < cracks; i++) {
    const a = (i / cracks) * Math.PI * 2 + r() * 0.4;
    const len = maxR * (0.7 + r() * 0.5) * ease.outCubic(clamp(k * 1.2 - 0.15));
    if (len < 4) continue;
    const pts = [[x, y]];
    let cx = x, cy = y, ang = a;
    for (let s = 0; s < 6; s++) { ang += (r() - .5) * 0.7; cx += Math.cos(ang) * len / 6; cy += Math.sin(ang) * len / 6 * 0.72; pts.push([cx, cy]); }
    inkStroke(G, pts, { w: 2.2, color: C.orange, seed: 400 + i, opacity: 0.9, filter: 'url(#marker)' });
    // Verzweigung
    const m = pts[3]; const a2 = ang + (r() > .5 ? .8 : -.8);
    inkStroke(G, [m, [m[0] + Math.cos(a2) * len * .25, m[1] + Math.sin(a2) * len * .18]], { w: 1.6, color: C.orange, seed: 450 + i, opacity: 0.8, filter: 'url(#marker)' });
  }
}
