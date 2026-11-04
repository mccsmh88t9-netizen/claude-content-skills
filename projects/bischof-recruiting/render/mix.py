"""Tonmischung: Sprecher (Knox), Musik (120 BPM), Originalton aus dem Footage.

python3 mix.py  -> out/ton_mix.wav und out/bischof_recruiting_final.mp4 (Bild aus out/video_stumm.mp4)
"""
import os
import subprocess
import build

ROOT = build.ROOT
TON = os.path.join(ROOT, "ton")
OUT = build.OUT
VOICE = os.path.join(TON, "sprecher_knox.mp3")
VOICE_EINSTIEG = os.path.join(TON, "sprecher_knox_einstieg.mp3")
VOICE_BENEFITS = os.path.join(TON, "sprecher_knox_benefits_v2.mp3")  # neuer Einstieg (ersetzt „Keine Ausbildung? Egal.“)
MUSIC = os.path.join(TON, "musik_v2.mp3")
MUSIC_OFFSET = 0.064  # erster Beat der Musik liegt 64 ms nach 0 -> auf Raster ziehen
DUR = 36.0

# (Quelle von, bis, Ziel im Video, Tempo) – Sätze aus dem Knox-Take, auf die Schrift-Einschläge gelegt
LINES = [
    (0.00, 1.36, 0.40, 1.0, "einstieg"),   # Bereit für was Neues?
    (1.78, 3.03, 2.00, 1.0, "einstieg"),   # Dann bist du hier richtig.
    (2.58, 4.00, 5.00, 1.0),   # Bei uns zählt nur eins:
    (4.18, 5.66, 6.51, 1.0),   # dass du anpacken willst.  ("anpacken" auf 7,0 s)
    (6.02, 7.08, 8.00, 1.0),   # Große Maschinen.
    (7.35, 8.40, 9.25, 1.0),   # Echte Natur.
    (8.60, 9.61, 10.50, 1.0),  # Bei jedem Wetter.
    (9.91, 11.63, 12.15, 1.0),  # Du brauchst keine Vorkenntnisse.
    (11.88, 13.26, 15.00, 1.0),  # Wir zeigen dir, wie's geht.
    (13.77, 15.10, 19.05, 1.0),  # Moderner Maschinenpark.
    (15.30, 16.29, 20.42, 1.0),  # Faire Vergütung.
    (16.76, 18.71, 21.45, 1.12),  # Jeden Tag ein anderer Einsatz.
    (0.00, 5.70, 23.35, 1.05, "benefits"),  # Dienstrad-Leasing, Urlaubsgeld und Weihnachtsgeld, vermögenswirksame Leistungen.
    (19.04, 20.91, 29.22, 1.0),  # Ob Quereinsteiger oder Profi:
    (21.13, 22.34, 31.12, 1.0),  # Wir wollen dich.
    (22.91, 24.84, 32.35, 1.0),  # Bischof Baumpflege aus Wiefelstede.
    (25.19, 26.09, 34.35, 1.0),  # Jetzt bewerben.
]


def sfx_parts():
    """Originalton je Shot (gleiche Quellstelle wie das Bild). Szene 5 und Stills ohne O-Ton."""
    parts = [("DJI_20260106_111921_962", 0.0, 0.0, 0.5, 0.35)]  # Säge läuft an im Schwarz
    for scene, shots in build.SHOTS.items():
        for sh in shots:
            if sh.still is not None or str(sh.src).endswith(".mp4"):
                continue
            a, b = sh.a / build.FPS, sh.b / build.FPS
            if scene == 9:
                b = build.FLASH / build.FPS + 0.4  # Lkw klingt in den Blitz aus
            parts.append((sh.src, sh.start, a, b - a, 0.02))
    return parts


def main():
    inputs, fc, n = [], [], 0

    def add(path):
        nonlocal n
        inputs.extend(["-i", path])
        n += 1
        return n - 1

    # Sprecher
    vi = add(VOICE)
    ei = add(VOICE_EINSTIEG)
    bi = add(VOICE_BENEFITS)
    vlabels = []
    for i, (s, e, d, tempo, *src) in enumerate(LINES):
        t = f",atempo={tempo}" if tempo != 1.0 else ""
        inp = {"einstieg": ei, "benefits": bi}[src[0]] if src else vi
        fc.append(f"[{inp}:a]atrim={s}:{e},asetpts=PTS-STARTPTS{t},afade=t=in:d=0.02,"
                  f"afade=t=out:st={(e - s) / tempo - 0.04:.3f}:d=0.04,adelay={int(d * 1000)}:all=1[v{i}]")
        vlabels.append(f"[v{i}]")
    fc.append(f"{''.join(vlabels)}amix=inputs={len(vlabels)}:normalize=0,"
              f"highpass=f=90,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
              f"loudnorm=I=-15:TP=-2:LRA=7,apad=whole_dur={DUR},asplit=3[vo][vsc1][vsc2]")

    # Musik: Aufbau 0–12 s, harte Stille 12–15 s, Drop ab 15 s
    mi = add(MUSIC)
    fc.append(f"[{mi}:a]atrim={MUSIC_OFFSET}:{MUSIC_OFFSET + 12},asetpts=PTS-STARTPTS,"
              f"afade=t=out:st=11.96:d=0.04[m1]")
    fc.append(f"[{mi}:a]atrim={MUSIC_OFFSET + 17}:{MUSIC_OFFSET + 25.02},asetpts=PTS-STARTPTS,"
              f"afade=t=in:d=0.005,afade=t=out:st=7.99:d=0.03,adelay=15000:all=1[m2a]")
    fc.append(f"[{mi}:a]atrim={MUSIC_OFFSET + 19}:{MUSIC_OFFSET + 32},asetpts=PTS-STARTPTS,"
              f"afade=t=in:d=0.02,afade=t=out:st={13 - 0.6}:d=0.6,adelay=23000:all=1[m2b]")
    fc.append("[m2a][m2b]amix=inputs=2:normalize=0[m2]")
    # leiser, dumpfer Teppich in der Stille (kein digitales Loch)
    fc.append(f"[{mi}:a]atrim={MUSIC_OFFSET + 12}:{MUSIC_OFFSET + 15},asetpts=PTS-STARTPTS,"
              f"lowpass=f=320,volume=0.07,afade=t=in:d=0.6,afade=t=out:st=2.7:d=0.3,adelay=12000:all=1[mpad]")
    # Musik präsent halten: etwas Bass raus, Präsenz rein (Handylautsprecher), nur sanft unter die Stimme ducken
    fc.append("[m1][m2][mpad]amix=inputs=3:normalize=0,bass=g=-4:f=110,"
              "equalizer=f=2200:t=q:w=1.2:g=4,equalizer=f=5500:t=q:w=1:g=2,volume=0.95[mraw]")
    fc.append("[mraw][vsc1]sidechaincompress=threshold=0.12:ratio=2.5:attack=20:release=300[mus]")

    # Originalton
    slabels = []
    for i, (src, start, dest, dur, fin) in enumerate(sfx_parts()):
        si = add(build.FOOT(src))
        fc.append(f"[{si}:a]atrim={start}:{start + dur},asetpts=PTS-STARTPTS,aformat=channel_layouts=stereo,"
                  f"afade=t=in:d={fin},afade=t=out:st={max(0, dur - 0.03):.3f}:d=0.03,"
                  f"adelay={int(dest * 1000)}:all=1[s{i}]")
        slabels.append(f"[s{i}]")
    fc.append(f"{''.join(slabels)}amix=inputs={len(slabels)}:normalize=0,highpass=f=40,"
              f"loudnorm=I=-22:TP=-5,volume=0.9[sraw]")
    fc.append("[sraw][vsc2]sidechaincompress=threshold=0.05:ratio=4:attack=10:release=200[sfx]")

    stem = os.environ.get("STEM")  # Messmodus: nur eine Spur, ohne Summen-Normalisierung
    weights = {"vo": "1 0 0", "mus": "0 1 0", "sfx": "0 0 1"}.get(stem, "1 1 1")
    norm = "" if stem else "loudnorm=I=-14:TP=-1:LRA=9,"
    fc.append(f"[vo][mus][sfx]amix=inputs=3:normalize=0:weights={weights},apad=whole_dur={DUR},atrim=0:{DUR},"
              f"{norm}aresample=48000,apad=whole_dur={DUR}[out]")

    wav = os.path.join(OUT, "ton_mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
                    "-map", "[out]", "-ac", "2", "-t", str(DUR), wav], check=True)
    if "--nur-ton" in __import__("sys").argv:
        print(wav)
        return
    final = os.path.join(OUT, "bischof_recruiting_final.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(OUT, "video_stumm.mp4"), "-i", wav,
                    "-map", "0:v", "-map", "1:a", "-af", f"apad=whole_dur={DUR}", "-t", str(DUR), "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                    "-maxrate", "10M", "-bufsize", "20M", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", final], check=True)
    print(wav)
    print(final)


if __name__ == "__main__":
    main()
