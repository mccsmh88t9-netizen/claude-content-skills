"""python3 render.py 1 2 3   -> rendert Szenen einzeln nach out/sN.mp4 + Standbilder nach check/
python3 render.py concat  -> fügt alle vorhandenen Szenen zu out/video_stumm.mp4 zusammen"""
import os, sys, time, subprocess
from PIL import Image
from engine import W, H, FPS, Writer, grain, HERE
import scenes

OUT = os.path.join(HERE, 'out'); CHK = os.path.join(HERE, 'check')
os.makedirs(OUT, exist_ok=True); os.makedirs(CHK, exist_ok=True)

def render(n):
    cls = scenes.SCENES[n]
    lp = os.path.join(OUT, f'last_{n - 1}.png')
    prev = Image.open(lp).convert('RGB') if os.path.exists(lp) else None
    t = time.time()
    sc = cls(prev)
    wr = Writer(os.path.join(OUT, f's{n}.mp4'))
    frames_for_sheet = []
    step = max(1, (sc.end - sc.start) // 12)
    last = None
    for g in range(sc.start, sc.end):
        im = sc.frame(g)
        last = im
        fin = grain(im, g)
        wr.write(fin)
        if (g - sc.start) % step == 0 or g == sc.end - 1:
            frames_for_sheet.append((g, fin))
    wr.close()
    last.save(lp.replace(f'last_{n - 1}', f'last_{n}'))
    # Kontaktbogen + Einzelstandbilder
    tw, th = 270, 480
    cols = 6; rows = (len(frames_for_sheet) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw, rows * th), (0, 0, 0))
    for i, (g, im) in enumerate(frames_for_sheet):
        sheet.paste(im.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    sheet.save(os.path.join(CHK, f's{n}_sheet.jpg'), quality=88)
    print(f'Szene {n}: {sc.end - sc.start} Frames in {time.time() - t:.0f}s', flush=True)

def concat():
    lst = os.path.join(OUT, 'list.txt')
    with open(lst, 'w') as f:
        for n in sorted(scenes.SCENES):
            p = os.path.join(OUT, f's{n}.mp4')
            if os.path.exists(p):
                f.write(f"file '{p}'\n")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                    os.path.join(OUT, 'video_stumm.mp4')], check=True)

if __name__ == '__main__':
    for a in sys.argv[1:]:
        if a == 'concat':
            concat()
        else:
            render(int(a))
