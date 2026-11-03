"""Grober Tonteppich aus den Originalgeräuschen des Footage (nur fürs Preview,
bis Musik/Sprecher/SFX aus Higgsfield kommen).

python3 build/sfx_bed.py <out.wav>
"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from edl import SHOTS, DUR, src_time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
inputs, filters, labels = [], [], []
for s in SHOTS:
    if not s.get("src"):
        continue
    d = s["t1"] - s["t0"]
    span = src_time(s, d) - s["src_in"]
    tempo = max(0.5, min(2.0, span / d))
    i = len(inputs) // 6
    inputs += ["-ss", f"{s['src_in']:.3f}", "-t", f"{span + 0.05:.3f}", "-i", os.path.join(ROOT, "footage", s["src"] + ".mov")]
    vol = 0.0 if s["id"] == "s5" else 0.9
    filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,atempo={tempo:.4f},"
                   f"atrim=0:{d:.3f},afade=t=in:d=0.02,afade=t=out:st={max(d - 0.04, 0):.3f}:d=0.04,"
                   f"volume={vol},adelay={int(s['t0'] * 1000)}|{int(s['t0'] * 1000)}[a{i}]")
    labels.append(f"[a{i}]")
fc = ";".join(filters) + ";" + "".join(labels) + f"amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.9,apad,atrim=0:{DUR}[out]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[out]", out], check=True)
print("ok", out)
