"""Vorbereitung: Quellframes extrahieren, Personenmasken (rembg u2net), Stills freistellen.

python3 build/prep.py <cache_dir>
"""
import os, sys, subprocess, glob
import numpy as np
import cv2
from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(__file__))
from edl import SHOTS, FPS, W, H, src_time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = sys.argv[1]


def extract(shot):
    out = os.path.join(CACHE, "src", shot["id"])
    if os.path.isdir(out) and glob.glob(out + "/*.jpg"):
        return out
    os.makedirs(out, exist_ok=True)
    dur = shot["t1"] - shot["t0"]
    span = src_time(shot, dur) - shot["src_in"] + 0.2
    vf = f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{shot['src_in']:.3f}",
                    "-i", os.path.join(ROOT, "footage", shot["src"] + ".mov"),
                    "-t", f"{span:.3f}", "-vf", vf, "-q:v", "2",
                    os.path.join(out, "%04d.jpg")], check=True)
    return out


def masks(shot, session, remove):
    src = os.path.join(CACHE, "src", shot["id"])
    out = os.path.join(CACHE, "mask", shot["id"])
    os.makedirs(out, exist_ok=True)
    for f in sorted(glob.glob(src + "/*.jpg")):
        m = os.path.join(out, os.path.basename(f).replace(".jpg", ".png"))
        if os.path.exists(m):
            continue
        im = Image.open(f)
        remove(im, session=session, only_mask=True).save(m)


def still(shot, session, remove):
    out = os.path.join(CACHE, "still")
    os.makedirs(out, exist_ok=True)
    name = shot["still"]
    if os.path.exists(os.path.join(out, name + "_mask.png")):
        return
    im = ImageOps.exif_transpose(Image.open(os.path.join(ROOT, "stills", name + ".jpg"))).convert("RGB")
    # auf 9:16 mit Reserve für Pan (Breite 1.25x)
    tw, th = int(W * 1.25), int(H * 1.12)
    s = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    fx = {"man_lkw": 0.42, "teleskoplader": 0.48}.get(name, 0.5)
    x0 = int(min(max(fx * im.width - tw / 2, 0), im.width - tw))
    y0 = int((im.height - th) / 2)
    im = im.crop((x0, y0, x0 + tw, y0 + th))
    im.save(os.path.join(out, name + ".jpg"), quality=95)
    m = np.asarray(remove(im, session=session, only_mask=True))
    Image.fromarray(m).save(os.path.join(out, name + "_mask.png"))
    # Hintergrund unter dem Vordergrund auffüllen (gegen Geisterkanten beim Parallax)
    a = np.asarray(im)
    hole = cv2.dilate((m > 40).astype(np.uint8) * 255, np.ones((41, 41), np.uint8))
    small = cv2.resize(a, None, fx=0.25, fy=0.25)
    hs = cv2.resize(hole, (small.shape[1], small.shape[0]))
    fill = cv2.inpaint(small, hs, 9, cv2.INPAINT_TELEA)
    fill = cv2.resize(fill, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_CUBIC)
    k = (cv2.GaussianBlur(hole, (61, 61), 0) / 255.0)[..., None]
    bg = (a * (1 - k) + fill * k).astype(np.uint8)
    Image.fromarray(bg).save(os.path.join(out, name + "_bg.jpg"), quality=95)


if __name__ == "__main__":
    from rembg import new_session, remove
    session = new_session("u2net")
    for s in SHOTS:
        if s.get("src"):
            print("extract", s["id"], extract(s))
            if s.get("mask"):
                masks(s, session, remove)
                print("  masks ok")
        if s.get("still"):
            still(s, session, remove)
            print("still", s["id"])
