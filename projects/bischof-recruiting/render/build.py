"""Baut das Recruiting-Video (ohne Ton) Frame für Frame.

python3 build.py              -> out/video_stumm.mp4 (alle Szenen, Szene 5 als Platzhalter)
python3 build.py --stills     -> out/stills/szene_XX_fNNN.jpg (Stil-Check)
python3 build.py --only 2,8   -> nur diese Szenen rendern (als Stills)
"""
import os
import sys
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

from look import (W, H, FPS, BEAT, FOREST, DEEP, FLEET, BONE, ROOT, grade, texture,
                  text_img, paste_scaled, slam_scale, composite, ease_out, font)

OUT = os.path.join(ROOT, "render/out")
CACHE = os.path.join(ROOT, "render/cache")
os.makedirs(OUT, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)
FOOT = lambda n: (os.path.join(ROOT, "ki", n) if n.endswith(".mp4") else
                  os.path.join(ROOT, "footage", n + (".mov" if n.startswith("IMG") else "_video.mov")))
SZENE5 = "DJI_20260106_111743_142"  # Aufasten am Stamm (echtes Footage, ersetzt KI-Shot)
HAS5 = True
TOTAL = 36 * FPS  # 1080 (Benefits +3 Takte, Szene 5 −1 Takt)

# ---------------------------------------------------------------- Quellen
_src_cache = {}


def load_clip(name, start, dur, over=1.08):
    """Dekodiert [start, start+dur] als 30-fps-Frames, Cover-Crop auf 9:16 in Übergröße (für Push-in)."""
    key = (name, start, dur)
    if key in _src_cache:
        return _src_cache[key]
    ow, oh = int(W * over) // 2 * 2, int(H * over) // 2 * 2
    vf = f"fps={FPS},scale={ow}:{oh}:force_original_aspect_ratio=increase:flags=lanczos,crop={ow}:{oh}"
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur + 0.2), "-i", FOOT(name),
           "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, oh, ow, 3)
    _src_cache.clear()  # Speicher klein halten
    _src_cache[key] = fr
    return fr


def load_still(name, over=1.16):
    im = cv2.cvtColor(cv2.imread(os.path.join(ROOT, "stills", name)), cv2.COLOR_BGR2RGB)
    ow, oh = int(W * over), int(H * over)
    s = max(ow / im.shape[1], oh / im.shape[0])
    im = cv2.resize(im, (int(im.shape[1] * s) + 1, int(im.shape[0] * s) + 1), interpolation=cv2.INTER_AREA)
    y0 = (im.shape[0] - oh) // 2
    x0 = (im.shape[1] - ow) // 2
    return im[y0:y0 + oh, x0:x0 + ow]


def sample(frames, t_src):
    """Frame an Quellzeit (Frames, float) mit Überblendung für Zeitlupe."""
    t_src = min(max(t_src, 0), len(frames) - 1.001)
    i = int(t_src)
    a = t_src - i
    if a < 0.05:
        return frames[i]
    return cv2.addWeighted(frames[i], 1 - a, frames[i + 1], a, 0)


def push(img, u, z0=1.0, z1=1.05, dx=0.0, dy=0.0, rot=0.0):
    """Push-in: u 0..1 im Shot, croppt aus der Übergröße auf W x H."""
    z = z0 + (z1 - z0) * u
    h, w = img.shape[:2]
    base = max(W / w, H / h)  # Übergröße -> 1.0 = volle Fläche
    s = base * z
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, s)
    M[0, 2] += W / 2 - w / 2 + dx
    M[1, 2] += H / 2 - h / 2 + dy
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def motion_blur(img, dx, dy=0):
    n = int(max(abs(dx), abs(dy)))
    if n < 2:
        return img
    k = np.zeros((2 * n + 1, 2 * n + 1), np.float32)
    cv2.line(k, (n - int(dx / 2), n - int(dy / 2)), (n + int(dx / 2), n + int(dy / 2)), 1, 1)
    k /= k.sum()
    return cv2.filter2D(img, -1, k)


# ---------------------------------------------------------------- Masken (rembg u2net)
_rembg = None


def person_mask(rgb, key):
    global _rembg
    path = os.path.join(CACHE, key + ".png")
    if os.path.exists(path):
        return cv2.imread(path, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    if _rembg is None:
        from rembg import new_session, remove
        _rembg = (new_session("u2net"), remove)
    sess, remove = _rembg
    small = Image.fromarray(cv2.resize(rgb, (540, 960), interpolation=cv2.INTER_AREA))
    m = np.asarray(remove(small, session=sess, only_mask=True))
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    m = cv2.GaussianBlur(m, (5, 5), 0)
    cv2.imwrite(path, m)
    return m.astype(np.float32) / 255


# ---------------------------------------------------------------- Grafik-Bausteine
LOGO = Image.open(os.path.join(ROOT, "stilrahmen/logo.png")).convert("RGBA")
_txt = {}


def T(txt, fname="anton", size=200, color=BONE, tracking=0, shadow=True):
    k = (txt, fname, size, color, tracking, shadow)
    if k not in _txt:
        _txt[k] = text_img(txt, fname, size, color, tracking, shadow)
    return _txt[k]


def brand_line(layer, scene_no):
    lg = LOGO.resize((110, 110), Image.LANCZOS)
    sh = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    sh.alpha_composite(lg, (20, 26))
    a = sh.split()[3].filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * .45))
    shadow = Image.new("RGBA", sh.size, (0, 0, 0, 255)); shadow.putalpha(a)
    layer.alpha_composite(shadow, (40, 76))
    layer.alpha_composite(lg, (60, 96))
    d = ImageDraw.Draw(layer)
    f = font("bc6", 30)
    for i, line in enumerate(["BISCHOF", "BAUMPFLEGE"]):
        x = 192
        for c in line:
            d.text((x + 1, 118 + i * 35 + 2), c, font=f, fill=(0, 0, 0, 120))
            d.text((x, 118 + i * 35), c, font=f, fill=BONE + (255,))
            x += f.getlength(c) + 5
    fb, fs = font("bc8", 28), font("bc6", 28)
    num, rest = f"{scene_no:02d}", " / 09"
    wn = fb.getlength(num) + 4 * len(num)
    wr = sum(fs.getlength(c) + 4 for c in rest)
    x = W - 60 - wn - wr
    for c in num:
        d.text((x, 132), c, font=fb, fill=FLEET + (255,)); x += fb.getlength(c) + 4
    for c in rest:
        d.text((x, 132), c, font=fs, fill=BONE + (217,)); x += fs.getlength(c) + 4


def kicker(layer, txt, x, y, t, size=64):
    """Label mit grünem Balken links (Barlow Condensed ExtraBold)."""
    if t < 0:
        return
    u = ease_out(min(1, t / 6))
    d = ImageDraw.Draw(layer)
    bh = int(size * 0.9)
    d.rectangle([x, y + 8, x + 14, y + 8 + int(bh * u)], fill=FLEET + (255,))
    im, pad = T(txt, "bc8", size, BONE, 2)
    if u > 0:
        w = int((im.size[0] - 2 * pad) * u) + pad
        crop = im.crop((0, 0, w + pad, im.size[1]))
        layer.alpha_composite(crop, (x + 32 - pad, y - pad - int(size * 0.12)))


def slam_words(layer, words, x, y, hit, f, size, color=BONE, gap=None, stagger=2, line_h=None, align="left"):
    """Wörter schlagen nacheinander ein (je 2 Frames versetzt). words: Liste von (text, farbe|None, zeile)."""
    line_h = line_h or int(size * 0.92)
    rows = {}
    for i, w in enumerate(words):
        txt, col, row = w if len(w) == 3 else (w[0], w[1], 0)
        rows.setdefault(row, []).append((i, txt, col or color))
    for row, items in rows.items():
        imgs = [(i, T(txt, "anton", size, col)) for i, txt, col in items]
        sp = gap if gap is not None else int(size * 0.22)
        total = sum(im.size[0] - 2 * pad for _, (im, pad) in imgs) + sp * (len(imgs) - 1)
        cx = x if align == "left" else x - total / 2
        for i, (im, pad) in imgs:
            ww = im.size[0] - 2 * pad
            s = slam_scale(f - hit - i * stagger)
            a = 0 if s is None else min(1, (f - hit - i * stagger + 1) / 2)
            paste_scaled(layer, im, cx + ww / 2, y + row * line_h + im.size[1] / 2 - pad, s, a)
            cx += ww + sp


def green_bar(layer, x, y, w, h, t):
    if t < 0:
        return
    u = ease_out(min(1, t / 5))
    ImageDraw.Draw(layer).rectangle([x, y, x + int(w * u), y + h], fill=FLEET + (255,))


def chip(layer, txt, x, y, t, size=46):
    if t < 0:
        return
    u = ease_out(min(1, t / 6))
    f = font("bc8", size)
    tw = sum(f.getlength(c) + 2 for c in txt)
    cw, chh = int(tw + 64), int(size * 1.75)
    c = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, cw, chh], fill=(11, 31, 18, 205), outline=(244, 242, 236, 46))
    d.rectangle([0, 0, 13, chh], fill=FLEET + (255,))
    xx = 38
    for ch in txt:
        d.text((xx, int(chh * 0.16)), ch, font=f, fill=BONE + (255,)); xx += f.getlength(ch) + 2
    off = int((1 - u) * -160)
    a = c.split()[3].point(lambda v: int(v * u)); c.putalpha(a)
    layer.alpha_composite(c, (x + off, y))


def cta(layer, x, y, t, size=70):
    if t < 0:
        return
    s = slam_scale(t)
    f = font("anton", size)
    txt = "JETZT BEWERBEN"
    tw = int(f.getlength(txt)) + 8
    bw, bh = tw + 100, int(size * 1.55)
    b = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.polygon([(0, 0), (bw, 0), (bw, int(bh * .7)), (bw - int(bw * .06), bh), (0, bh)], fill=FLEET + (255,))
    d.text((50, int(bh * .14)), txt, font=f, fill=DEEP + (255,))
    paste_scaled(layer, b, x + bw / 2, y + bh / 2, s)


# ---------------------------------------------------------------- Shots
class Shot:
    def __init__(self, a, b, src=None, start=0.0, speed=1.0, still=None, z=(1.0, 1.05), drift=(0, 0), mask=False,
                 off=(0, 0), over=1.08, dehaze=0.0, lv=None):
        self.a, self.b, self.src, self.start, self.speed = a, b, src, start, speed
        self.still, self.z, self.drift, self.mask = still, z, drift, mask
        self.off, self.over, self.dehaze, self.lv = off, over, dehaze, lv

    def src_dur(self):
        n = self.b - self.a
        sp = self.speed if not callable(self.speed) else 2.2
        return n * sp / FPS + 0.3

    def t_src(self, k):
        if callable(self.speed):
            return self.speed(k)
        return k * self.speed

    def frame(self, f):
        k = f - self.a
        u = k / max(1, self.b - self.a - 1)
        if self.still is not None:
            img = self.still
        else:
            fr = load_clip(self.src, self.start, self.src_dur(), self.over)
            img = sample(fr, self.t_src(k))
        dx = self.off[0] + self.drift[0] * (u - 0.5)
        dy = self.off[1] + self.drift[1] * (u - 0.5)
        out = push(img, ease_inout(u), self.z[0], self.z[1], dx, dy)
        if self.dehaze:
            out = dehaze(out, self.dehaze)
        if self.lv:
            out = levels(out, *self.lv)
        return grade(out)


def dehaze(img, k):
    """Nebel: Tonwerte spreizen (1.–99. Perzentil je Kanal gemeinsam), Mitten leicht absenken."""
    f = img.astype(np.float32)
    lo, hi = np.percentile(f, 1), np.percentile(f, 99.5)
    g = np.clip((f - lo) / max(1, hi - lo), 0, 1) ** 1.15 * 255
    return np.clip(f * (1 - k) + g * k, 0, 255).astype(np.uint8)


def levels(img, bp, gamma, wp=255):
    """Belichtung je Shot: Schwarzpunkt bp, Mitten-Gamma (>1 = dichter), Weißpunkt wp."""
    lut = np.clip((np.arange(256) - bp) / (wp - bp), 0, 1) ** gamma * 255
    return lut.astype(np.uint8)[img]


def ease_inout(u):
    return u  # konstanter Push, nie Stillstand


def ramp_greifer(k):
    # schnell rein (2x), Zeitlupe beim Zupacken (0.4x), wieder anziehen
    if k < 12:
        return k * 2.0
    if k < 24:
        return 24 + (k - 12) * 0.4
    return 28.8 + (k - 24) * 1.6


def ramp_saw(k):
    # Säge im Stamm: Zeitlupe 0.45x
    return k * 0.45


def ramp_fall(k):
    # Stammstück fällt: normal, dann Zeitlupe im Fall
    if k < 30:
        return k * 1.0
    return 30 + (k - 30) * 0.5


# Szenen-Timing (Frames, 30 fps, 1 Beat = 15 Frames)
SHOTS = {
    1: [Shot(15, 60, "DJI_20260106_111921_962", 0.2, ramp_saw, z=(1.06, 1.12))],
    2: [Shot(60, 150, "IMG_0209", 11.4, 1.0, z=(1.0, 1.05), drift=(0, -60), mask=True)],
    3: [Shot(150, 240, "IMG_0469", 2.0, 1.0, z=(1.0, 1.05), drift=(0, 40), lv=(30, 1.22, 250))],
    4: [Shot(240, 255, "IMG_0472", 1.6, ramp_greifer, z=(1.02, 1.07), lv=(16, 1.2, 250)),
        Shot(255, 277, "DJI_20260131_090238_114", 0.6, 1.0, z=(1.04, 1.09), lv=(16, 1.2, 250)),
        Shot(277, 315, "IMG_0452", 1.3, 1.0, z=(1.02, 1.07), lv=(8, 1.45, 255), dehaze=0.5),
        Shot(315, 360, "DJI_20260131_091040_966", 0.4, 1.0, z=(1.0, 1.05), lv=(14, 1.15, 250))],
    6: [Shot(450, 510, "IMG_0474", 2.6, 1.0, z=(1.02, 1.07), mask=True),
        Shot(510, 570, "DJI_20260106_111921_962", 4.4, ramp_fall, z=(1.03, 1.08))],
    7: [Shot(570, 670, still="man_lkw.jpg", z=(1.0, 1.07), drift=(80, 0)),
        Shot(670, 770, "IMG_0468", 0.6, 1.0, z=(1.02, 1.08), drift=(-40, 0)),
        Shot(770, 870, "IMG_52F7A0A2", 1.3, 1.0, z=(1.32, 1.38), off=(150, 60))],  # Kronenabwurf, Stamm rechts
    5: [Shot(360, 450, SZENE5, 1.4, 1.0, z=(1.0, 1.06), lv=(12, 1.24, 255))],
    8: [Shot(870, 930, "IMG_3412", 1.0, 1.0, z=(1.0, 1.05), drift=(0, -40), mask=True)],
    9: [Shot(930, 1080, "IMG_3569", 0.6, 1.0, z=(1.45, 1.55), off=(0, -110), over=1.6, dehaze=0.85)],
}
SCENE_RANGE = {1: (0, 60), 2: (60, 150), 3: (150, 240), 4: (240, 360), 5: (360, 450),
               6: (450, 570), 7: (570, 870), 8: (870, 930), 9: (930, 1080)}
FLASH = 998  # Licht-Match-Cut auf Logo


def scene_of(f):
    for s, (a, b) in SCENE_RANGE.items():
        if a <= f < b:
            return s


def shot_of(f):
    for s in SHOTS.values():
        for sh in s:
            if sh.a <= f < sh.b:
                return sh


_still_cache = {}


def base_frame(f):
    sh = shot_of(f)
    if sh is None:
        return None, None
    if isinstance(sh.still, str):
        if sh.still not in _still_cache:
            _still_cache[sh.still] = load_still(sh.still)
        sh.still = _still_cache[sh.still]
    return sh.frame(f), sh


# ---------------------------------------------------------------- Szene 5: Platzhalter
def placeholder(f):
    k = f - 360
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = DEEP
    yy = np.linspace(0, 1, H)[:, None, None]
    img = (img * (0.75 + 0.35 * yy)).clip(0, 255).astype(np.uint8)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    fs = font("bc6", 34)
    for i, line in enumerate(["PLATZHALTER SZENE 5", "Anlernszene · Seedance 2.5 (Higgsfield)", "folgt nach Kostenfreigabe"]):
        d.text((80, 1250 + i * 50), line, font=fs, fill=(244, 242, 236, 110))
    d.rectangle([60, 1250, 66, 1390], fill=FLEET + (120,))
    return img, layer


# ---------------------------------------------------------------- Typo pro Szene
def typo(f, layer):
    """Zeichnet Schrift in layer. Gibt (layer_vorn, layer_hinten) zurück; hinten = hinter Person maskiert."""
    back = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s = scene_of(f)
    if s == 1:
        slam_words(layer, [("BEREIT FÜR", None, 0), ("WAS NEUES?", None, 1)], 64, 470, 15, f, 190)
    elif s == 2:
        kicker(layer, "BEREIT FÜR WAS NEUES?", 62, 300, f - 60)
        slam_words(back, [("HIER.", FLEET)], 52, 330, 75, f, 500)
    elif s == 3:
        kicker(layer, "BEI UNS ZÄHLT NUR EINS", 62, 300, f - 152)
        slam_words(layer, [("ANPACKEN.", None)], 56, 400, 210, f, 230)
        green_bar(layer, 64, 700, 300, 22, f - 214)
    elif s == 4:
        if f < 277:
            slam_words(layer, [("GROSSE", None, 0), ("MASCHINEN.", FLEET, 1)], 60, 360, 240, f, 200)
        elif f < 315:
            slam_words(layer, [("ECHTE", None, 0), ("NATUR.", FLEET, 1)], 60, 360, 277, f, 200)
        else:
            slam_words(layer, [("JEDES", None, 0), ("WETTER.", FLEET, 1)], 60, 360, 315, f, 200)
    elif s == 5:
        slam_words(layer, [("DU BRAUCHST", None, 0), ("KEINE", FLEET, 1), ("VORKENNTNISSE.", None, 2)],
                   60, 1090 if HAS5 else 420, 364, f, 150, stagger=4)
    elif s == 6:
        slam_words(back, [("WIR ZEIGEN", None, 0), ("DIR, WIE'S", None, 1), ("GEHT.", FLEET, 2)],
                   60, 300, 450, f, 175, stagger=3)
    elif s == 7:
        kicker(layer, "DAS BEKOMMST DU", 62, 300, f - 572)
        chip(layer, "MODERNER MASCHINENPARK", 60, 420, f - 572)
        chip(layer, "FAIRE VERGÜTUNG", 60, 530, f - 613)
        chip(layer, "VIELFÄLTIGE EINSÄTZE", 60, 640, f - 645)
        chip(layer, "DIENSTRAD-LEASING", 60, 750, f - 700)
        chip(layer, "URLAUBS- & WEIHNACHTSGELD", 60, 860, f - 745)
        chip(layer, "VERMÖGENSWIRKSAME LEISTUNGEN", 60, 970, f - 814)
    elif s == 8:
        slam_words(back, [("QUEREINSTEIGER?", None, 0)], 56, 330, 872, f, 160)
        slam_words(back, [("PROFI?", None, 0)], 56, 480, 887, f, 160)
        slam_words(layer, [("BEIDE.", FLEET, 0)], 56, 640, 902, f, 260)
    elif s == 9 and f >= FLASH:
        k = f - FLASH
        # Logo-Endkarte
        u = slam_scale(k - 4)
        lg = LOGO.resize((420, 420), Image.LANCZOS)
        paste_scaled(layer, lg, W / 2, 560, u, 1 if u else 0)
        slam_words(layer, [("BISCHOF", None, 0), ("BAUMPFLEGE", FLEET, 1)], W / 2, 830, FLASH + 12, f, 150,
                   align="center")
        if k >= 22:
            d = ImageDraw.Draw(layer)
            ff = font("bc6", 36)
            txt = "AUS WIEFELSTEDE"
            tw = sum(ff.getlength(c) + 6 for c in txt)
            x = W / 2 - tw / 2
            a = int(255 * min(1, (k - 22) / 6))
            for c in txt:
                d.text((x, 1170), c, font=ff, fill=BONE + (int(a * .85),)); x += ff.getlength(c) + 6
        cta(layer, W / 2 - 290, 1270, k - 30)
        if k >= 38:
            d = ImageDraw.Draw(layer)
            ff = font("bc8", 46)
            txt = "bischof-baumpflege.de/jobs"
            tw = ff.getlength(txt)
            a = int(255 * min(1, (k - 38) / 6))
            d.text((W / 2 - tw / 2, 1435), txt, font=ff, fill=BONE + (a,))
    return layer, back


# ---------------------------------------------------------------- Übergänge
def transition(f, img):
    # Whip Pans in Szene 4 (um Schnitte 270, 300, 330 und 360-Eingang nicht)
    for c in (255, 277, 315):
        d = f - c
        if -3 <= d <= 2:
            strength = (1 - abs(d + 0.5) / 3.5)
            dx = (1 if c != 277 else -1) * int(260 * strength)
            img = np.roll(img, dx, axis=1)
            img = motion_blur(img, 120 * strength)
    # Maske über Korbrand: S3 -> S4 (Fläche steigt von unten, 8 Frames)
    d = f - 240
    if -5 <= d <= 3:
        u = (d + 5) / 8
        edge = int(H * (1 - ease_out(u) * 1.15)) if d < 0 else int(H * (1.15 - 1.15 * ease_out((d + 1) / 4)) - H * 0.15)
        if d < 0:
            y = max(0, edge)
            img = img.copy(); img[y:] = FOREST
            img[max(0, y - 10):y] = FLEET
        else:
            y = int(H * (1 - (d + 1) / 4))
            img = img.copy(); img[:max(0, y)] = FOREST
            if y > 10:
                img[y - 10:y] = FLEET
    # Grüne Wischblende: S6 -> S7
    d = f - 570
    if -4 <= d <= 3:
        u = (d + 4) / 8
        x = int((W + 400) * ease_out(u)) - 200
        pts = np.array([[x - 260, 0], [x + 140, 0], [x, H], [x - 400, H]], np.int32)
        img = img.copy()
        cv2.fillPoly(img, [pts], FLEET)
        right = np.array([[x + 140, 0], [W + 500, 0], [W + 500, H], [x, H]], np.int32)
        left = np.array([[-500, 0], [x - 260, 0], [x - 400, H], [-500, H]], np.int32)
        # links vom Balken neues Bild (S7), rechts altes (S6): wird im Hauptloop gemischt
        return img, (left if d < 0 else right, d)
    # Zoom-Schnitt: S7 -> S8
    d = f - 870
    if 0 <= d < 6:
        z = 1.25 - 0.25 * ease_out(d / 6)
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
        img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        img = cv2.addWeighted(img, 0.6, cv2.GaussianBlur(img, (0, 0), 6 * (1 - d / 6) + 0.1), 0.4, 0)
    return img, None


# ---------------------------------------------------------------- Frame
def render(f):
    s = scene_of(f)
    if f < 15:  # Schwarz + Anwerfzug
        img = np.zeros((H, W, 3), np.uint8)
        return img
    if s == 5 and not HAS5:
        img, layer = placeholder(f)
        sh = None
    elif s == 9 and f >= FLASH:
        # Endkarte auf Logo-Grün, Lkw tief abgedunkelt dahinter
        bg, _ = base_frame(min(f, TOTAL - 1))
        bg = cv2.GaussianBlur(bg, (0, 0), 18)
        g = np.array(DEEP, np.float32)
        img = (bg.astype(np.float32) * 0.18 + g * 0.82).astype(np.uint8)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh = None
    else:
        img, sh = base_frame(f)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if s == 6:
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        img = (img * (1 - 0.5 * np.clip(1 - yy / 0.42, 0, 1) ** 1.2)).astype(np.uint8)
    elif s == 5 and HAS5:  # Schrift unten, Person bleibt frei
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        img = (img * (1 - 0.55 * np.clip((yy - 0.5) / 0.3, 0, 1) ** 1.2)).astype(np.uint8)
    front, back = typo(f, layer)
    mask = None
    if sh is not None and sh.mask and back.getbbox():
        mask = person_mask(img, f"m{f:04d}")
    if back.getbbox():
        img = composite(img, back, mask)
    if s not in (5,) and not (s == 9 and f >= FLASH):
        brand_line(front, s)
    elif s == 5:
        brand_line(front, s)
    img = composite(img, front)

    # Grüne Wischblende braucht beide Bilder
    img2, wipe = transition(f, img)
    if wipe is not None and wipe[0] is not None:
        poly, d = wipe
        other_f = 570 if d < 0 else 569
        other = render_simple(other_f)
        m = np.zeros((H, W), np.uint8)
        cv2.fillPoly(m, [poly], 255)
        img2 = np.where(m[..., None] > 0, other, img2)
    img = img2

    # Licht-Match-Cut: Blitz wird weiß, dann Logo
    d = f - FLASH
    if -6 <= d < 0:
        u = (d + 6) / 6
        img = cv2.addWeighted(img, 1 - u * 0.85, np.full_like(img, 255), u * 0.85, 0)
    elif 0 <= d < 6:
        u = 1 - d / 6
        img = cv2.addWeighted(img, 1 - u * 0.9, np.full_like(img, 250), u * 0.9, 0)

    grain = 2.0 if (s == 9 and f >= FLASH) else 2.8  # feines Korn, kein Rauschen
    return texture(img, f, grain, vignette=not (s == 9 and f >= FLASH))


def render_simple(f):
    img, sh = base_frame(f)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    front, back = typo(f, layer)
    if back.getbbox():
        img = composite(img, back, person_mask(img, f"m{f:04d}") if sh and sh.mask else None)
    brand_line(front, scene_of(f))
    return composite(img, front)


# ---------------------------------------------------------------- Main
STYLE_FRAMES = {1: [30], 2: [80, 130], 3: [200], 4: [255, 285, 315, 345], 5: [420], 6: [470, 540],
                7: [640, 740, 840], 8: [920], 9: [980, 1060]}

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--stills" in args or "--only" in args:
        only = None
        if "--only" in args:
            only = [int(x) for x in args[args.index("--only") + 1].split(",")]
        os.makedirs(os.path.join(OUT, "stills"), exist_ok=True)
        for s, frs in STYLE_FRAMES.items():
            if only and s not in only:
                continue
            for f in frs:
                img = render(f)
                p = os.path.join(OUT, "stills", f"szene_{s}_f{f:03d}.jpg")
                cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
                print(p, flush=True)
        sys.exit()
    a, b = 0, TOTAL
    if "--range" in args:
        a, b = map(int, args[args.index("--range") + 1].split(":"))
    out = os.path.join(OUT, "video_stumm.mp4" if (a, b) == (0, TOTAL) else f"teil_{a}_{b}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for f in range(a, b):
        ff.stdin.write(render(f).tobytes())
        if f % 30 == 0:
            print(f"frame {f}", flush=True)
    ff.stdin.close()
    ff.wait()
    print(out)
