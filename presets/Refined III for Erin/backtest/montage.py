"""Stack all chart previews into a single before/after comparison image."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "output"

names = ["Refined III.1", "Refined III.2", "Refined III.3"]
chart_before = np.asarray(Image.open(OUT / "_chart_before.png").convert("RGB"))
rows = [chart_before]
for n in names:
    img = np.asarray(Image.open(OUT / f"{n} - chart.png").convert("RGB"))
    # the file is already [before | gap | after], we want just the after half
    after = img[:, chart_before.shape[1] + 12:]
    rows.append(after)

gap = np.full((chart_before.shape[0], 12, 3), 32, dtype=np.uint8)
montage = np.concatenate([rows[0], gap, rows[1], gap, rows[2], gap, rows[3]], axis=1)

label_h = 28
labels_strip = np.full((label_h, montage.shape[1], 3), 24, dtype=np.uint8)
m_img = Image.fromarray(np.concatenate([labels_strip, montage], 0))
draw = ImageDraw.Draw(m_img)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
except OSError:
    font = ImageFont.load_default()
w = chart_before.shape[1]
for i, label in enumerate(["Original"] + names):
    x = i * (w + 12) + 6
    draw.text((x, 6), label, fill=(230, 230, 230), font=font)
m_img.save(OUT / "_montage_chart.png")
print(f"Wrote {OUT.name}/_montage_chart.png  ({m_img.size[0]}x{m_img.size[1]})")
