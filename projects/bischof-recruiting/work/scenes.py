"""Szenen des Recruiting-Videos. Alle Zeiten in globalen Frames (30 fps, 1 Schlag = 15 Frames)."""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *

X0 = 56          # linke Satzkante
MAXW = W - 2 * X0
SAFE_BOTTOM = H - 380

def stack(words_spec, y, size, gap=26):
    """Mehrere Zeilen untereinander, gleiche Größe. words_spec: [(txt, hit, color)]"""
    out = []
    for txt, hit, col in words_spec:
        w = Word(txt, X0, y, size, hit, color=col)
        out.append(w); y += w.th + gap
    return out

class Scene:
    n = 0; start = 0; end = 0
    def __init__(self, prev_last=None):
        self.prev = prev_last
    def frame(self, g):
        raise NotImplementedError

# ------------------------------------------------------------------ Szene 1
class S1(Scene):
    """0:00–0:02 Schwarz + Anwerfzug, dann Säge im Stamm, Späne in Zeitlupe."""
    n, start, end = 1, 0, 60
    BLACK = 12
    def __init__(self, prev=None):
        super().__init__(prev)
        self.src = decode('DJI_20260106_111921_962_video', 0.0, 1.0, minterp=True)
        s = fit_size('AUSBILDUNG?', 'anton', MAXW, 330)
        self.words = stack([('KEINE', 15, BONE), ('AUSBILDUNG?', 17, FLEET)], 330, s, 22)
        for w in self.words:
            w.out = self.end - 3
    def idx(self, j):
        # Speed-Ramp: 6 Frames Echtzeit (60p -> jeder 2.), dann 0,5x Zeitlupe
        return 2 * j if j < 6 else 12 + (j - 6)
    def frame(self, g):
        if g < self.BLACK:
            return Image.new('RGB', (W, H), (0, 0, 0))
        j = g - self.BLACK
        z = lerp(1.04, 1.10, j / 47)
        sx, sy = shake(g, [15], amp=9)
        img = self.src
        if g >= self.end - 4:  # Match Cut: Aufwärts-Whip raus
            k = g - (self.end - 4)
            dy0, dy1 = [0, 120, 380, 800][k], [120, 380, 800, 1300][k]
            im = whip(view(sample(img, self.idx(j)), z, 0.5, 0.45, sx, sy), -dy0, -dy1, axis=0)
        else:
            im = view(sample(img, self.idx(j)), z, 0.5, 0.45, sx, sy)
        im = fin_bg(im)
        for w in self.words:
            w.draw(im, g, sx * 0.5, sy * 0.5)
        header(im, 1)
        return im

# ------------------------------------------------------------------ Szene 2
class S2(Scene):
    """0:02–0:05 Kletterer schwebt hoch, EGAL. hinter ihm maskiert."""
    n, start, end = 2, 60, 150
    def __init__(self, prev=None):
        super().__init__(prev)
        self.src = decode('IMG_0209', 11.0, 3.1)
        self.kick = Kick('Keine Ausbildung?', 62, 300, 60, size=62)
        self.egal = Word('EGAL.', 50, 412, 500, 64, color=FLEET)
    def frame(self, g):
        j = g - self.start
        z = lerp(1.0, 1.05, j / 89); cy = lerp(0.50, 0.47, j / 89)
        sx, sy = shake(g, [64], amp=8)
        if j < 4:  # Match Cut: Aufwärtsbewegung rein
            dy0, dy1 = [-700, -320, -120, -30][j], [-320, -120, -30, 0][j]
            im = whip(view(self.src[j], z, 0.5, cy, sx, sy), -dy0, -dy1, axis=0)
        else:
            im = view(self.src[j], z, 0.5, cy, sx, sy)
        im = fin_bg(im)
        m = person_mask(im, f's2_{j}')
        base = im.copy()
        self.egal.draw(im, g, sx * 0.3, sy * 0.3)
        im = Image.composite(base, im, m)   # Person vor die Schrift
        self.kick.draw(im, g)
        header(im, 2)
        return im

# ------------------------------------------------------------------ Szene 3
class S3(Scene):
    """0:05–0:08 Blick aus dem Hubsteiger-Korb, ANPACKEN. + grüner Balken. Rein: Maske über Korbrand."""
    n, start, end = 3, 150, 240
    def __init__(self, prev=None):
        super().__init__(prev)
        self.src = decode('IMG_0469', 4.3, 3.1)
        self.kick = Kick('Bei uns zählt nur eins:', 62, 1000, 162, size=58)
        s = fit_size('ANPACKEN.', 'anton', MAXW, 300)
        self.word = Word('ANPACKEN.', X0, 1070, s, 195, color=BONE)
        self.bar = Bar(X0 + 4, 1070 + self.word.th + 34, 300, 20, 199)
    def frame(self, g):
        j = g - self.start
        z = lerp(1.02, 1.08, j / 89)
        sx, sy = shake(g, [195], amp=7)
        im = fin_bg(view(self.src[j], z, 0.5, 0.5, sx, sy))
        self.kick.draw(im, g)
        self.word.draw(im, g, sx * 0.4, sy * 0.4)
        self.bar.draw(im, g)
        header(im, 3)
        if j < 7 and self.prev is not None:  # Korbrand wischt von unten nach oben durchs Bild
            u = ease_in((j + 1) / 7)
            y0 = lerp(H + 250, -420, u)
            slope = -0.20
            yy = np.arange(H)[:, None]; xx = np.arange(W)[None, :]
            edge = y0 + slope * (xx - W / 2)
            new_mask = (yy > edge).astype(np.uint8) * 255
            prev = self.prev
            # Vorheriges Bild wird nach oben weggeschoben
            prev = view(prev, 1.0, 0.5, 0.5, 0, lerp(0, 260, u))
            out = Image.composite(im, prev, Image.fromarray(new_mask))
            # Korbrand: heller Holm mit dunkler Unterkante, unscharf
            rim = Image.new('L', (W, H), 0)
            d = ImageDraw.Draw(rim)
            poly = [(0, y0 + slope * (-W / 2) - 70), (W, y0 + slope * (W / 2) - 70),
                    (W, y0 + slope * (W / 2) + 70), (0, y0 + slope * (-W / 2) + 70)]
            d.polygon(poly, fill=255)
            rim = rim.filter(ImageFilter.GaussianBlur(18))
            out.paste(Image.new('RGB', (W, H), (196, 200, 204)), (0, 0), rim)
            sh = Image.new('L', (W, H), 0)
            d = ImageDraw.Draw(sh)
            poly2 = [(0, y0 + slope * (-W / 2) + 60), (W, y0 + slope * (W / 2) + 60),
                     (W, y0 + slope * (W / 2) + 150), (0, y0 + slope * (-W / 2) + 150)]
            d.polygon(poly2, fill=150)
            sh = sh.filter(ImageFilter.GaussianBlur(30))
            out.paste(Image.new('RGB', (W, H), (8, 12, 10)), (0, 0), sh)
            im = out
        return im

# ------------------------------------------------------------------ Szene 4
class S4(Scene):
    """0:08–0:12 Stakkato, je 1 Sekunde, Whip Pans."""
    n, start, end = 4, 240, 360
    SHOT = 30
    def __init__(self, prev=None):
        super().__init__(prev)
        self.shots = [
            # (frames, idx(j), z0, z1, cx, cy)
            (decode('IMG_0472', 1.8, 1.9), lambda j: j * 2.2 if j < 14 else 30.8 + (j - 14) * 0.6, 1.0, 1.06, 0.5, 0.45),
            (decode('DJI_20260131_090238_114_video', 3.0, 1.2, cx=0.54, cy=0.47, zoom=1.8), lambda j: j, 1.0, 1.05, 0.5, 0.5),
            (decode('IMG_0477', 4.4, 1.2), lambda j: j, 1.02, 1.07, 0.5, 0.5),
            (decode('DJI_20260131_091040_966_video', 0.6, 1.2, cx=0.42, cy=0.42, zoom=1.3), lambda j: j, 1.0, 1.05, 0.5, 0.5),
        ]
        s = fit_size('MASCHINEN.', 'anton', MAXW, 300)
        y = 330
        self.texts = [
            stack([('GROSSE', 242, BONE), ('MASCHINEN.', 256, FLEET)], y, s),
            stack([('ECHTE', 302, BONE), ('NATUR.', 312, FLEET)], y, s),
            stack([('JEDES', 332, BONE), ('WETTER.', 342, FLEET)], y, s),
        ]
        for grp, out in zip(self.texts, [298, 328, None]):
            for w in grp:
                w.out = out
    def shot_frame(self, k, j, dx=0):
        src, idx, z0, z1, cx, cy = self.shots[k]
        return view(sample(src, idx(j)), lerp(z0, z1, j / (self.SHOT - 1)), cx, cy, dx, 0)
    def frame(self, g):
        j = g - self.start
        k, jj = divmod(j, self.SHOT)
        sx, sy = shake(g, [242, 256, 302, 312, 332, 342], amp=6, decay=4)
        d = 1 if k % 2 == 0 else -1
        # Whip raus (letzte 2 Frames eines Shots, außer dem letzten Shot)
        if k < 3 and jj >= self.SHOT - 2:
            a = [(0, 260), (260, 760)][jj - (self.SHOT - 2)]
            im = whip(self.shot_frame(k, jj), -d * a[0], -d * a[1])
        elif jj < 2 and (k > 0 or self.prev is not None):
            a = [(-760, -260), (-260, 0)][jj]
            if k == 0:  # Whip aus Szene 3 heraus
                pd = -1
                if jj == 0:
                    a1 = np.asarray(whip(self.prev, 0, 700), np.float32)
                    a2 = np.asarray(whip(self.shot_frame(0, 0), -900, -300), np.float32)
                    im = Image.fromarray(((a1 + a2) / 2).astype(np.uint8))
                else:
                    im = whip(self.shot_frame(0, 1), -300, 0)
            else:
                pd = 1 if (k - 1) % 2 == 0 else -1
                im = whip(self.shot_frame(k, jj), -pd * a[0], -pd * a[1])
        else:
            im = self.shot_frame(k, jj, sx)
        im = fin_bg(im)
        for grp in self.texts:
            for w in grp:
                w.draw(im, g, sx * 0.4, sy * 0.4)
        header(im, 4)
        return im

SCENES = {1: S1, 2: S2, 3: S3, 4: S4}

# ------------------------------------------------------------------ Szene 5
class S5(Scene):
    """0:12–0:17 Anlernszene (Seedance 2.5). Bis der Clip da ist: Platzhalter, Schrift ist final."""
    n, start, end = 5, 360, 510
    CLIP = 'seedance_s5.mp4'
    def __init__(self, prev=None):
        super().__init__(prev)
        p = os.path.join(ROOT, 'footage', self.CLIP)
        self.src = decode(self.CLIP, 0.0, 5.0) if os.path.exists(p) else None
        if self.src is None:
            bg = Image.new('RGB', (W, H), DEEP)
            d = ImageDraw.Draw(bg)
            for k in range(-H, W + H, 60):
                d.line([(k, 0), (k - H * 0.6, H)], fill=(16, 40, 24), width=18)
            f = font('bc8', 40)
            for i, t in enumerate(['SZENE 5 · ANLERNSZENE', 'SEEDANCE 2.5 · PLATZHALTER',
                                   'Kollege zeigt Griff an der Säge / Knoten', 'Nahaufnahme Hände']):
                tw = text_width(t, f, 3)
                draw_tracked(d, ((W - tw) / 2, 1150 + i * 62), t, f, (90, 130, 100) if i > 1 else (150, 190, 160), 3)
            self.ph = bg
        s = fit_size('VORKENNTNISSE.', 'anton', MAXW, 300)
        self.words = stack([('DU BRAUCHST', 372, BONE), ('KEINE', 390, BONE), ('VORKENNTNISSE.', 394, FLEET)], 330, s)
    def frame(self, g):
        j = g - self.start
        if self.src is not None:
            im = view(sample(self.src, j), lerp(1.0, 1.05, j / 149))
        else:
            im = view(self.ph, lerp(1.0, 1.04, j / 149))
        im = fin_bg(im)
        for w in self.words:
            w.draw(im, g)
        header(im, 5)
        return im

# ------------------------------------------------------------------ Szene 6
class S6(Scene):
    """0:17–0:21 Beat-Drop: Äste ziehen, Stammstück fällt."""
    n, start, end = 6, 510, 630
    def __init__(self, prev=None):
        super().__init__(prev)
        self.a = decode('IMG_0474', 2.4, 2.1)
        self.b = decode('DJI_20260106_111921_962_video', 4.5, 2.08)
        s1 = fit_size('WIR ZEIGEN DIR,', 'anton', MAXW, 300)
        s2 = fit_size('WIE’S GEHT.', 'anton', MAXW, 330)
        w1 = Word('WIR ZEIGEN DIR,', X0, 330, s1, 513, color=BONE)
        w2 = Word('WIE’S GEHT.', X0, 330 + w1.th + 26, s2, 540, color=FLEET)
        self.words = [w1, w2]
    def frame(self, g):
        j = g - self.start
        sx, sy = shake(g, [510, 540, 570], amp=14, decay=5)
        if j < 60:
            im = view(sample(self.a, j), lerp(1.0, 1.06, j / 59), 0.5, 0.5, sx, sy)
        else:
            k = j - 60
            im = view(sample(self.b, k), lerp(1.03, 1.09, k / 59), 0.5, 0.5, sx, sy)
        im = fin_bg(im)
        if j < 3:  # Drop-Blitz
            a = np.asarray(im, np.float32)
            im = Image.fromarray(np.clip(a * [1.6, 1.35, 1.2][j] + [40, 20, 8][j], 0, 255).astype(np.uint8))
        for w in self.words:
            w.draw(im, g, sx * 0.4, sy * 0.4)
        header(im, 6)
        return im

# ------------------------------------------------------------------ Szene 7
class S7(Scene):
    """0:21–0:25 MAN-Lkw + Teleskoplader mit Parallax, Benefit-Chips. Rein: grüne Wischblende."""
    n, start, end = 7, 630, 750
    def __init__(self, prev=None):
        super().__init__(prev)
        self.stills = []
        for fname, box, z0, z1, cx0, cx1 in [('man_lkw.jpg', (0, 0, 0.75, 1), 1.0, 1.03, 0.5, 0.48),
                                              ('teleskoplader.jpg', (0.18, 0, 0.82, 1), 1.0, 1.04, 0.40, 0.56)]:
            img = Image.fromarray(load_still(fname, box))
            m = person_mask(img, 'still_' + fname)
            self.stills.append((img, m.resize(img.size), z0, z1, cx0, cx1))
        y = 1110
        self.chips = []
        for txt, hit in [('Moderner Maschinenpark', 645), ('Faire Vergütung', 675), ('Vielfältige Einsätze', 705)]:
            c = Chip(txt, X0, y, hit - 3, size=58); self.chips.append(c); y += c.h + 26
    def still_frame(self, k, u):
        img, m, z0, z1, cx0, cx1 = self.stills[k]
        z = lerp(z0, z1, u); cx = lerp(cx0, cx1, u)
        bg = view(img, z, cx, 0.5)
        fg = view(img, z, cx, 0.5); fm = view(m.convert('RGB'), z, cx, 0.5).convert('L')
        kf = lerp(1.0, 1.06, ease_io(u))      # Vordergrund wächst schneller
        if kf > 1.001:
            nw, nh = int(W * kf), int(H * kf)
            ox, oy = (nw - W) // 2, int((nh - H) * 0.55)
            fg = fg.resize((nw, nh), Image.BICUBIC).crop((ox, oy, ox + W, oy + H))
            fm = fm.resize((nw, nh), Image.BICUBIC).crop((ox, oy, ox + W, oy + H))
        return Image.composite(fg, bg, fm)
    def frame(self, g):
        j = g - self.start
        k, jj = divmod(j, 60)
        im = fin_bg(self.still_frame(k, jj / 59))
        if j >= 117:  # Zoom-Schnitt raus
            q = j - 116
            im = mblur(lambda u: view(im, 1 + 0.12 * (q - 1 + u)), 6)
        for c in self.chips:
            c.draw(im, g)
        header(im, 7)
        if j < 9 and self.prev is not None:  # grüne Wischblende
            u = ease_io((j + 1) / 9)
            p = lerp(-500, W + 900, u)
            t = math.tan(math.radians(18))
            yy = np.arange(H)[:, None]; xx = np.arange(W)[None, :]
            xe = xx - (p + (yy - H / 2) * t)
            out = np.where((xe < -320)[..., None], np.asarray(im), np.asarray(self.prev))
            out = np.where(((xe >= -320) & (xe < -150))[..., None], np.array(FOREST, np.uint8), out)
            out = np.where(((xe >= -150) & (xe < 0))[..., None], np.array(FLEET, np.uint8), out)
            im = Image.fromarray(out.astype(np.uint8))
        return im

# ------------------------------------------------------------------ Szene 8
class S8(Scene):
    """0:25–0:27 Kletterer hoch oben. QUEREINSTEIGER? PROFI? BEIDE. Rein: Zoom-Schnitt."""
    n, start, end = 8, 750, 810
    def __init__(self, prev=None):
        super().__init__(prev)
        self.src = decode('IMG_0209', 14.6, 2.1, cx=0.58, cy=0.48, zoom=1.3)
        s = fit_size('QUEREINSTEIGER?', 'anton', MAXW, 300)
        w1 = Word('QUEREINSTEIGER?', X0, 330, s, 753, color=BONE)
        w2 = Word('PROFI?', X0, 330 + w1.th + 22, s, 768, color=BONE)
        w3 = Word('BEIDE.', X0 - 4, 330 + 2 * (w1.th + 22) + 6, fit_size('BEIDE.', 'anton', MAXW * 0.78, 400), 783, color=FLEET)
        self.words = [w1, w2, w3]
    def frame(self, g):
        j = g - self.start
        sx, sy = shake(g, [783], amp=10)
        z = lerp(1.0, 1.05, j / 59)
        if j < 4:
            zz = [1.45, 1.22, 1.08, 1.02][j]
            im = mblur(lambda u: view(self.src[j], z * lerp(zz + 0.12, zz, u), 0.5, 0.5, sx, sy), 6)
        else:
            im = view(self.src[j], z, 0.5, 0.5, sx, sy)
        im = fin_bg(im)
        m = person_mask(im, f's8_{j}')
        base = im.copy()
        for w in self.words:
            w.draw(im, g, sx * 0.4, sy * 0.4)
        im = Image.composite(base, im, m)
        header(im, 8)
        return im

# ------------------------------------------------------------------ Szene 9
class CTA:
    def __init__(self, txt, cx, y, hit, size=96):
        f = font('anton', size); tr = size * 0.01
        tw = int(text_width(txt, f, tr)); bb = f.getbbox('H')
        px, py = int(size * 0.55), int(size * 0.36)
        w, h = tw + 2 * px, (bb[3] - bb[1]) + 2 * py
        self.img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.img)
        d.polygon([(0, 0), (w, 0), (w, int(h * 0.70)), (int(w * 0.94), h), (0, h)], fill=FLEET + (255,))
        draw_tracked(d, (px, py - bb[1]), txt, f, DEEP + (255,), tr)
        self.x, self.y, self.hit = cx - w / 2, y, hit
    def draw(self, frame, i):
        st = slam(i - (self.hit - 3))
        if st is None:
            return
        s, op = st
        img = self.img
        if abs(s - 1) > 1e-3:
            img = img.resize((int(img.width * s), int(img.height * s)), Image.BILINEAR)
        x = int(self.x + (self.img.width - img.width) / 2); y = int(self.y + (self.img.height - img.height) / 2)
        a = img.getchannel('A')
        if op < 1:
            a = Image.eval(a, lambda v: int(v * op))
        frame.paste(img.convert('RGB'), (x, y), a)

class S9(Scene):
    """0:27–0:32 Lkw-Front, Push-in auf den Blitzer, Licht-Match-Cut auf Logo, CTA."""
    n, start, end = 9, 810, 960
    FLASH = 870
    def __init__(self, prev=None):
        super().__init__(prev)
        self.src = decode('IMG_0460', 0.0, 5.4)
        # Endkarte
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - 760) / H) ** 2)
        c0 = np.array([30, 78, 44], np.float32); c1 = np.array(DEEP, np.float32)
        t = np.clip(r / 0.75, 0, 1)[..., None] ** 1.2
        self.card = Image.fromarray((c0 * (1 - t) + c1 * t).astype(np.uint8))
        lg = LOGO.resize((560, 560), Image.LANCZOS)
        self.logo = lg
        sh = Image.new('L', (W, H), 0); sh.paste(lg.getchannel('A'), ((W - 560) // 2, 470))
        self.logo_sh = Image.eval(sh.filter(ImageFilter.GaussianBlur(40)), lambda v: int(v * 0.55))
        glow = Image.new('L', (W, H), 0)
        ImageDraw.Draw(glow).ellipse([W / 2 - 420, 750 - 420, W / 2 + 420, 750 + 420], fill=255)
        self.glow = glow.filter(ImageFilter.GaussianBlur(160))
        f = font('bc8', 46); t1 = 'BAUMPFLEGE AUS WIEFELSTEDE'
        self.sub = Image.new('L', (W, 80), 0)
        draw_tracked(ImageDraw.Draw(self.sub), ((W - text_width(t1, f, 7)) / 2, 10), t1, f, 255, 7)
        self.cta = CTA('JETZT BEWERBEN', W / 2, 1150, 900, size=104)
        f2 = font('bc8', 58); t2 = 'bischof-baumpflege.de/jobs'
        self.url = Image.new('L', (W, 90), 0)
        draw_tracked(ImageDraw.Draw(self.url), ((W - text_width(t2, f2, 1.5)) / 2, 8), t2, f2, 255, 1.5)
    def truck(self, j):
        u = j / 59
        idx = 156 - (156 - 8) * (1 - (1 - u) ** 3)   # rückwärts, Speed-Ramp: schnell -> langsam
        return view(sample(self.src, idx), lerp(1.0, 1.10, u), 0.5, 0.42)
    def frame(self, g):
        j = g - self.start
        if g < self.FLASH:
            im = fin_bg(self.truck(j))
            header(im, 9)
            d = g - (self.FLASH - 8)
            if d >= 0:  # Blitzer glüht auf und füllt das Bild
                u = (d + 1) / 8
                gl = Image.new('L', (W, H), 0)
                rr = lerp(80, 1500, ease_in(u))
                cy = 0.42 * H
                ImageDraw.Draw(gl).ellipse([W / 2 - rr * 1.6, cy - rr * 0.5, W / 2 + rr * 1.6, cy + rr * 0.5], fill=255)
                gl = gl.filter(ImageFilter.GaussianBlur(40 + 80 * u))
                gl = Image.eval(gl, lambda v: int(v * min(1, 0.4 + u)))
                im.paste(Image.new('RGB', (W, H), (248, 252, 240)), (0, 0), gl)
            return im
        k = g - self.FLASH
        im = self.card.copy()
        # weiches Licht hinter dem Logo, klingt ab
        gop = lerp(0.55, 0.18, ease_out(clamp01(k / 30)))
        im.paste(Image.new('RGB', (W, H), FLEET), (0, 0), Image.eval(self.glow, lambda v: int(v * gop)))
        st = slam(k)
        s, op = st if st else (1, 1)
        lg = self.logo if abs(s - 1) < 1e-3 else self.logo.resize((int(560 * s), int(560 * s)), Image.BILINEAR)
        im.paste(Image.new('RGB', (W, H), (0, 0, 0)), (0, 18), self.logo_sh)
        a = lg.getchannel('A')
        if op < 1:
            a = Image.eval(a, lambda v: int(v * op))
        im.paste(lg.convert('RGB'), (int(W / 2 - lg.width / 2), int(750 - lg.height / 2)), a)
        so = clamp01((g - 884) / 6)
        if so > 0:
            im.paste(Image.new('RGB', (W, 80), BONE), (0, int(1060 + 20 * (1 - ease_out(so)))),
                     Image.eval(self.sub, lambda v: int(v * so * 0.85)))
        self.cta.draw(im, g)
        uo = clamp01((g - 912) / 6)
        if uo > 0:
            im.paste(Image.new('RGB', (W, 90), BONE), (0, int(1330 + 24 * (1 - ease_out(uo)))),
                     Image.eval(self.url, lambda v: int(v * uo)))
        im = fin_bg(im, top=False)
        if k < 8:  # Weiß klingt aus
            wa = int(255 * (1 - ease_out((k + 1) / 8)))
            im.paste(Image.new('RGB', (W, H), (248, 252, 240)), (0, 0), Image.new('L', (W, H), wa))
        return im

SCENES = {1: S1, 2: S2, 3: S3, 4: S4, 5: S5, 6: S6, 7: S7, 8: S8, 9: S9}
