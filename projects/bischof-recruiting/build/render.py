"""Renderer – Recruiting-Video Bischof Baumpflege (Action-Trailer-Stil).

python3 build/render.py <cache> stills <t> [<t> ...]        -> PNG-Standbilder (Stil-Check)
python3 build/render.py <cache> video <out.mp4> [t0 t1]      -> MP4 (ohne Ton)
"""
import os, sys, glob, math, subprocess
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from edl import SHOTS, FPS, W, H, DUR, src_time, shot_at

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = sys.argv[1] if len(sys.argv) > 1 else "cache"
FONTS = os.path.join(ROOT, "fonts")

C = dict(forest=(0x12, 0x34, 0x1D), deep=(0x0B, 0x1F, 0x12), fleet=(0x7D, 0xC2, 0x43),
         bone=(0xF4, 0xF2, 0xEC), ink=(0x0B, 0x0F, 0x0C))
def rgbf(c): return np.array(C[c], np.float32) / 255.0

SHOT = {s["id"]: s for s in SHOTS}
F = 1.0 / FPS

# ---------------------------------------------------------------- Grading
COEF = np.load(os.path.join(os.path.dirname(__file__), "grade_coef.npy")).astype(np.float32)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIGNETTE = (1 - 0.42 * np.clip(_r - 0.5, 0, None) ** 1.3).clip(0.45, 1)[..., None]
_yt = yy / H
TOPDARK = (1 - 0.40 * np.clip(1 - _yt / 0.2, 0, 1) ** 1.5)[..., None]
del yy, xx, _r, _yt


def grade(img):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    feats = [r, g, b, r * r, g * g, b * b, r * g, g * b, r * b, r ** 3, g ** 3, b ** 3]
    out = np.empty_like(img)
    for c in range(3):
        acc = np.full(r.shape, COEF[12, c], np.float32)
        for k, f in enumerate(feats):
            acc += COEF[k, c] * f
        out[..., c] = acc
    np.clip(out, 0, 1, out=out)
    return out * VIGNETTE * TOPDARK


rng = np.random.default_rng(7)
GRAIN = []
for _ in range(8):
    n = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), 0.6)
    GRAIN.append(cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)[..., None])


def add_grain(img, f, amt=0.045):
    n = GRAIN[f % len(GRAIN)]
    lum = img.mean(2, keepdims=True)
    w = 0.6 + 1.6 * lum * (1 - lum)          # Korn stärker in den Mitteltönen
    return np.clip(img + n * amt * w, 0, 1)

# ---------------------------------------------------------------- Quellen
@lru_cache(maxsize=48)
def load_jpg(path):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0


@lru_cache(maxsize=48)
def load_mask(path):
    m = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return None if m is None else m.astype(np.float32) / 255.0


def nframes(sid):
    return len(glob.glob(os.path.join(CACHE, "src", sid, "*.jpg")))


def src_frame(shot, lt):
    """Quellbild (mit Frame-Blending für Zeitlupe) + ggf. Maske."""
    st = src_time(shot, max(lt, 0)) - shot["src_in"]
    x = st * FPS
    n = nframes(shot["id"])
    i0 = int(min(max(math.floor(x), 0), n - 1)); i1 = min(i0 + 1, n - 1); a = x - math.floor(x)
    p = lambda i: os.path.join(CACHE, "src", shot["id"], f"{i + 1:04d}.jpg")
    img = load_jpg(p(i0))
    if 0.08 < a < 0.92 and i1 != i0:
        img = img * (1 - a) + load_jpg(p(i1)) * a
    m = None
    if shot.get("mask"):
        im = i0 if a < 0.5 else i1
        m = load_mask(os.path.join(CACHE, "mask", shot["id"], f"{im + 1:04d}.png"))
    return img, m


def ease_io(x): return 0.5 - 0.5 * math.cos(math.pi * min(max(x, 0), 1))
def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3


def affine(img, s, cx, cy, dx=0, dy=0, border=cv2.BORDER_REFLECT):
    M = np.float32([[s, 0, (1 - s) * cx + dx], [0, s, (1 - s) * cy + dy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=border)


def push_scale(shot, lt):
    p0, p1 = shot["push"]
    return p0 + (p1 - p0) * (lt / (shot["t1"] - shot["t0"]))


@lru_cache(maxsize=4)
def still_layers(name):
    d = os.path.join(CACHE, "still")
    fg = load_jpg(os.path.join(d, name + ".jpg"))
    bg = load_jpg(os.path.join(d, name + "_bg.jpg"))
    m = cv2.imread(os.path.join(d, name + "_mask.png"), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
    return fg, bg, m


def still_frame(shot, lt):
    """Parallax: Hintergrund langsam, freigestellter Vordergrund schneller."""
    fg, bg, m = still_layers(shot["still"])
    hh, ww = fg.shape[:2]
    u = lt / (shot["t1"] - shot["t0"])
    s = push_scale(shot, lt)
    pan = {"man_lkw": (-1, 0), "teleskoplader": (1, 0)}[shot["still"]]
    def place(src, scale, k):
        base = H / hh
        sc = base * scale
        ox = (W - ww * sc) / 2 - pan[0] * (u - 0.5) * 70 * k
        oy = (H - hh * sc) / 2
        M = np.float32([[sc, 0, ox], [0, sc, oy]])
        return cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    b = place(bg, s, 1.0)
    f = place(fg, s + (s - 1) * 0.9, 1.9)
    mm = place(m, s + (s - 1) * 0.9, 1.9)[..., None]
    return b * (1 - mm) + f * mm, mm[..., 0]


def placeholder(lt):
    """Szene 5 bis zur Seedance-Erzeugung: dunkle Fläche mit Kennzeichnung."""
    g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img = rgbf("deep") * (1 - g) * 1.1 + rgbf("ink") * g
    img = np.broadcast_to(img, (H, W, 3)).copy()
    return img


def endcard_bg(lt):
    g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img = rgbf("forest") * (1 - g) + rgbf("deep") * g
    img = np.broadcast_to(img, (H, W, 3)).copy()
    # weiches Licht hinter dem Logo
    yy, xx = np.ogrid[0:H, 0:W]
    d = np.sqrt((xx - W / 2) ** 2 + (yy - 720) ** 2) / 700
    img += (np.exp(-d ** 2 * 2.2) * 0.16)[..., None] * rgbf("fleet")
    return img


def base(shot, lt, extra=1.0, dx=0, dy=0):
    """Ungegradetes Bild + Personenmaske für einen Shot zur lokalen Zeit."""
    if shot["id"] == "s5":
        return placeholder(lt), None, False
    if shot["id"] == "end":
        return endcard_bg(lt), None, False
    if shot.get("still"):
        img, m = still_frame(shot, lt)
        if extra != 1 or dx or dy:
            img = affine(img, extra, W / 2, H / 2, dx, dy); m = affine(m, extra, W / 2, H / 2, dx, dy)
        return img, m, True
    img, m = src_frame(shot, lt)
    s = push_scale(shot, lt) * extra
    cx, cy = shot["focus"][0] * W, shot["focus"][1] * H
    img = affine(img, s, cx, cy, dx, dy)
    if m is not None:
        m = affine(m, s, cx, cy, dx, dy)
    return img, m, True


def mblur(img, length, axis):
    L = int(abs(length))
    if L < 3:
        return img
    small = cv2.resize(img, (W // 2, H // 2))
    k = np.zeros((L // 2 * 2 + 1,) * 2, np.float32)
    c = k.shape[0] // 2
    if axis == 0: k[c, :] = 1
    else: k[:, c] = 1
    k /= k.sum()
    b = cv2.filter2D(small, -1, k, borderType=cv2.BORDER_REFLECT)
    return cv2.resize(b, (W, H))


def zoomblur(img, s0, s1, n=4):
    acc = np.zeros_like(img)
    for i in range(n):
        s = s0 + (s1 - s0) * i / max(n - 1, 1)
        acc += affine(img, s, W / 2, H / 2)
    return acc / n

# ---------------------------------------------------------------- Bildebene + Übergänge
def frame_image(t):
    """Gegradetes Hintergrundbild + Maske (Person) zum Zeitpunkt t."""
    f = round(t * FPS)
    if t < 0.5:  # Kaltstart Schwarz
        return np.zeros((H, W, 3), np.float32), None
    sh = shot_at(t)
    lt = t - sh["t0"]
    img, m, footage = base(sh, lt)

    def cut_offset(tc):
        return round((t - tc) * FPS)  # Frames relativ zum Schnitt (0 = erstes Bild nach dem Schnitt)

    # Match Cut Aufwärtsbewegung 5.0 (s2 -> s3)
    k = cut_offset(5.0)
    if -2 <= k <= 2:
        dy = [-140, -60, 120, 60, 20][k + 2]
        sh2 = shot_at(t); img, m, _ = base(sh2, t - sh2["t0"], dy=dy)
        img = mblur(img, [70, 40, 90, 50, 0][k + 2], 1)
    # Whip Pans 9, 10, 11
    for tc in (9.0, 10.0, 11.0):
        k = cut_offset(tc)
        if -3 <= k <= 2:
            prog = (k + 3.5) / 6.0  # 0..1 über den Whip
            if k < 0:
                dx = -ease_io(prog * 2) * W * 0.55
            else:
                dx = (1 - ease_io((prog - 0.5) * 2)) * W * 0.55
            sh2 = shot_at(t); img, m, _ = base(sh2, t - sh2["t0"], dx=dx)
            img = mblur(img, 30 + 220 * math.sin(math.pi * prog), 0)
    # Zoom-Schnitt 19.0 (s6a -> s6b) und 25.0 (s7b -> s8)
    for tc, amt in ((19.0, 0.16), (25.0, 0.22)):
        k = cut_offset(tc)
        if -2 <= k < 0:
            sh2 = shot_at(t); im2, m2, _ = base(sh2, t - sh2["t0"])
            s = 1 + amt * (k + 3) / 3
            img = zoomblur(im2, s, s + amt * 0.4); m = None
        elif 0 <= k < 5:
            s = 1 + amt * (1 - ease_out((k + 1) / 5))
            sh2 = shot_at(t); im2, m2, _ = base(sh2, t - sh2["t0"], extra=s)
            img = zoomblur(im2, 1.0, 1 + (s - 1) * 0.5) if k < 3 else im2
            m = m2
    if footage or sh["id"] in ("s5", "end"):
        img = grade(img) if footage else img
    # Maske über den Korbrand 8.0 (s3 -> s4a)
    k = cut_offset(8.0)
    if -5 <= k <= 3:
        a_img, _, _ = base(SHOT["s3"], min(t, 7.999) - SHOT["s3"]["t0"])
        b_img, _, _ = base(SHOT["s4a"], max(t, 8.0) - SHOT["s4a"]["t0"])
        a_img, b_img = grade(a_img), grade(b_img)
        p = ease_io((k + 5.5) / 9)
        yy, xx = np.ogrid[0:H, 0:W]
        edge = (H + 260) - p * (H + 900) + (xx - W / 2) * 0.22
        below = ((yy - edge) / 6).clip(0, 1).astype(np.float32)[..., None]
        band = (np.abs(yy - edge + 45) < 55).astype(np.float32)
        band = cv2.GaussianBlur(band, (0, 0), 4)[..., None]
        img = a_img * (1 - below) + b_img * below
        img = img * (1 - band) + rgbf("ink") * band
        m = None
    # Grüne Wischblende 21.0 (s6b -> s7a)
    k = cut_offset(21.0)
    if -5 <= k <= 4:
        p = (k + 5.5) / 10
        yy, xx = np.ogrid[0:H, 0:W]
        slant = (H - yy) * 0.35
        lead = -500 + p * (W + 1400)           # führende Kante
        trail = lead - 900
        x = xx + slant * 0 - slant + 250
        inside = ((x < lead) & (x > trail)).astype(np.float32)
        edge = ((x < lead) & (x > lead - 46)).astype(np.float32)
        panel = rgbf("forest") * (1 - edge[..., None]) + rgbf("fleet") * edge[..., None]
        img = img * (1 - inside[..., None]) + panel * inside[..., None]
        m = None if inside.mean() > 0.02 else m
    # Flash auf den Drop 17.0
    k = cut_offset(17.0)
    if 0 <= k <= 2:
        img = img + (1 - img) * [0.85, 0.45, 0.15][k]
    # Licht-Match-Cut 29.6: Licht vom Lkw blüht auf, wird zur Endkarte
    if 28.9 <= t < 29.6:
        p = (t - 28.9) / 0.7
        yy, xx = np.ogrid[0:H, 0:W]
        cx, cy = W / 2, 1060
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        rad = 60 + p ** 2.2 * 2200
        bloom = np.exp(-(d / rad) ** 2)[..., None].astype(np.float32)
        img = img + (1 - img) * np.clip(bloom * (0.4 + 1.2 * p ** 1.5), 0, 1)
    if 29.6 <= t < 30.0:
        p = (t - 29.6) / 0.4
        img = img + (1 - img) * (1 - ease_out(p))
    return img, m

# ---------------------------------------------------------------- Typografie
@lru_cache(maxsize=32)
def font(name, size):
    files = dict(anton="Anton-Regular.ttf", bc6="BarlowCondensed-SemiBold.ttf",
                 bc8="BarlowCondensed-ExtraBold.ttf", bc9="BarlowCondensed-Black.ttf")
    return ImageFont.truetype(os.path.join(FONTS, files[name]), size)


def fit(text, fname, max_w, max_size):
    f = font(fname, 200)
    w = f.getlength(text)
    return int(min(max_size, max_w * 200 / w))


@lru_cache(maxsize=128)
def sprite(text, fname, size, color, tracking=0, shadow=0.35):
    """RGBA-Sprite (premultiplied float) mit weichem Schlagschatten. Ursprung = Tintenkante oben links."""
    f = font(fname, size)
    pad = int(size * 0.5) + 20
    asc, desc = f.getmetrics()
    widths = [f.getlength(ch) + tracking for ch in text]
    tw = int(sum(widths) + 2 * pad); th = int(asc + desc + 2 * pad)
    a = Image.new("L", (tw, th), 0); d = ImageDraw.Draw(a)
    x = pad
    for ch, wch in zip(text, widths):
        d.text((x, pad), ch, font=f, fill=255); x += wch
    bbox = a.getbbox()
    A = np.asarray(a, np.float32) / 255.0
    col = np.array(C[color], np.float32) / 255.0
    rgba = np.zeros((th, tw, 4), np.float32)
    if shadow:
        sh = a.filter(ImageFilter.GaussianBlur(size * 0.12))
        S = np.asarray(sh, np.float32) / 255.0 * shadow
        S = np.roll(S, int(size * 0.06), axis=0)
        if fname == "anton":  # weicher Scrim für Lesbarkeit auf hellem/grünem Grund
            wide = np.asarray(a.filter(ImageFilter.GaussianBlur(size * 0.38)), np.float32) / 255.0
            S = 1 - (1 - S * 1.4) * (1 - np.clip(wide * 1.6, 0, 1) * 0.42)
        rgba[..., 3] = np.clip(S, 0, 1)
    rgba[..., :3] = col * A[..., None]
    rgba[..., 3] = A + rgba[..., 3] * (1 - A)
    return rgba, (bbox[0], bbox[1]), (bbox[2] - bbox[0], bbox[3] - bbox[1])


def over(canvas, layer):
    """canvas RGB float; layer premultiplied RGBA float (H,W,4)."""
    return canvas * (1 - layer[..., 3:4]) + layer[..., :3]


def blit(layer, spr, x, y, scale=1.0, alpha=1.0, dx=0, dy=0):
    """Sprite so platzieren, dass seine Tintenkante oben links bei (x, y) liegt; Skalierung um die Mitte."""
    rgba, (bx, by), (bw, bh) = spr
    cx, cy = bx + bw / 2, by + bh / 2
    tx, ty = x + bw / 2 + dx, y + bh / 2 + dy
    M = np.float32([[scale, 0, tx - scale * cx], [0, scale, ty - scale * cy]])
    warped = cv2.warpAffine(rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    warped *= alpha
    layer[...] = layer * (1 - warped[..., 3:4]) + warped


def slam(dt):
    """Einschlag auf den Beat: groß rein, 8 % Overshoot, 120 ms Nachfedern, danach leichter Drift."""
    fr = dt * FPS
    if fr < 0:
        return None
    if fr < 3:
        u = fr / 3
        s = 1.38 + (0.92 - 1.38) * u * u
    elif fr < 3 + 3.6:
        s = 0.92 + 0.08 * ease_out((fr - 3) / 3.6)
    else:
        s = 1.0
    s *= 1 + 0.012 * dt
    return s, min(1.0, (fr + 1) / 2.5)


def slide(dt, dist=70):
    fr = dt * FPS
    if fr < 0:
        return None
    u = min(fr / 7, 1)
    back = 1 + 2.2 * (u - 1) ** 3 + 1.2 * (u - 1) ** 2  # easeOutBack
    return (1 - back) * -dist, min(1, fr / 3)


def chip(text, size=46):
    f = font("bc8", size)
    tracking = 2
    tw = sum(f.getlength(c) + tracking for c in text)
    pw, ph = int(tw + 2 * 30 + 12), int(size * 1.55)
    pad = 40
    img = np.zeros((ph + 2 * pad, pw + 2 * pad, 4), np.float32)
    a = Image.new("L", (pw + 2 * pad, ph + 2 * pad), 0); d = ImageDraw.Draw(a)
    d.rectangle([pad, pad, pad + pw, pad + ph], fill=255)
    sh = np.asarray(a.filter(ImageFilter.GaussianBlur(18)), np.float32) / 255 * 0.45
    sh = np.roll(sh, 10, axis=0)
    img[..., 3] = sh
    body = np.zeros_like(img)
    body[pad:pad + ph, pad:pad + pw, :3] = rgbf("forest") * 0.92
    body[pad:pad + ph, pad:pad + pw, 3] = 0.92
    body[pad:pad + ph, pad:pad + 12, :3] = rgbf("fleet"); body[pad:pad + ph, pad:pad + 12, 3] = 1
    img = body + img * (1 - body[..., 3:4])
    t = Image.new("L", a.size, 0); dt_ = ImageDraw.Draw(t)
    asc, desc = f.getmetrics()
    x = pad + 12 + 30
    y = pad + (ph - (asc + desc)) / 2 + size * 0.04
    for ch in text:
        dt_.text((x, y), ch, font=f, fill=255); x += f.getlength(ch) + tracking
    T = (np.asarray(t, np.float32) / 255)[..., None]
    img = np.concatenate([rgbf("bone") * T, T], 2) + img * (1 - T)
    return img, (pad, pad), (pw, ph)


def cta(text="JETZT BEWERBEN", size=84):
    f = font("anton", size)
    tw = f.getlength(text)
    pw, ph = int(tw + 2 * 64), int(size * 1.6)
    pad = 50
    a = Image.new("L", (pw + 2 * pad, ph + 2 * pad), 0); d = ImageDraw.Draw(a)
    poly = [(pad, pad), (pad + pw, pad), (pad + pw, pad + ph * 0.7), (pad + pw - pw * 0.06, pad + ph), (pad, pad + ph)]
    d.polygon(poly, fill=255)
    A = (np.asarray(a, np.float32) / 255)[..., None]
    sh = np.roll(np.asarray(a.filter(ImageFilter.GaussianBlur(24)), np.float32) / 255 * 0.4, 14, axis=0)[..., None]
    img = np.concatenate([rgbf("fleet") * A, A], 2) + np.concatenate([np.zeros_like(A).repeat(3, 2), sh], 2) * (1 - A)
    t = Image.new("L", a.size, 0); dt_ = ImageDraw.Draw(t)
    asc, desc = f.getmetrics()
    dt_.text((pad + 64, pad + (ph - asc) / 2 - size * 0.06), text, font=f, fill=255)
    T = (np.asarray(t, np.float32) / 255)[..., None]
    img = np.concatenate([rgbf("deep") * T, img[..., 3:4]], 2) + np.concatenate([img[..., :3] * (1 - T), np.zeros_like(T)], 2)
    return img, (pad, pad), (pw, ph)


@lru_cache(maxsize=1)
def logo_sprite(size=460):
    im = Image.open(os.path.join(ROOT, "stilrahmen", "logo.png")).convert("RGBA").resize((size, size), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255
    pad = 60
    out = np.zeros((size + 2 * pad, size + 2 * pad, 4), np.float32)
    al = Image.fromarray((a[..., 3] * 255).astype(np.uint8))
    canvas = Image.new("L", (size + 2 * pad, size + 2 * pad), 0); canvas.paste(al, (pad, pad))
    sh = np.roll(np.asarray(canvas.filter(ImageFilter.GaussianBlur(30)), np.float32) / 255 * 0.5, 18, axis=0)
    out[..., 3] = sh
    fg = np.zeros_like(out)
    fg[pad:pad + size, pad:pad + size, :3] = a[..., :3] * a[..., 3:4]
    fg[pad:pad + size, pad:pad + size, 3] = a[..., 3]
    return fg + out * (1 - fg[..., 3:4]), (pad, pad), (size, size)


def bar_sprite(w, h, color="fleet"):
    img = np.zeros((h, w, 4), np.float32)
    img[..., :3] = rgbf(color); img[..., 3] = 1
    return img, (0, 0), (w, h)


def kick_sprite(text, size=58):
    """Label mit grünem Strich links (wie im Stilrahmen)."""
    s = sprite(text.upper(), "bc8", size, "bone", 2, 0.5)
    rgba, (bx, by), (bw, bh) = s
    rgba = rgba.copy()
    bar_w, gap = int(size * 0.22), int(size * 0.3)
    x0 = bx - gap - bar_w
    if x0 < 0:
        return s
    rgba[by - 2:by + bh + 4, x0:x0 + bar_w, :3] = rgbf("fleet"); rgba[by - 2:by + bh + 4, x0:x0 + bar_w, 3] = 1
    return rgba, (x0, by - 2), (bw + gap + bar_w, bh + 6)


# Textereignisse: (Start, Ende, Ebene, Sprite-Fabrik, x, y, Animation)
def headline(text, max_w=960, max_size=260, color="bone"):
    size = fit(text, "anton", max_w, max_size)
    return sprite(text, "anton", size, color, -2)


def stack(words, t, x, y, colors, max_size=250, gap=0.9, stagger=2, until=None, layer="front", max_w=960):
    """Mehrere Zeilen, jede auf eigener Zeile, gemeinsam skaliert, um 2 Frames versetzt."""
    size = min(fit(w, "anton", max_w, max_size) for w in words)
    out = []
    yy = y
    for i, (w, c) in enumerate(zip(words, colors)):
        s = sprite(w, "anton", size, c, -2)
        ti = t[i] if isinstance(t, (list, tuple)) else t + i * stagger * F
        out.append(dict(t=ti, until=until, layer=layer, spr=s, x=x, y=yy, anim="slam"))
        yy += s[2][1] + size * 0.10
    return out


EV = []
# Szene 1
EV += stack(["KEINE", "AUSBILDUNG?"], 0.5, 60, 560, ["bone", "bone"], max_size=230, until=2.0)
# Szene 2
EV += [dict(t=2.0, until=5.0, layer="front", spr=kick_sprite("Keine Ausbildung?", 62), x=62, y=300, anim="slide")]
EV += [dict(t=2.0, until=5.0, layer="back", spr=sprite("EGAL.", "anton", 520, "fleet", -6, 0.35), x=48, y=420, anim="slam")]
# Szene 3
EV += [dict(t=5.0, until=8.0, layer="front", spr=kick_sprite("Bei uns zählt nur eins:", 52), x=62, y=1040, anim="slide")]
EV += stack(["ANPACKEN."], 6.0, 56, 1130, ["bone"], max_size=250, until=8.0)
EV += [dict(t=6.5, until=8.0, layer="front", spr=bar_sprite(520, 22), x=62, y=1395, anim="wipe")]
# Szene 4
EV += stack(["GROSSE", "MASCHINEN."], [8.0, 8.5], 60, 700, ["bone", "fleet"], max_size=240, until=10.0)
EV += stack(["ECHTE", "NATUR."], [10.0, 10.25], 60, 700, ["bone", "fleet"], max_size=240, until=11.0)
EV += stack(["JEDES", "WETTER."], [11.0, 11.25], 60, 700, ["bone", "fleet"], max_size=240, until=12.0)
# Szene 5 (Platzhalter-Bild, Schrift final)
EV += stack(["DU BRAUCHST", "KEINE", "VORKENNTNISSE."], [12.5, 13.0, 13.5], 60, 640,
            ["bone", "bone", "fleet"], max_size=250, until=17.0)
EV += [dict(t=12.0, until=17.0, layer="front", spr=sprite("PLATZHALTER · SZENE 5 · ANLERNSZENE (SEEDANCE 2.5)", "bc6", 30, "bone", 3, 0),
            x=60, y=1440, anim="none", alpha=0.55)]
# Szene 6
EV += stack(["WIR ZEIGEN DIR,", "WIE'S GEHT."], [17.0, 18.0], 60, 640, ["bone", "fleet"], max_size=240, until=21.0)
# Szene 7
for i, (txt, tt) in enumerate([("Moderner Maschinenpark", 21.5), ("Faire Vergütung", 22.5), ("Vielfältige Einsätze", 23.5)]):
    EV.append(dict(t=tt, until=25.0, layer="front", spr=chip(txt.upper()), x=60, y=1100 + i * 118, anim="slide"))
# Szene 8
EV += stack(["QUEREINSTEIGER?", "PROFI?"], [25.0, 25.5], 60, 300, ["bone", "bone"], max_size=170, until=27.0)
EV += [dict(t=26.0, until=27.0, layer="back", spr=sprite("BEIDE.", "anton", 400, "fleet", -5, 0.35), x=48, y=700, anim="slam")]
# Endkarte
EV += [dict(t=29.6, until=None, layer="front", spr=logo_sprite(460), x=(W - 460) // 2, y=440, anim="slam")]
EV += [dict(t=29.85, until=None, layer="front", spr=sprite("BISCHOF BAUMPFLEGE", "bc8", 64, "bone", 8, 0.3), x=None, y=960, anim="slide")]
EV += [dict(t=29.95, until=None, layer="front", spr=sprite("WIEFELSTEDE", "bc6", 40, "fleet", 10, 0.3), x=None, y=1046, anim="slide")]
EV += [dict(t=30.5, until=None, layer="front", spr=cta(), x=None, y=1170, anim="slam")]
EV += [dict(t=30.75, until=None, layer="front", spr=sprite("bischof-baumpflege.de/jobs", "bc8", 54, "bone", 1, 0.3), x=None, y=1372, anim="slide")]


def text_layers(t):
    back = np.zeros((H, W, 4), np.float32); front = np.zeros((H, W, 4), np.float32)
    for e in EV:
        if t < e["t"] or (e["until"] is not None and t >= e["until"]):
            continue
        dt = t - e["t"]
        spr = e["spr"]
        x = e["x"] if e["x"] is not None else (W - spr[2][0]) / 2
        L = back if e["layer"] == "back" else front
        if e["anim"] == "slam":
            s, a = slam(dt); blit(L, spr, x, e["y"], s, a)
        elif e["anim"] == "slide":
            dx, a = slide(dt); blit(L, spr, x, e["y"], 1.0, a, dx=dx)
        elif e["anim"] == "wipe":
            u = ease_out(dt * FPS / 8)
            rgba, o, (bw, bh) = spr
            if u > 0.01:
                cut = (rgba[:, :max(1, int(bw * u))], o, (max(1, int(bw * u)), bh))
                blit(L, cut, x, e["y"])
        else:
            blit(L, spr, x, e["y"], 1.0, e.get("alpha", 1.0))
    return back, front


@lru_cache(maxsize=10)
def brand_layer(scene):
    L = np.zeros((H, W, 4), np.float32)
    blit(L, logo_sprite(110), 60, 96)
    rgba, o, (bw, bh) = sprite("BISCHOF", "bc6", 30, "bone", 5, 0.6)
    blit(L, (rgba, o, (bw, bh)), 192, 116)
    blit(L, sprite("BAUMPFLEGE", "bc6", 30, "bone", 5, 0.6), 192, 152)
    num = sprite(f"{scene:02d}", "bc8", 28, "fleet", 4, 0.6)
    rest = sprite(" / 09", "bc6", 28, "bone", 4, 0.6)
    xr = W - 60 - rest[2][0]
    blit(L, rest, xr, 136, alpha=0.85)
    blit(L, num, xr - num[2][0] - 6, 136)
    return L


def render(t):
    f = round(t * FPS)
    img, m = frame_image(t)
    back, front = text_layers(t)
    if back[..., 3].any():
        if m is not None:
            mm = cv2.GaussianBlur(m, (0, 0), 1.2)[..., None]
            back = back * (1 - mm)
        img = over(img, back)
    img = over(img, front)
    sh = shot_at(t)
    if 2.0 <= t < 29.6 and not (8 * 0 and False):
        img = over(img, brand_layer(sh["scene"]))
    img = add_grain(img, f, 0.05 if t >= 0.5 else 0.0)
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "stills":
        outdir = os.path.join(CACHE, "stills"); os.makedirs(outdir, exist_ok=True)
        for ts in sys.argv[3:]:
            t = float(ts)
            p = os.path.join(outdir, f"t{t:05.2f}.png")
            Image.fromarray(render(t)).save(p); print(p)
    elif mode == "video":
        out = sys.argv[3]
        t0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
        t1 = float(sys.argv[5]) if len(sys.argv) > 5 else DUR
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fr in range(round(t0 * FPS), round(t1 * FPS)):
            p.stdin.write(render(fr / FPS).tobytes())
            if fr % 60 == 0:
                print("frame", fr, flush=True)
        p.stdin.close(); p.wait()
        print("ok", out)
