// Bischof Baumpflege – Skizzen-Reise: gemeinsame Zeichen-Bibliothek
// Alles deterministisch (Seeds), damit jedes Frame reproduzierbar ist.

export const C = {
  paper: '#F4F2EC',      // Knochenweiß (Markenfarbe)
  paperShade: '#E9E4D8',
  ink: '#1B1C1A',        // Tusche
  graphite: '#6B6862',   // Bleistift
  orange: '#F26B1D',     // Schnittschutz (Akzent)
  green: '#7DC243',      // Fuhrpark-Grün
  greenDeep: '#12341D',  // Logo-Grün
  water: '#3E7CC0',      // Wasser
  soil: '#B9A88C',
};

export const W = 1080, H = 1920;
const NS = 'http://www.w3.org/2000/svg';

export function rng(seed) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; return ((s >>> 0) % 1e6) / 1e6; };
}

export function el(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

// ---------- Easing ----------
export const ease = {
  outCubic: t => 1 - Math.pow(1 - t, 3),
  inOutCubic: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  outBack: (t, s = 1.7) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
  outElastic: t => t === 0 || t === 1 ? t : Math.pow(2, -9 * t) * Math.sin((t * 10 - .75) * (2 * Math.PI) / 3.2) + 1,
  inOutQuint: t => t < .5 ? 16 * t ** 5 : 1 - Math.pow(-2 * t + 2, 5) / 2,
};
export const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const prog = (t, a, b) => clamp((t - a) / (b - a));
export const lerp = (a, b, k) => a + (b - a) * k;

// ---------- Defs: Papier, Tusche-Rauheit, Korn ----------
export function defs(svg, boilSeed = 1) {
  const d = el('defs', {}, svg);
  // Papierfaser
  const fp = el('filter', { id: 'paperTex', x: 0, y: 0, width: '100%', height: '100%' }, d);
  el('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.75', numOctaves: 2, seed: 7, result: 'fib' }, fp);
  el('feColorMatrix', { in: 'fib', type: 'matrix', values: '0 0 0 0 0.40  0 0 0 0 0.36  0 0 0 0 0.28  0 0 0 -1.6 0.92', result: 'fibA' }, fp);
  el('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.006', numOctaves: 4, seed: 3, result: 'cloud' }, fp);
  el('feColorMatrix', { in: 'cloud', type: 'matrix', values: '0 0 0 0 0.62  0 0 0 0 0.54  0 0 0 0 0.40  0 0 0 -1.1 0.62', result: 'cloudA' }, fp);
  const m = el('feMerge', {}, fp); el('feMergeNode', { in: 'cloudA' }, m); el('feMergeNode', { in: 'fibA' }, m);
  // Tusche: leichtes Zittern ("boil"), Seed wechselt alle 3 Frames
  const fi = el('filter', { id: 'ink', x: '-5%', y: '-5%', width: '110%', height: '110%' }, d);
  el('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.035', numOctaves: 2, seed: boilSeed, result: 'n' }, fi);
  el('feDisplacementMap', { in: 'SourceGraphic', in2: 'n', scale: 3.2, xChannelSelector: 'R', yChannelSelector: 'G' }, fi);
  // Bleistift: körniger, ausgefranster Strich
  const fg = el('filter', { id: 'pencil', x: '-5%', y: '-5%', width: '110%', height: '110%' }, d);
  el('feTurbulence', { type: 'fractalNoise', baseFrequency: '1.4', numOctaves: 1, seed: boilSeed + 11, result: 'g' }, fg);
  el('feColorMatrix', { in: 'g', type: 'matrix', values: '0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.4 1.75', result: 'ga' }, fg);
  el('feComposite', { in: 'SourceGraphic', in2: 'ga', operator: 'in', result: 'grain' }, fg);
  el('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.05', numOctaves: 1, seed: boilSeed + 3, result: 'n2' }, fg);
  el('feDisplacementMap', { in: 'grain', in2: 'n2', scale: 2.4, xChannelSelector: 'R', yChannelSelector: 'G' }, fg);
  // Marker-Akzent (Orange/Grün): leicht unregelmäßige Kante + Multiply-Look
  const fm = el('filter', { id: 'marker', x: '-5%', y: '-5%', width: '110%', height: '110%' }, d);
  el('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.6', numOctaves: 2, seed: 5, result: 'mk' }, fm);
  el('feColorMatrix', { in: 'mk', type: 'matrix', values: '0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -0.9 1.25', result: 'mka' }, fm);
  el('feComposite', { in: 'SourceGraphic', in2: 'mka', operator: 'in', result: 'mm' }, fm);
  el('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.04', numOctaves: 1, seed: boilSeed + 5, result: 'n3' }, fm);
  el('feDisplacementMap', { in: 'mm', in2: 'n3', scale: 4, xChannelSelector: 'R', yChannelSelector: 'G' }, fm);
  // weicher Papierschatten unter Etiketten
  const fs = el('filter', { id: 'softShadow', x: '-20%', y: '-20%', width: '140%', height: '160%' }, d);
  el('feGaussianBlur', { in: 'SourceAlpha', stdDeviation: 10 }, fs);
  el('feOffset', { dy: 8, result: 'ob' }, fs);
  el('feComponentTransfer', { in: 'ob', result: 'oc' }, fs).appendChild((() => { const f = document.createElementNS(NS, 'feFuncA'); f.setAttribute('type', 'linear'); f.setAttribute('slope', '0.18'); return f; })());
  const sm = el('feMerge', {}, fs); el('feMergeNode', { in: 'oc' }, sm); el('feMergeNode', { in: 'SourceGraphic' }, sm);
  // wechselndes Filmkorn (4 Varianten)
  for (let i = 0; i < 4; i++) {
    const fg2 = el('filter', { id: 'grain' + i, x: 0, y: 0, width: '100%', height: '100%' }, d);
    el('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.85', numOctaves: 1, seed: 30 + i, result: 'g' }, fg2);
    el('feColorMatrix', { in: 'g', type: 'matrix', values: '0 0 0 0 0.2  0 0 0 0 0.18  0 0 0 0 0.15  0 0 0 -1.4 1.1' }, fg2);
  }
  // Vignette
  const rg = el('radialGradient', { id: 'vig', cx: '50%', cy: '45%', r: '75%' }, d);
  el('stop', { offset: '60%', 'stop-color': '#000', 'stop-opacity': 0 }, rg);
  el('stop', { offset: '100%', 'stop-color': '#3a2f1c', 'stop-opacity': 0.16 }, rg);
  return d;
}

export function paper(svg) {
  el('rect', { x: 0, y: 0, width: W, height: H, fill: C.paper }, svg);
  el('rect', { x: 0, y: 0, width: W, height: H, filter: 'url(#paperTex)', opacity: 0.32 }, svg);
}
export function vignette(svg) {
  el('rect', { x: 0, y: 0, width: W, height: H, fill: 'url(#vig)' }, svg);
}

// ---------- Hand-gezeichnete Linien ----------
// Catmull-Rom → Bezier
export function smooth(pts, closed = false) {
  if (pts.length < 2) return '';
  const p = closed ? [pts[pts.length - 1], ...pts, pts[0], pts[1]] : [pts[0], ...pts, pts[pts.length - 1]];
  let d = `M${p[1][0].toFixed(1)},${p[1][1].toFixed(1)}`;
  for (let i = 1; i < p.length - 2; i++) {
    const [x0, y0] = p[i - 1], [x1, y1] = p[i], [x2, y2] = p[i + 1], [x3, y3] = p[i + 2];
    d += `C${(x1 + (x2 - x0) / 6).toFixed(1)},${(y1 + (y2 - y0) / 6).toFixed(1)} ${(x2 - (x3 - x1) / 6).toFixed(1)},${(y2 - (y3 - y1) / 6).toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)}`;
  }
  return closed ? d + 'Z' : d;
}

// Linie mit Handzittern
export function wobble(pts, r, amp = 2, step = 18) {
  const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const [ax, ay] = pts[i], [bx, by] = pts[i + 1];
    const L = Math.hypot(bx - ax, by - ay), n = Math.max(1, Math.round(L / step));
    for (let j = 0; j < n; j++) {
      const k = j / n;
      out.push([ax + (bx - ax) * k + (r() - .5) * amp, ay + (by - ay) * k + (r() - .5) * amp]);
    }
  }
  out.push(pts[pts.length - 1]);
  return out;
}

// Tuschestrich mit variabler Strichstärke (gefüllte Kontur), optional teilweise gezeichnet
export function inkStroke(parent, pts, { w = 4.5, color = C.ink, taper = true, drawn = 1, seed = 1, opacity = 1, filter = 'url(#ink)' } = {}) {
  if (drawn <= 0 || pts.length < 2) return null;
  // resample entlang Länge
  const seg = []; let L = 0;
  for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(l); L += l; }
  const N = Math.max(4, Math.round(L / 6));
  const res = [];
  for (let s = 0; s <= N; s++) {
    let target = (s / N) * L * drawn, i = 0;
    while (i < seg.length - 1 && target > seg[i]) { target -= seg[i]; i++; }
    const k = seg[i] ? target / seg[i] : 0;
    res.push([lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k)]);
  }
  const r = rng(seed);
  const left = [], right = [];
  for (let i = 0; i < res.length; i++) {
    const a = res[Math.max(0, i - 1)], b = res[Math.min(res.length - 1, i + 1)];
    let nx = -(b[1] - a[1]), ny = b[0] - a[0]; const nl = Math.hypot(nx, ny) || 1; nx /= nl; ny /= nl;
    const u = i / (res.length - 1);
    let tw = taper ? Math.pow(Math.sin(Math.PI * clamp(u * 0.92 + 0.04)), 0.45) : 1;
    tw *= 0.85 + 0.3 * Math.sin(u * 9 + seed) * 0.5 + (r() - .5) * 0.12;
    const hw = (w / 2) * tw;
    left.push([res[i][0] + nx * hw, res[i][1] + ny * hw]);
    right.push([res[i][0] - nx * hw, res[i][1] - ny * hw]);
  }
  const d = smooth(left) + 'L' + smooth(right.reverse()).slice(1) + 'Z';
  return el('path', { d, fill: color, opacity, filter }, parent);
}

// Einfacher Pfad-Strich (für Schraffur/Bleistift)
export function line(parent, pts, { w = 1.4, color = C.graphite, opacity = 0.7, filter = 'url(#pencil)', drawn = 1, cap = 'round', dash } = {}) {
  const d = smooth(pts);
  const p = el('path', { d, fill: 'none', stroke: color, 'stroke-width': w, 'stroke-linecap': cap, 'stroke-linejoin': 'round', opacity }, parent);
  if (filter) p.setAttribute('filter', filter);
  if (drawn < 1) { p.setAttribute('pathLength', 1000); p.setAttribute('stroke-dasharray', `${drawn * 1000} 1000`); }
  if (dash) p.setAttribute('stroke-dasharray', dash);
  return p;
}

// Bleistift-Schraffur in einem Polygon (Clip), Dichte = Abstand
export let _clipId = 0;
export function hatch(parent, poly, { gap = 14, angle = -38, w = 1.5, color = C.graphite, opacity = 0.55, seed = 1, cross = false, jitter = 1.2 } = {}) {
  const id = 'hc' + (++_clipId);
  const cp = el('clipPath', { id }, parent);
  el('path', { d: smooth(poly, true) }, cp);
  const g = el('g', { 'clip-path': `url(#${id})`, filter: 'url(#pencil)', opacity }, parent);
  const xs = poly.map(p => p[0]), ys = poly.map(p => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  const R = Math.hypot(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) / 2 + 20;
  const r = rng(seed);
  const pass = (ang) => {
    const a = ang * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
    for (let o = -R; o <= R; o += gap * (0.8 + r() * 0.4)) {
      const x1 = cx + ca * -R - sa * o, y1 = cy + sa * -R + ca * o;
      const x2 = cx + ca * R - sa * o, y2 = cy + sa * R + ca * o;
      const pts = wobble([[x1, y1], [x2, y2]], r, jitter, 40);
      el('path', { d: smooth(pts), stroke: color, 'stroke-width': w * (0.75 + r() * 0.5), fill: 'none', 'stroke-linecap': 'round' }, g);
    }
  };
  pass(angle); if (cross) pass(angle + 78);
  return g;
}

// Unregelmäßiger Blob (Krone, Partikel, Poren)
export function blob(cx, cy, rx, ry, r, n = 14, irr = 0.18) {
  const pts = [];
  const ph = r() * 6;
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    const k = 1 + (r() - .5) * irr * 2 + Math.sin(a * 3 + ph) * irr * 0.5;
    pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]);
  }
  return pts;
}

// Kringel-Kontur (Scribble-Wolke) für Baumkrone
export function cloudOutline(cx, cy, rx, ry, r, lobes = 11) {
  const pts = [];
  for (let i = 0; i <= lobes; i++) {
    const a0 = (i / lobes) * Math.PI * 2 - Math.PI / 2;
    const a1 = ((i + 1) / lobes) * Math.PI * 2 - Math.PI / 2;
    const bulge = 1.12 + r() * 0.12;
    for (let s = 0; s < 6; s++) {
      const u = s / 6, a = lerp(a0, a1, u);
      const k = 1 + Math.sin(u * Math.PI) * (bulge - 1) + (r() - .5) * 0.02;
      pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]);
    }
  }
  return pts;
}

// Text
export function text(parent, str, x, y, { size = 100, family = 'BarlowCondensed', weight = 700, fill = C.ink, ls = 0.02, anchor = 'start', opacity = 1 } = {}) {
  const t = el('text', { x, y, 'font-family': family, 'font-weight': weight, 'font-size': size, fill, 'letter-spacing': `${ls}em`, 'text-anchor': anchor, opacity }, parent);
  t.textContent = str;
  return t;
}

// ---------- Bild-Assets (KI-Zeichnungen, freigestellt) ----------
export const POSES = { 1: [290, 664], 2: [410, 667], 3: [432, 669], 4: [440, 678], 5: [306, 736], 6: [358, 729], 7: [727, 940], 8: [551, 1240] };
// Druckfläche [x, y, breite, höhe] im Freisteller (Brust links bzw. Rücken)
export const PATCH = { 1: [168, 176, 46, 24], 2: [274, 180, 46, 24], 5: [86, 205, 134, 60], 6: [176, 200, 48, 25] };
export function image(parent, href, x, y, w, h, extra = {}) {
  return el('image', { href, x, y, width: w, height: h, preserveAspectRatio: 'none', ...extra }, parent);
}
// Figur: Füße (Bildunterkante minus Rand) auf (fx, fy); h = sichtbare Körperhöhe
export function figure(parent, pose, fx, fy, h, { flip = false, anchorX = 0.5, label = true } = {}) {
  const [pw, ph] = POSES[pose];
  const s = h / (ph - 24);
  const w = pw * s, H = ph * s;
  const g = el('g', { transform: `translate(${fx},${fy}) ${flip ? 'scale(-1,1)' : ''}` }, parent);
  image(g, `../assets/cut/pose_${pose}.png`, -w * anchorX, -H + 12 * s, w, H);
  if (label && PATCH[pose]) {
    const [px, py, qw, qh] = PATCH[pose];
    const X = -w * anchorX + px * s, Y = -H + 12 * s + py * s, PW = qw * s, PH = qh * s;
    const lg = el('g', { transform: flip ? `translate(${X + PW / 2},0) scale(-1,1) translate(${-(X + PW / 2)},0)` : '' }, g);
    const big = pose === 5;
    const fs1 = PH * (big ? 0.42 : 0.44);
    const col = '#F7DC2E';
    const t1 = el('text', { x: X + PW / 2, y: Y + PH * 0.45, 'font-family': 'BarlowCondensed', 'font-weight': 700, 'font-size': fs1, fill: col, 'text-anchor': 'middle', 'letter-spacing': '0.05em', opacity: 0.95 }, lg);
    t1.textContent = 'BISCHOF';
    const t2 = el('text', { x: X + PW / 2, y: Y + PH * 0.9, 'font-family': 'BarlowCondensed', 'font-weight': 600, 'font-size': fs1 * 0.8, fill: col, 'text-anchor': 'middle', 'letter-spacing': '0.07em', opacity: 0.95 }, lg);
    t2.textContent = 'BAUMPFLEGE';
  }
  return { g, s, w, H };
}
