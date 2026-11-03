"""Render-Engine Recruiting-Video Bischof Baumpflege.
Footage-Dekodierung (HLG->SDR, LUT), Kamera, Typo, Übergänge, Finish."""
import os, subprocess, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W, H, FPS = 1080, 1920, 30
BEAT = 15  # 120 BPM -> 15 Frames pro Schlag
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LUT = os.path.join(HERE, 'nordic.cube')
CACHE = os.path.join(HERE, 'cache'); os.makedirs(CACHE, exist_ok=True)
FONT = {
    'anton': os.path.join(ROOT, 'fonts/Anton-Regular.ttf'),
    'bc6': os.path.join(ROOT, 'fonts/BarlowCondensed-SemiBold.ttf'),
    'bc8': os.path.join(ROOT, 'fonts/BarlowCondensed-ExtraBold.ttf'),
    'bc9': os.path.join(ROOT, 'fonts/BarlowCondensed-Black.ttf'),
}
FOREST = (18, 52, 29); DEEP = (11, 31, 18); FLEET = (125, 194, 67); BONE = (244, 242, 236)
TM_HLG = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
          "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")

# ---------------------------------------------------------------- Footage
def decode(name, t0, dur, cx=0.5, cy=0.5, zoom=1.0, minterp=False, size=(W, H)):
    """Dekodiert einen Clipausschnitt als RGB-Array (n,H,W,3), gegradet.
    zoom/cx/cy wählen einen 9:16-Ausschnitt aus dem (bereits hochkant gedrehten) Quellbild."""
    key = hashlib.md5(repr((name, t0, dur, cx, cy, zoom, minterp, size, os.path.getmtime(LUT))).encode()).hexdigest()[:12]
    cp = os.path.join(CACHE, f'dec_{name}_{key}.npy')
    if os.path.exists(cp):
        return np.load(cp, mmap_mode='r')
    vf = []
    if name.startswith('IMG'):
        vf.append(TM_HLG)
    if zoom != 1.0:
        w = 1 / zoom
        x = min(max(cx - w / 2, 0), 1 - w); y = min(max(cy - w / 2, 0), 1 - w)
        vf.append(f"crop=trunc(iw*{w:.5f}/2)*2:trunc(ih*{w:.5f}/2)*2:iw*{x:.5f}:ih*{y:.5f}")
    vf.append(f"scale={size[0]}:{size[1]}:flags=lanczos")
    vf.append(f"lut3d={LUT}")
    if minterp:
        vf.append("minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1")
    vf.append("format=rgb24")
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-t', f'{dur:.3f}',
           '-i', os.path.join(ROOT, 'footage', name if '.' in name else name + '.mov'), '-vf', ','.join(vf),
           '-f', 'rawvideo', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    fs = size[0] * size[1] * 3; n = len(raw) // fs
    arr = np.frombuffer(raw[:n * fs], np.uint8).reshape(n, size[1], size[0], 3)
    np.save(cp, arr)
    return np.load(cp, mmap_mode='r')

def load_still(fname, box=None, size=None):
    """Still laden (EXIF-Drehung), optional Ausschnitt box=(l,t,r,b) normiert, LUT anwenden."""
    im = ImageOps.exif_transpose(Image.open(os.path.join(ROOT, 'stills', fname))).convert('RGB')
    if box:
        l, t, r, b = box
        im = im.crop((int(l * im.width), int(t * im.height), int(r * im.width), int(b * im.height)))
    if size:
        im = im.resize(size, Image.LANCZOS)
    tmp = os.path.join(CACHE, 'still_tmp.png'); im.save(tmp)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', tmp, '-vf', f'lut3d={LUT},format=rgb24',
                          '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(im.height, im.width, 3).copy()

def sample(frames, f):
    """Frame mit gebrochenem Index (Überblendung für Zeitlupe)."""
    f = min(max(f, 0), len(frames) - 1)
    i = int(f); a = f - i
    if a < 0.02 or i + 1 >= len(frames):
        return np.asarray(frames[i])
    if a > 0.98:
        return np.asarray(frames[i + 1])
    return (np.asarray(frames[i]) * (1 - a) + np.asarray(frames[i + 1]) * a).astype(np.uint8)

def view(img, z=1.0, cx=0.5, cy=0.5, dx=0.0, dy=0.0, rot=0.0):
    """Virtuelle Kamera: Ausschnitt mit Zoom z (>=1) um (cx,cy), Versatz dx/dy in Ausgabe-Pixeln."""
    if not isinstance(img, Image.Image):
        img = Image.fromarray(np.ascontiguousarray(img))
    w, h = img.size
    s = min(w / W, h / H) / z          # 'cover' für beliebige Seitenverhältnisse
    vw, vh = W * s, H * s
    left = cx * w - vw / 2 + dx * s
    top = cy * h - vh / 2 + dy * s
    left = min(max(left, 0), w - vw); top = min(max(top, 0), h - vh)
    if rot:
        c, sn = math.cos(rot), math.sin(rot)
        ox, oy = W / 2, H / 2
        a, b = s * c, -s * sn; d, e = s * sn, s * c
        cxs, cys = left + vw / 2, top + vh / 2
        data = (a, b, cxs - a * ox - b * oy, d, e, cys - d * ox - e * oy)
    else:
        data = (s, 0, left, 0, s, top)
    return img.transform((W, H), Image.AFFINE, data, resample=Image.BICUBIC)

def whip(img, d0, d1, axis=1, n=None):
    """Whip-Pan: Bild um d0..d1 Pixel verschieben (umlaufend) und Bewegungsunschärfe mitteln."""
    a = np.asarray(img)
    n = n or int(max(6, min(40, abs(d1 - d0) / 18)))
    acc = np.zeros(a.shape, np.float32)
    for k in range(n):
        acc += np.roll(a, int(round(lerp(d0, d1, k / max(n - 1, 1)))), axis=axis)
    return Image.fromarray((acc / n).astype(np.uint8))

def mblur(render, n, **span):
    """Bewegungsunschärfe: render(k) für k in [0,1] n-mal mitteln."""
    acc = None
    for k in range(n):
        a = np.asarray(render(k / max(n - 1, 1)), np.float32)
        acc = a if acc is None else acc + a
    return Image.fromarray((acc / n).astype(np.uint8))

def ease_in(u): return u * u
def ease_out(u): return 1 - (1 - u) ** 3
def ease_io(u): return 3 * u * u - 2 * u * u * u
def lerp(a, b, u): return a + (b - a) * u
def clamp01(u): return min(max(u, 0.0), 1.0)

def shake(i, hits, amp=10, decay=6):
    """Kamera-Ruck nach Einschlägen (Frames in hits)."""
    dx = dy = 0.0
    for h0 in hits:
        d = i - h0
        if 0 <= d < decay * 2:
            e = amp * math.exp(-d / decay * 2.2)
            dx += e * math.sin(d * 2.7 + h0); dy += e * math.cos(d * 3.1 + h0 * 0.7)
    return dx, dy

# ---------------------------------------------------------------- Finish
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H * 0.48) / (H * 0.60)) ** 2)
VIGN = 1 - 0.42 * np.clip((_r - 0.55) / 0.55, 0, 1) ** 1.6
TOPDARK = 1 - 0.38 * np.clip(1 - _yy / 420, 0, 1) ** 1.8
BGMUL = (VIGN * TOPDARK)[..., None].astype(np.float32)
del _yy, _xx, _r

def fin_bg(img, top=True):
    a = np.asarray(img, np.float32)
    m = BGMUL if top else VIGN[..., None]
    return Image.fromarray(np.clip(a * m, 0, 255).astype(np.uint8))

_rng = np.random.default_rng(7)
GRAIN = []
for _ in range(10):
    g = _rng.normal(128, 40, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)
    g = Image.fromarray(g).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(0.6))
    GRAIN.append((np.asarray(g, np.float32) - 128) / 128)

def grain(img, i, amt=0.075):
    a = np.asarray(img, np.float32) / 255
    g = GRAIN[(i * 7) % len(GRAIN)][..., None]
    w = np.sqrt(np.clip(4 * a * (1 - a), 0, 1))
    return Image.fromarray(np.clip((a + g * amt * w) * 255, 0, 255).astype(np.uint8))

# ---------------------------------------------------------------- Typo
_fc = {}
def font(k, size):
    if (k, size) not in _fc:
        _fc[(k, size)] = ImageFont.truetype(FONT[k], size)
    return _fc[(k, size)]

def text_width(txt, f, tr):
    return sum(f.getlength(c) for c in txt) + tr * (len(txt) - 1)

def draw_tracked(d, xy, txt, f, fill, tr=0):
    x, y = xy
    for c in txt:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + tr

def word_sprite(txt, k='anton', size=200, color=BONE, tr=None, shadow=0.5):
    """RGBA-Sprite eines Worts mit weichem Schlagschatten. Rückgabe: (sprite, ox, oy, tw, th)
    ox/oy = Position der Textbox im Sprite, tw/th = Textmaße (Kappenhöhe-Box)."""
    f = font(k, size)
    if tr is None:
        tr = -size * 0.012 if k == 'anton' else size * 0.04
    tw = int(text_width(txt, f, tr)) + 2
    asc, desc = f.getmetrics()
    bb = f.getbbox('H')
    cap_top, cap_bot = bb[1], bb[3]
    pad = int(size * 0.35)
    cw, ch = tw + 2 * pad, asc + desc + 2 * pad
    txtl = Image.new('L', (cw, ch), 0)
    draw_tracked(ImageDraw.Draw(txtl), (pad, pad), txt, f, 255, tr)
    out = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    if shadow:
        sh = txtl.filter(ImageFilter.GaussianBlur(size * 0.10))
        sh = Image.eval(sh, lambda v: int(v * shadow))
        shl = Image.new('L', (cw, ch), 0); shl.paste(sh, (0, int(size * 0.05)))
        out.paste(Image.new('RGBA', (cw, ch), (0, 0, 0, 255)), (0, 0), shl)
    col = Image.new('RGBA', (cw, ch), color + (255,))
    out = Image.alpha_composite(out, Image.composite(col, Image.new('RGBA', (cw, ch), (0, 0, 0, 0)), txtl))
    return out, pad, pad + cap_top, tw, cap_bot - cap_top

def fit_size(txt, k, maxw, start=400, tr_rel=None):
    s = start
    while s > 20:
        tr = (-s * 0.012 if k == 'anton' else s * 0.04) if tr_rel is None else s * tr_rel
        if text_width(txt, font(k, s), tr) <= maxw:
            return s
        s -= 2
    return s

def slam(dt):
    """Einschlag nach Stilrahmen: von groß einschlagen, 8 % Overshoot, 120 ms Nachfedern.
    dt = Frames seit Start; Einschlag (Kontakt) bei dt=3. Rückgabe (scale, opacity) oder None."""
    if dt < 0:
        return None
    if dt < 3:
        u = dt / 3
        return lerp(1.55, 0.92, ease_in(u)), [0.25, 0.6, 0.9][int(dt)]
    if dt < 7:
        u = (dt - 3) / 4
        return lerp(0.92, 1.0, ease_out(u)), 1.0
    return 1.0, 1.0

class Word:
    """Ein Wort, das auf einen Frame (Einschlag = hit) einschlägt."""
    def __init__(self, txt, x, y, size, hit, color=BONE, k='anton', out=None, anchor='l', tr=None, shadow=0.5):
        self.spr, self.ox, self.oy, self.tw, self.th = word_sprite(txt, k, size, color, tr, shadow)
        self.hit, self.out, self.anchor = hit, out, anchor
        self.x = x - (self.tw if anchor == 'r' else self.tw / 2 if anchor == 'c' else 0)
        self.y = y  # Oberkante der Großbuchstaben

    def draw(self, frame, i, dx=0, dy=0):
        st = slam(i - (self.hit - 3))
        if st is None:
            return
        s, op = st
        if self.out is not None and i >= self.out:
            u = (i - self.out) / 3
            if u >= 1:
                return
            s *= 1 + 0.12 * u; op *= 1 - u
        spr = self.spr
        cxw = self.x + self.tw / 2 + dx; cyw = self.y + self.th / 2 + dy
        if abs(s - 1) > 1e-3:
            spr = spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))), Image.BILINEAR)
        ocx = (self.ox + self.tw / 2) * s; ocy = (self.oy + self.th / 2) * s
        px, py = int(round(cxw - ocx)), int(round(cyw - ocy))
        a = spr.getchannel('A')
        if op < 1:
            a = Image.eval(a, lambda v: int(v * op))
        frame.paste(spr.convert('RGB'), (px, py), a)

class Kick:
    """Label in Barlow Condensed mit grünem Balken links, fährt von links ein."""
    def __init__(self, txt, x, y, start, size=60, out=None):
        f = font('bc8', size); tr = size * 0.035
        tw = int(text_width(txt.upper(), f, tr)) + 4
        barw, gap = int(size * 0.22), int(size * 0.3)
        pad = 40
        self.img = Image.new('RGBA', (barw + gap + tw + 2 * pad, int(size * 1.4) + 2 * pad), (0, 0, 0, 0))
        tl = Image.new('L', self.img.size, 0)
        dl = ImageDraw.Draw(tl)
        draw_tracked(dl, (pad + barw + gap, pad), txt.upper(), f, 255, tr)
        bb = f.getbbox('H')
        sh = tl.filter(ImageFilter.GaussianBlur(10)); sh = Image.eval(sh, lambda v: int(v * 0.55))
        self.img.paste(Image.new('RGBA', self.img.size, (0, 0, 0, 255)), (0, 4), sh)
        self.img.paste(Image.new('RGBA', self.img.size, BONE + (255,)), (0, 0), tl)
        ImageDraw.Draw(self.img).rectangle([pad, pad + bb[1] - 4, pad + barw, pad + bb[3] + 4], fill=FLEET + (255,))
        self.x, self.y, self.start, self.out, self.pad = x, y, start, out, pad
        self.cap = bb[1]

    def draw(self, frame, i, dx=0, dy=0):
        d = i - self.start
        if d < 0:
            return
        u = clamp01(d / 6)
        op = clamp01(d / 3)
        off = -60 * (1 - ease_out(u))
        if self.out is not None and i >= self.out:
            v = (i - self.out) / 3
            if v >= 1:
                return
            op *= 1 - v; off += 40 * v
        a = self.img.getchannel('A')
        if op < 1:
            a = Image.eval(a, lambda v: int(v * op))
        frame.paste(self.img.convert('RGB'), (int(self.x - self.pad + off + dx), int(self.y - self.pad - self.cap + dy)), a)

class Bar:
    def __init__(self, x, y, w, h, start, color=FLEET):
        self.x, self.y, self.w, self.h, self.start, self.color = x, y, w, h, start, color
    def draw(self, frame, i, dx=0, dy=0):
        d = i - self.start
        if d < 0:
            return
        ww = self.w * ease_out(clamp01(d / 6))
        ImageDraw.Draw(frame).rectangle([self.x + dx, self.y + dy, self.x + dx + ww, self.y + dy + self.h], fill=self.color)

class Chip:
    """Benefit-Chip: dunkles Glas mit Backdrop-Blur, grüne Kante links."""
    def __init__(self, txt, x, y, start, size=50):
        f = font('bc8', size); tr = size * 0.04
        tw = int(text_width(txt.upper(), f, tr))
        bb = f.getbbox('H')
        self.padx, self.pady, self.edge = 34, 26, 12
        self.w = self.edge + self.padx * 2 + tw
        self.h = (bb[3] - bb[1]) + self.pady * 2
        self.x, self.y, self.start = x, y, start
        self.txt = Image.new('L', (self.w, self.h), 0)
        draw_tracked(ImageDraw.Draw(self.txt), (self.edge + self.padx, self.pady - bb[1]), txt.upper(), f, 255, tr)

    def draw(self, frame, i, dx=0, dy=0):
        d = i - self.start
        if d < 0:
            return
        u = ease_out(clamp01(d / 6))
        st = slam(d)
        s = st[0] if st else 1
        op = clamp01(d / 3)
        x = int(self.x - 80 * (1 - u) + dx); y = int(self.y + dy)
        w, h = self.w, self.h
        box = (x, y, x + w, y + h)
        reg = frame.crop(box).filter(ImageFilter.GaussianBlur(16))
        reg = Image.blend(reg, Image.new('RGB', reg.size, DEEP), 0.45)
        card = reg.copy()
        dr = ImageDraw.Draw(card)
        dr.rectangle([0, 0, w - 1, h - 1], outline=(110, 120, 112))
        dr.rectangle([0, 0, self.edge - 1, h - 1], fill=FLEET)
        card.paste(Image.new('RGB', card.size, BONE), (0, 0), self.txt)
        if abs(s - 1) > 1e-3:
            nw, nh = int(w * s), int(h * s)
            card = card.resize((nw, nh), Image.BILINEAR)
            x += (w - nw) // 2; y += (h - nh) // 2
        m = Image.new('L', card.size, int(255 * op))
        # weicher Schatten
        frame.paste(card, (x, y), m)

# ---------------------------------------------------------------- Header
LOGO = Image.open(os.path.join(ROOT, 'stilrahmen/logo.png')).convert('RGBA')
def header_layer(n):
    lay = Image.new('RGBA', (W, 260), (0, 0, 0, 0))
    lg = LOGO.resize((112, 112), Image.LANCZOS)
    sh = Image.new('RGBA', lay.size, (0, 0, 0, 0))
    shm = Image.new('L', lay.size, 0); shm.paste(lg.getchannel('A'), (60, 102))
    shm = shm.filter(ImageFilter.GaussianBlur(10)); shm = Image.eval(shm, lambda v: int(v * 0.5))
    lay.paste(Image.new('RGBA', lay.size, (0, 0, 0, 255)), (0, 0), shm)
    lay.alpha_composite(lg, (60, 96))
    tl = Image.new('L', lay.size, 0); d = ImageDraw.Draw(tl)
    f = font('bc6', 30)
    draw_tracked(d, (194, 116), 'BISCHOF', f, 255, 5)
    draw_tracked(d, (194, 152), 'BAUMPFLEGE', f, 255, 5)
    if n:
        f2b, f2 = font('bc8', 28), font('bc6', 28)
        a = f'{n:02d}'; b = ' / 09'
        wa = text_width(a, f2b, 4) + 4; wb = text_width(b, f2, 4)
        x0 = W - 60 - wa - wb
        draw_tracked(d, (x0 + wa, 132), b, f2, 215, 4)
    sh2 = tl.filter(ImageFilter.GaussianBlur(6)); sh2 = Image.eval(sh2, lambda v: int(v * 0.6))
    lay.paste(Image.new('RGBA', lay.size, (0, 0, 0, 255)), (0, 2), sh2)
    lay.paste(Image.new('RGBA', lay.size, BONE + (255,)), (0, 0), tl)
    if n:
        gl = Image.new('L', lay.size, 0)
        draw_tracked(ImageDraw.Draw(gl), (x0, 132), a, f2b, 255, 4)
        lay.paste(Image.new('RGBA', lay.size, FLEET + (255,)), (0, 0), gl)
    return lay

_hc = {}
def header(frame, n, op=1.0):
    if n not in _hc:
        _hc[n] = header_layer(n)
    lay = _hc[n]
    a = lay.getchannel('A')
    if op < 1:
        a = Image.eval(a, lambda v: int(v * op))
    frame.paste(lay.convert('RGB'), (0, 0), a)

# ---------------------------------------------------------------- Masken
_rs = None
def person_mask(img, key):
    """Freistellmaske (u2net) als L-Bild, gecacht."""
    global _rs
    p = os.path.join(CACHE, f'mask_{key}.png')
    if os.path.exists(p):
        return Image.open(p)
    from rembg import remove, new_session
    if _rs is None:
        _rs = new_session('u2net')
    m = remove(img, session=_rs, only_mask=True, post_process_mask=True)
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    m.save(p)
    return m

# ---------------------------------------------------------------- Ausgabe
class Writer:
    def __init__(self, path):
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                                   '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264',
                                   '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p',
                                   '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                                   '-movflags', '+faststart', path], stdin=subprocess.PIPE)
    def write(self, img):
        self.p.stdin.write(np.asarray(img.convert('RGB'), np.uint8).tobytes())
    def close(self):
        self.p.stdin.close(); self.p.wait()
