"""Grading 'Nordischer Winter' als 3D-LUT (.cube) + Hilfsfunktionen.
Kühle Schatten, harter Kontrast, Highlights/Himmel komprimiert, Grün und Orange satt."""
import numpy as np, colorsys, sys

def grade(rgb):
    x = np.clip(rgb, 0, 1).astype(np.float64)
    L = x @ np.array([0.2126, 0.7152, 0.0722])
    # 1) Highlights/Himmel komprimieren (Soft-Knee ab 0.62)
    k = 0.62
    Lc = np.where(L > k, k + (1 - k) * np.tanh((L - k) / (1 - k) * 1.1) / np.tanh(1.1) * 0.9, L)
    x = x * (Lc / np.maximum(L, 1e-5))[..., None]
    # 2) harter Kontrast: S-Kurve um 0.42, Schwarz leicht abgesenkt
    def s(v):
        p = 0.42
        lo = p * (v / p) ** 1.45
        hi = 1 - (1 - p) * ((1 - v) / (1 - p)) ** 1.25
        return np.where(v < p, lo, hi)
    x = s(np.clip(x, 0, 1))
    x = np.clip((x - 0.025) / 0.975, 0, 1)
    # 3) Farbe: HSV, Grün und Orange satt, Rest entsättigt
    flat = x.reshape(-1, 3)
    out = np.empty_like(flat)
    for i, (r, g, b) in enumerate(flat):
        h, sat, v = colorsys.rgb_to_hsv(r, g, b)
        hd = h * 360
        def bump(c, w):
            d = min(abs(hd - c), 360 - abs(hd - c))
            return max(0.0, 1 - d / w)
        green = bump(100, 50)   # Fuhrpark-Grün / Vegetation
        orange = bump(22, 22)   # Schnittschutz
        red = bump(355, 15)
        f = 0.78 + 0.55 * green + 0.55 * orange + 0.25 * red
        sat = min(1.0, sat * f)
        # Grün leicht Richtung Gelbgrün ziehen (Fuhrpark-Grün #7DC243 ~ 93°)
        if green > 0:
            hd = hd + (93 - hd) * 0.25 * green
        out[i] = colorsys.hsv_to_rgb((hd % 360) / 360, sat, v)
    x = out.reshape(x.shape)
    # 4) kühle Schatten, minimal kühle Lichter
    L = x @ np.array([0.2126, 0.7152, 0.0722])
    ws = np.clip(1 - L / 0.5, 0, 1) ** 1.5
    x = x + ws[..., None] * np.array([-0.040, -0.006, 0.052])
    wh = np.clip((L - 0.6) / 0.4, 0, 1)
    x = x + wh[..., None] * np.array([-0.014, 0.000, 0.016])
    return np.clip(x, 0, 1)

def write_cube(path, n=33):
    g = np.linspace(0, 1, n)
    b, gg, r = np.meshgrid(g, g, g, indexing='ij')  # r schnellste Achse
    rgb = np.stack([r, gg, b], -1).reshape(-1, 3)
    out = grade(rgb)
    with open(path, 'w') as f:
        f.write('TITLE "Nordischer Winter"\nLUT_3D_SIZE %d\n' % n)
        for v in out:
            f.write('%.6f %.6f %.6f\n' % tuple(v))

if __name__ == '__main__':
    write_cube(sys.argv[1] if len(sys.argv) > 1 else 'nordic.cube')
