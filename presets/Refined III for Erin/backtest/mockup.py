"""Render a mockup grid: real photos × Refined III presets.

Reuses the simulator from backtest.py. Output is a single PNG with rows of
images and columns showing Original / III.1 / III.2 / III.3.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from backtest import parse_xmp, render  # noqa: E402

REPO = HERE.parent.parent.parent
PRESET_DIR = HERE.parent
OUT = HERE / "output"
OUT.mkdir(exist_ok=True)

# Hand-picked photos that exercise the parts of the pack Erin will care about:
#   sunset+person, lush foliage, warm tones, mixed greens.
PHOTOS = [
    ("Sunset portrait",  REPO / "_input" / "11.jpg"),
    ("Foliage path",     REPO / "_input" / "10.jpg"),
    ("Warm tones",       REPO / "_input" / "4.jpg"),
    ("Cabin in pines",   REPO / "_input" / "3.jpg"),
    ("River + town",     REPO / "_input" / "9.jpg"),
]
PRESETS = ["Refined III.1", "Refined III.2", "Refined III.3"]
TILE = 360       # square tile size
GAP = 10
LABEL_H = 30
HEADER_H = 36


def load(path: Path, size: int) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    img.thumbnail((size, size))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    # Pad to square so the grid lines up cleanly
    h, w = arr.shape[:2]
    if (h, w) != (size, size):
        canvas = np.zeros((size, size, 3), dtype=np.float32)
        y = (size - h) // 2
        x = (size - w) // 2
        canvas[y:y + h, x:x + w] = arr
        arr = canvas
    return arr


def to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))


def main() -> int:
    settings = {p: parse_xmp(PRESET_DIR / f"{p}.xmp") for p in PRESETS}
    cols = 1 + len(PRESETS)              # original + presets
    rows = len(PHOTOS)
    grid_w = cols * TILE + (cols - 1) * GAP
    grid_h = HEADER_H + rows * (TILE + LABEL_H) + (rows - 1) * GAP

    canvas = Image.new("RGB", (grid_w, grid_h), (18, 18, 20))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except OSError:
        font = label_font = ImageFont.load_default()

    # Column headers
    for c, header in enumerate(["Original"] + PRESETS):
        x = c * (TILE + GAP)
        draw.text((x + 8, 8), header, fill=(235, 235, 235), font=font)

    for r, (label, path) in enumerate(PHOTOS):
        if not path.exists():
            print(f"  skip {path} (missing)")
            continue
        original = load(path, TILE)
        y = HEADER_H + r * (TILE + LABEL_H + GAP)

        # Original
        canvas.paste(to_pil(original), (0, y))
        draw.text((4, y + TILE + 6), label, fill=(220, 220, 220), font=label_font)

        for c, preset_name in enumerate(PRESETS, start=1):
            rendered = render(original, settings[preset_name], seed=r * 10 + c)
            x = c * (TILE + GAP)
            canvas.paste(to_pil(rendered), (x, y))
            draw.text((x + 4, y + TILE + 6), preset_name, fill=(180, 180, 180), font=label_font)

        print(f"  rendered row {r + 1}/{len(PHOTOS)}: {label}")

    out_path = OUT / "_mockup.png"
    canvas.save(out_path, optimize=True)
    print(f"\nWrote {out_path.relative_to(REPO)}  ({canvas.size[0]}x{canvas.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
