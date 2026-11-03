"""Schnittliste (EDL) – Recruiting-Video Bischof Baumpflege.

Zeiten in Sekunden, 30 fps, 120 BPM (1 Schlag = 0,5 s = 15 Frames).
speed: Liste (lokale Zeit, Tempo) – linear interpoliert, ergibt Speed-Ramps.
push:  Zoom am Shot-Anfang/-Ende (1.00 -> 1.05 = 5 % Push-in).
focus: Zoom-Zentrum relativ (x, y) im 1080x1920-Bild.
"""
FPS = 30
DUR = 32.0
W, H = 1080, 1920

SHOTS = [
    # Szene 1 – Kaltstart: Schwarz, dann Säge im Stamm, Späne in Zeitlupe
    dict(id="s1", scene=1, src="DJI_20260106_111921_962_video", t0=0.5, t1=2.0, src_in=0.15,
         speed=[(0, 1.0), (0.35, 1.0), (0.6, 0.35), (1.5, 0.35)], push=(1.04, 1.10), focus=(0.62, 0.45)),
    # Szene 2 – Kletterer am Greifer schwebt hoch, EGAL. hinter ihm
    dict(id="s2", scene=2, src="IMG_0209", t0=2.0, t1=5.0, src_in=11.2,
         speed=[(0, 1.3)], push=(1.00, 1.05), focus=(0.55, 0.40), mask=True),
    # Szene 3 – Blick aus dem Korb auf Team + Häcksler
    dict(id="s3", scene=3, src="IMG_0469", t0=5.0, t1=8.0, src_in=3.6,
         speed=[(0, 1.0)], push=(1.02, 1.07), focus=(0.5, 0.5)),
    # Szene 4 – Stakkato, je 2 Schläge, Whip Pans
    dict(id="s4a", scene=4, src="IMG_0472", t0=8.0, t1=9.0, src_in=2.75,
         speed=[(0, 1.4), (0.35, 0.45), (1.0, 0.45)], push=(1.03, 1.08), focus=(0.6, 0.35)),
    dict(id="s4b", scene=4, src="DJI_20260131_090238_114_video", t0=9.0, t1=10.0, src_in=1.0,
         speed=[(0, 1.0)], push=(1.05, 1.10), focus=(0.55, 0.42)),
    dict(id="s4c", scene=4, src="IMG_0477", t0=10.0, t1=11.0, src_in=3.9,
         speed=[(0, 1.0)], push=(1.02, 1.07), focus=(0.5, 0.45)),
    dict(id="s4d", scene=4, src="DJI_20260131_091040_966_video", t0=11.0, t1=12.0, src_in=0.3,
         speed=[(0, 1.2)], push=(1.00, 1.05), focus=(0.4, 0.4)),
    # Szene 5 – Anlernszene (Seedance 2.5) – bis zur Erzeugung Platzhalter
    dict(id="s5", scene=5, src=None, t0=12.0, t1=17.0),
    # Szene 6 – Beat-Drop
    dict(id="s6a", scene=6, src="IMG_0474", t0=17.0, t1=19.0, src_in=3.5,
         speed=[(0, 1.0)], push=(1.02, 1.07), focus=(0.55, 0.55)),
    dict(id="s6b", scene=6, src="DJI_20260106_111921_962_video", t0=19.0, t1=21.0, src_in=4.45,
         speed=[(0, 1.0)], push=(1.00, 1.05), focus=(0.55, 0.6)),
    # Szene 7 – Fuhrpark-Fotos mit Parallax
    dict(id="s7a", scene=7, still="man_lkw", t0=21.0, t1=23.0, push=(1.04, 1.09), focus=(0.5, 0.5)),
    dict(id="s7b", scene=7, still="teleskoplader", t0=23.0, t1=25.0, push=(1.04, 1.09), focus=(0.5, 0.5)),
    # Szene 8 – Kletterer hoch oben
    dict(id="s8", scene=8, src="IMG_0209", t0=25.0, t1=27.0, src_in=14.4,
         speed=[(0, 1.0)], push=(1.06, 1.12), focus=(0.6, 0.42), mask=True),
    # Szene 9 – Lkw-Front, Licht wird Match Cut aufs Logo
    dict(id="s9", scene=9, src="IMG_0460", t0=27.0, t1=29.6, src_in=4.9,
         speed=[(0, 1.0)], push=(1.00, 1.04), focus=(0.5, 0.5)),
    dict(id="end", scene=9, src=None, t0=29.6, t1=32.0),
]


def src_time(shot, lt):
    """Quellzeit für lokale Zeit lt (Integral der Tempokurve)."""
    sp = shot["speed"]
    def v(x):
        if x <= sp[0][0]:
            return sp[0][1]
        for (a, va), (b, vb) in zip(sp, sp[1:]):
            if x <= b:
                return va + (vb - va) * (x - a) / (b - a)
        return sp[-1][1]
    n = max(1, int(lt * 240))
    dt = lt / n
    return shot["src_in"] + sum(v((i + 0.5) * dt) * dt for i in range(n))


def shot_at(t):
    for s in SHOTS:
        if s["t0"] <= t < s["t1"]:
            return s
    return None if t < SHOTS[0]["t0"] else SHOTS[-1]
