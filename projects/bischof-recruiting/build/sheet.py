"""Kontaktbogen aus Standbildern: python3 build/sheet.py out.jpg cols img1.png ..."""
import sys
from PIL import Image, ImageDraw
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
w, h = 360, 640
rows = (len(files) + cols - 1) // cols
o = Image.new("RGB", (cols * (w + 8), rows * (h + 30)), (20, 20, 20)); d = ImageDraw.Draw(o)
for i, f in enumerate(files):
    x, y = (i % cols) * (w + 8), (i // cols) * (h + 30)
    o.paste(Image.open(f).convert("RGB").resize((w, h), Image.LANCZOS), (x, y + 26))
    d.text((x + 4, y + 6), f.split("/")[-1], fill=(255, 255, 0))
    d.line([(x, y + 26 + h - 127), (x + w, y + 26 + h - 127)], fill=(255, 0, 0))  # Safe-Zone-Linie
o.save(out, quality=88)
