"""Grading 'Nordischer Winter', Textur und Typo-Bausteine (Stilrahmen Bischof Baumpflege)."""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
BEAT = 15  # 120 BPM -> 0,5 s = 15 Frames

FOREST = (0x12, 0x34, 0x1D)
DEEP = (0x0B, 0x1F, 0x12)
FLEET = (0x7D, 0xC2, 0x43)
BONE = (0xF4, 0xF2, 0xEC)

FONT = {
    "anton": os.path.join(ROOT, "fonts/Anton-Regular.ttf"),
    "bc6": os.path.join(ROOT, "fonts/BarlowCondensed-SemiBold.ttf"),
    "bc8": os.path.join(ROOT, "fonts/BarlowCondensed-ExtraBold.ttf"),
}


def font(name, size):
    return ImageFont.truetype(FONT[name], size)


# ---------------------------------------------------------------- Grading
def _build_luts():
    x = np.linspace(0, 1, 256)
    # harter Kontrast (S-Kurve) + komprimierte Highlights
    s = 1 / (1 + np.exp(-7.0 * (x - 0.48)))
    s = (s - s[0]) / (s[-1] - s[0])
    tone = 0.35 * x + 0.65 * s
    tone = np.where(tone > 0.6, 0.6 + (tone - 0.6) * 0.5, tone)  # Himmel/Highlights komprimieren
    tone = tone * 0.97 + 0.012  # Schwarz leicht angehoben (Film)
    shadow = np.clip(1 - x / 0.5, 0, 1) ** 1.5  # Gewicht Schatten
    high = np.clip((x - 0.6) / 0.4, 0, 1)
    r = tone - 0.035 * shadow - 0.010 * high
    g = tone + 0.004 * shadow
    b = tone + 0.045 * shadow + 0.02 * high  # kühle Schatten, leicht kühle Lichter
    return [np.clip(c * 255, 0, 255).astype(np.uint8) for c in (r, g, b)]


LUT_R, LUT_G, LUT_B = _build_luts()


def _build_luts_kino():
    """Kinolook: tiefe Schwärzen, kräftige S-Kurve, weiche Schulter, Teal-Schatten, warme Lichter."""
    x = np.linspace(0, 1, 256)
    s = 1 / (1 + np.exp(-7.0 * (x - 0.46)))
    s = (s - s[0]) / (s[-1] - s[0])
    tone = 0.38 * x + 0.62 * s
    tone = tone ** 1.04  # Mitten etwas dichter
    tone = np.where(tone > 0.7, 0.7 + (tone - 0.7) * 0.62, tone)  # Schulter: Himmel bleibt gezeichnet
    tone = tone * 0.975 + 0.015  # Schwarz minimal angehoben, keine zugelaufenen Schatten
    shadow = np.clip(1 - x / 0.55, 0, 1) ** 1.3
    warm = np.clip(1 - np.abs(x - 0.6) / 0.25, 0, 1)  # Wärme in den oberen Mitten (Haut, Holz, Schnittschutz)
    top = np.clip((x - 0.82) / 0.18, 0, 1)  # Spitzlichter/Himmel neutral-kühl
    r = tone - 0.050 * shadow + 0.035 * warm - 0.030 * top
    g = tone + 0.012 * shadow + 0.010 * warm - 0.004 * top
    b = tone + 0.045 * shadow - 0.030 * warm + 0.026 * top
    return [np.clip(c * 255, 0, 255).astype(np.uint8) for c in (r, g, b)]


KINO_R, KINO_G, KINO_B = _build_luts_kino()
LOOK = os.environ.get("LOOK", "kino")


def grade(rgb):
    if LOOK == "kino":
        return grade_kino(rgb)
    return grade_winter(rgb)


def denoise(rgb):
    """Leichtes Entrauschen: Farbrauschen kräftig, Helligkeitsrauschen kantenschonend."""
    ycc = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    y = cv2.bilateralFilter(ycc[..., 0], 7, 14, 5)
    cr = cv2.GaussianBlur(ycc[..., 1], (0, 0), 2.2)
    cb = cv2.GaussianBlur(ycc[..., 2], (0, 0), 2.2)
    return cv2.cvtColor(np.dstack([y, cr, cb]), cv2.COLOR_YCrCb2RGB)


def grade_kino(rgb):
    rgb = denoise(rgb)
    f0 = rgb.astype(np.float32)
    # Klarheit: nur großflächiger lokaler Kontrast, verstärkt kein feines Rauschen
    lum0 = f0 @ np.array([0.299, 0.587, 0.114], np.float32)
    base = cv2.GaussianBlur(lum0, (0, 0), 3)
    blur = cv2.GaussianBlur(lum0, (0, 0), 40)
    mid = 1 - np.abs(lum0 / 127.5 - 1)
    f0 += (0.2 * (base - blur) * mid)[..., None]
    src = np.clip(f0, 0, 255).astype(np.uint8)
    out = np.empty_like(src)
    out[..., 0] = KINO_R[src[..., 0]]
    out[..., 1] = KINO_G[src[..., 1]]
    out[..., 2] = KINO_B[src[..., 2]]
    f = out.astype(np.float32)
    lum = f @ np.array([0.299, 0.587, 0.114], np.float32)
    hsv = cv2.cvtColor(src, cv2.COLOR_RGB2HSV)
    h = hsv[..., 0].astype(np.float32)
    green = np.clip(1 - np.abs(h - 45) / 25, 0, 1)
    orange = np.clip(1 - np.abs(h - 13) / 11, 0, 1)
    sat = 1.1 + 0.38 * green + 0.5 * orange
    sat *= 1 - 0.3 * np.clip((lum - 180) / 60, 0, 1)
    f = lum[..., None] + (f - lum[..., None]) * sat[..., None]
    return np.clip(f, 0, 255).astype(np.uint8)


def grade_winter(rgb):
    """rgb uint8 HxWx3 -> graded uint8."""
    out = np.empty_like(rgb)
    out[..., 0] = LUT_R[rgb[..., 0]]
    out[..., 1] = LUT_G[rgb[..., 1]]
    out[..., 2] = LUT_B[rgb[..., 2]]
    f = out.astype(np.float32)
    lum = f @ np.array([0.299, 0.587, 0.114], np.float32)
    # Grün und Orange satt, Rest (Himmel, Asphalt) zurückhaltend
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h = hsv[..., 0].astype(np.float32)  # 0..180
    green = np.clip(1 - np.abs(h - 45) / 25, 0, 1)
    orange = np.clip(1 - np.abs(h - 12) / 10, 0, 1)
    sat = 0.92 + 0.42 * green + 0.38 * orange
    sat *= 1 - 0.35 * np.clip((lum - 190) / 65, 0, 1)  # Himmel entsättigen
    f = lum[..., None] + (f - lum[..., None]) * sat[..., None]
    return np.clip(f, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- Textur
def _vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.48) / (H * 0.6)) ** 2)
    v = 1 - 0.55 * np.clip(d - 0.42, 0, 1) ** 1.3
    top = 1 - 0.38 * np.clip(1 - yy / 420, 0, 1) ** 1.6  # Brand-Zeile oben
    return (v * top)[..., None]


VIG = _vignette()
_rng = np.random.default_rng(7)
GRAIN = []
for _ in range(6):
    n = _rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)
    n += _rng.normal(0, 0.6, (H, W)).astype(np.float32)
    GRAIN.append(n)


def texture(rgb, frame, grain=7.0, vignette=True):
    f = rgb.astype(np.float32)
    if vignette:
        f *= VIG
    g = GRAIN[frame % len(GRAIN)]
    lum = f.mean(axis=2, keepdims=True) / 255
    f += (g[..., None] * grain) * (0.5 + 0.5 * (1 - np.abs(lum * 2 - 1)))  # Korn in Mitteltönen
    return np.clip(f, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- Typo
def ease_out(t):
    return 1 - (1 - t) ** 3


def slam_scale(t):
    """t in Frames seit Einschlag. Schlägt ein, Overshoot 8 %, Nachfedern 120 ms (~4 Frames)."""
    if t < 0:
        return None
    if t < 3:
        return 1.45 + (1.08 - 1.45) * ease_out(t / 3)
    if t < 7:
        u = (t - 3) / 4
        return 1.08 + (0.985 - 1.08) * ease_out(u)
    if t < 10:
        u = (t - 7) / 3
        return 0.985 + (1.0 - 0.985) * ease_out(u)
    return 1.0


def text_img(txt, fname, size, color=BONE, tracking=0, shadow=True):
    f = font(fname, size)
    asc, desc = f.getmetrics()
    widths = [f.getlength(c) + tracking for c in txt]
    tw = int(sum(widths) - tracking) + 4
    pad = 60 if shadow else 4
    im = Image.new("RGBA", (tw + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for c, w in zip(txt, widths):
        d.text((x, pad), c, font=f, fill=color + (255,))
        x += w
    if shadow:
        a = im.split()[3].filter(ImageFilter.GaussianBlur(22))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.putalpha(a.point(lambda v: int(v * 0.55)))
        sh = sh.transform(sh.size, Image.AFFINE, (1, 0, 0, 0, 1, -14))
        im = Image.alpha_composite(sh, im)
    return im, pad


def paste_scaled(canvas, img, cx, cy, scale, alpha=1.0):
    """canvas: PIL RGBA. Zentriert img bei (cx, cy) mit Skalierung."""
    if scale is None or alpha <= 0:
        return
    w, h = img.size
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    im = img.resize((nw, nh), Image.BICUBIC)
    if alpha < 1:
        a = im.split()[3].point(lambda v: int(v * alpha))
        im.putalpha(a)
    canvas.alpha_composite(im, (int(cx - nw / 2), int(cy - nh / 2)))


def composite(rgb, layer, mask=None):
    """rgb uint8, layer PIL RGBA. mask: float HxW (1 = Person vorn, Schrift dahinter)."""
    L = np.asarray(layer, dtype=np.float32)
    a = L[..., 3:4] / 255
    if mask is not None:
        a = a * (1 - mask[..., None])
    out = rgb.astype(np.float32) * (1 - a) + L[..., :3] * a
    return out.astype(np.uint8)
