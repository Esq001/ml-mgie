"""
Backtest Refined III XMP presets.

What this does:
  1. Parses every .xmp in the parent folder, extracts all crs: settings.
  2. Validates that each setting falls inside Lightroom's documented range.
  3. Approximates the Camera Raw pipeline in numpy and renders before/after
     previews on (a) a synthetic color chart with skin / foliage / sky / gray
     swatches, and (b) a real photo from the repo.
  4. Measures the mean color shift per swatch region and writes a markdown
     report.

The render is a *simulation*, not a pixel-exact recreation of Adobe Camera
Raw. Adobe's processing pipeline (ProPhoto linear, proprietary HSL falloff,
proprietary color grading blend) is closed-source. The point here is to
verify the math heads in the right direction (greens → cyan, skin → peach,
shadows → cyan, etc.), not to substitute for opening Lightroom.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PRESET_DIR = HERE.parent
OUT_DIR = HERE / "output"
OUT_DIR.mkdir(exist_ok=True)


# --- Lightroom Camera Raw value ranges (the ones we touch) -------------------
RANGES = {
    "Exposure2012": (-5.0, 5.0),
    "Contrast2012": (-100, 100),
    "Highlights2012": (-100, 100),
    "Shadows2012": (-100, 100),
    "Whites2012": (-100, 100),
    "Blacks2012": (-100, 100),
    "Texture": (-100, 100),
    "Clarity2012": (-100, 100),
    "Dehaze": (-100, 100),
    "Vibrance": (-100, 100),
    "Saturation": (-100, 100),
    "ParametricShadows": (-100, 100),
    "ParametricDarks": (-100, 100),
    "ParametricLights": (-100, 100),
    "ParametricHighlights": (-100, 100),
    "Sharpness": (0, 150),
    "LuminanceSmoothing": (0, 100),
    "ColorNoiseReduction": (0, 100),
    "GrainAmount": (0, 100),
    "GrainSize": (0, 100),
    "GrainFrequency": (0, 100),
    "PostCropVignetteAmount": (-100, 100),
    "ShadowTint": (-100, 100),
    "ColorGradeShadowHue": (0, 360),
    "ColorGradeMidtoneHue": (0, 360),
    "ColorGradeHighlightHue": (0, 360),
    "ColorGradeGlobalHue": (0, 360),
    "ColorGradeShadowSat": (0, 100),
    "ColorGradeMidtoneSat": (0, 100),
    "ColorGradeHighlightSat": (0, 100),
    "ColorGradeGlobalSat": (0, 100),
    "ColorGradeBlending": (0, 100),
}
# HSL adjustments share a range
for color in ("Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta"):
    for kind in ("HueAdjustment", "SaturationAdjustment", "LuminanceAdjustment"):
        RANGES[f"{kind}{color}"] = (-100, 100)
# Calibration primaries
for prim in ("Red", "Green", "Blue"):
    RANGES[f"{prim}Hue"] = (-100, 100)
    RANGES[f"{prim}Saturation"] = (-100, 100)


# --- XMP parsing -------------------------------------------------------------
ATTR_RE = re.compile(r'crs:([A-Za-z0-9_]+)\s*=\s*"([^"]*)"')


def parse_xmp(path: Path) -> dict:
    """Pull every crs:* attribute out of the XMP. Numeric where possible."""
    text = path.read_text()
    settings: dict[str, object] = {}
    for key, raw in ATTR_RE.findall(text):
        if key in settings:
            continue
        if raw in ("true", "True"):
            settings[key] = True
        elif raw in ("false", "False"):
            settings[key] = False
        else:
            try:
                settings[key] = float(raw) if "." in raw or raw.startswith(("+", "-")) else int(raw)
            except ValueError:
                settings[key] = raw
    return settings


# --- Validation --------------------------------------------------------------
@dataclass
class ValidationResult:
    name: str
    ok: bool
    issues: list[str] = field(default_factory=list)
    settings: dict = field(default_factory=dict)


def validate(name: str, settings: dict) -> ValidationResult:
    issues: list[str] = []
    for key, (lo, hi) in RANGES.items():
        if key not in settings:
            continue
        v = settings[key]
        if not isinstance(v, (int, float)):
            issues.append(f"{key}: non-numeric value {v!r}")
            continue
        if v < lo or v > hi:
            issues.append(f"{key}={v} out of range [{lo}, {hi}]")
    # Required identity
    for required in ("ProcessVersion", "Version"):
        if required not in settings:
            issues.append(f"missing required field {required}")
    return ValidationResult(name=name, ok=not issues, issues=issues, settings=settings)


# --- Approximated Camera Raw pipeline ----------------------------------------
def srgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1)
    mn = rgb.min(-1)
    diff = mx - mn
    h = np.zeros_like(mx)
    mask = diff > 1e-8
    rmax = (mx == r) & mask
    gmax = (mx == g) & mask
    bmax = (mx == b) & mask
    h[rmax] = ((g[rmax] - b[rmax]) / diff[rmax]) % 6
    h[gmax] = ((b[gmax] - r[gmax]) / diff[gmax]) + 2
    h[bmax] = ((r[bmax] - g[bmax]) / diff[bmax]) + 4
    h = h / 6.0
    s = np.where(mx > 1e-8, diff / np.maximum(mx, 1e-8), 0)
    v = mx
    return np.stack([h, s, v], -1)


def hsv_to_srgb(hsv: np.ndarray) -> np.ndarray:
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1)


# Center hue (in [0,1]) for each LR HSL color band.
HSL_BANDS = {
    "Red": 0.00, "Orange": 0.083, "Yellow": 0.167, "Green": 0.333,
    "Aqua": 0.5, "Blue": 0.667, "Purple": 0.778, "Magenta": 0.889,
}
HSL_BAND_WIDTH = 1.0 / 8.0  # cosine falloff width


def _band_weights(h: np.ndarray, band_hue: float) -> np.ndarray:
    """Cosine-falloff weight, peaks at band_hue, zero outside ±band_width."""
    d = np.minimum(np.abs(h - band_hue), 1 - np.abs(h - band_hue))
    w = np.cos(np.clip(d / HSL_BAND_WIDTH, 0, 1) * np.pi / 2)
    return np.maximum(w, 0)


def apply_hsl(rgb: np.ndarray, settings: dict) -> np.ndarray:
    hsv = srgb_to_hsv(rgb)
    h, s, v = hsv[..., 0].copy(), hsv[..., 1].copy(), hsv[..., 2].copy()
    for color, base in HSL_BANDS.items():
        w = _band_weights(hsv[..., 0], base)
        hue_adj = settings.get(f"HueAdjustment{color}", 0) / 100.0  # ±1 hue band
        sat_adj = settings.get(f"SaturationAdjustment{color}", 0) / 100.0
        lum_adj = settings.get(f"LuminanceAdjustment{color}", 0) / 100.0
        h += w * hue_adj * (HSL_BAND_WIDTH * 0.5)
        s = np.clip(s + w * sat_adj * 0.5, 0, 1)
        v = np.clip(v + w * lum_adj * 0.25, 0, 1)
    h = h % 1.0
    return np.clip(hsv_to_srgb(np.stack([h, s, v], -1)), 0, 1)


def apply_tone_basics(rgb: np.ndarray, settings: dict) -> np.ndarray:
    img = rgb.copy()
    img *= 2 ** float(settings.get("Exposure2012", 0))
    # Contrast: pivot around 0.5 with strength scaled by slider/100
    contrast = float(settings.get("Contrast2012", 0)) / 100.0
    img = (img - 0.5) * (1 + contrast * 0.5) + 0.5
    # Highlights / shadows / whites / blacks (gentle approximations)
    lum = img.mean(-1, keepdims=True)
    hi = np.clip((lum - 0.6) / 0.4, 0, 1)
    sh = np.clip((0.4 - lum) / 0.4, 0, 1)
    img += hi * float(settings.get("Highlights2012", 0)) / 100.0 * 0.25
    img += sh * float(settings.get("Shadows2012", 0)) / 100.0 * 0.25
    wh = np.clip((lum - 0.75) / 0.25, 0, 1)
    bl = np.clip((0.25 - lum) / 0.25, 0, 1)
    img += wh * float(settings.get("Whites2012", 0)) / 100.0 * 0.2
    img += bl * float(settings.get("Blacks2012", 0)) / 100.0 * 0.2
    return np.clip(img, 0, 1)


def apply_vibrance_saturation(rgb: np.ndarray, settings: dict) -> np.ndarray:
    hsv = srgb_to_hsv(rgb)
    sat = hsv[..., 1]
    vib = float(settings.get("Vibrance", 0)) / 100.0
    # Vibrance boosts low-sat pixels more, scaled gently
    sat = sat + vib * (1 - sat) * 0.5
    sat = sat * (1 + float(settings.get("Saturation", 0)) / 100.0 * 0.5)
    hsv[..., 1] = np.clip(sat, 0, 1)
    return np.clip(hsv_to_srgb(hsv), 0, 1)


def _hue_to_rgb_tint(hue_deg: float, sat_pct: float) -> np.ndarray:
    """Convert a color-grading wheel position to an additive RGB tint."""
    h = (hue_deg % 360) / 360.0
    rgb = hsv_to_srgb(np.array([[[h, 1.0, 1.0]]]))[0, 0]
    return (rgb - 0.5) * (sat_pct / 100.0) * 0.3


def apply_color_grading(rgb: np.ndarray, settings: dict) -> np.ndarray:
    img = rgb.copy()
    lum = img.mean(-1, keepdims=True)
    sh_w = np.clip((0.4 - lum) / 0.4, 0, 1)
    mid_w = np.clip(1 - np.abs(lum - 0.5) / 0.3, 0, 1)
    hi_w = np.clip((lum - 0.6) / 0.4, 0, 1)
    img += sh_w * _hue_to_rgb_tint(
        settings.get("ColorGradeShadowHue", 0), settings.get("ColorGradeShadowSat", 0)
    )
    img += mid_w * _hue_to_rgb_tint(
        settings.get("ColorGradeMidtoneHue", 0), settings.get("ColorGradeMidtoneSat", 0)
    )
    img += hi_w * _hue_to_rgb_tint(
        settings.get("ColorGradeHighlightHue", 0), settings.get("ColorGradeHighlightSat", 0)
    )
    img += _hue_to_rgb_tint(
        settings.get("ColorGradeGlobalHue", 0), settings.get("ColorGradeGlobalSat", 0)
    )
    return np.clip(img, 0, 1)


def apply_vignette_grain(rgb: np.ndarray, settings: dict, rng: np.random.Generator) -> np.ndarray:
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx = h / 2, w / 2
    r = np.sqrt(((yy - cy) / cy) ** 2 + ((xx - cx) / cx) ** 2) / np.sqrt(2)
    vig = float(settings.get("PostCropVignetteAmount", 0)) / 100.0
    falloff = np.clip(r, 0, 1) ** 2
    img = rgb * (1 + vig * falloff[..., None] * 0.5)
    grain = float(settings.get("GrainAmount", 0)) / 100.0
    if grain > 0:
        noise = rng.normal(0, grain * 0.05, rgb.shape[:2])
        img += noise[..., None]
    return np.clip(img, 0, 1)


def render(rgb: np.ndarray, settings: dict, seed: int = 0) -> np.ndarray:
    img = apply_tone_basics(rgb, settings)
    img = apply_vibrance_saturation(img, settings)
    img = apply_hsl(img, settings)
    img = apply_color_grading(img, settings)
    img = apply_vignette_grain(img, settings, np.random.default_rng(seed))
    return img


# --- Synthetic test chart ----------------------------------------------------
SWATCHES = [
    # (label, sRGB color in [0,1], region row, region col)
    ("skin_pale",   (0.95, 0.82, 0.72)),
    ("skin_med",   (0.86, 0.66, 0.54)),
    ("skin_tan",    (0.66, 0.45, 0.34)),
    ("foliage",     (0.34, 0.50, 0.22)),
    ("sky",         (0.45, 0.60, 0.80)),
    ("sunset",      (0.95, 0.70, 0.45)),
    ("magenta",     (0.75, 0.40, 0.55)),
    ("gray_25",     (0.25, 0.25, 0.25)),
    ("gray_50",     (0.50, 0.50, 0.50)),
    ("gray_75",     (0.75, 0.75, 0.75)),
    ("white_95",    (0.95, 0.95, 0.95)),
    ("black_05",    (0.05, 0.05, 0.05)),
]


def make_chart(swatch_size=80, cols=6) -> tuple[np.ndarray, dict]:
    rows = (len(SWATCHES) + cols - 1) // cols
    h = rows * swatch_size
    w = cols * swatch_size
    img = np.zeros((h, w, 3))
    regions = {}
    for i, (label, color) in enumerate(SWATCHES):
        r, c = divmod(i, cols)
        y0, x0 = r * swatch_size, c * swatch_size
        img[y0:y0 + swatch_size, x0:x0 + swatch_size] = color
        regions[label] = (y0, x0, swatch_size)
    return img, regions


def measure(img: np.ndarray, regions: dict, pad: int = 8) -> dict:
    out = {}
    for label, (y, x, size) in regions.items():
        patch = img[y + pad:y + size - pad, x + pad:x + size - pad]
        out[label] = patch.mean((0, 1)).tolist()
    return out


# --- Real photo --------------------------------------------------------------
def load_real_photo() -> np.ndarray | None:
    candidate = PRESET_DIR.parent.parent / "demo.png"
    if not candidate.exists():
        return None
    img = Image.open(candidate).convert("RGB")
    img.thumbnail((900, 900))
    return np.asarray(img, dtype=np.float32) / 255.0


# --- Driver ------------------------------------------------------------------
def save(arr: np.ndarray, path: Path) -> None:
    Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)).save(path)


def stack(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    gap = np.ones((before.shape[0], 12, 3))
    return np.concatenate([before, gap, after], 1)


def main() -> int:
    xmps = sorted(PRESET_DIR.glob("*.xmp"))
    if not xmps:
        print(f"No XMP files in {PRESET_DIR}", file=sys.stderr)
        return 2

    chart, regions = make_chart()
    photo = load_real_photo()
    save(chart, OUT_DIR / "_chart_before.png")
    if photo is not None:
        save(photo, OUT_DIR / "_photo_before.png")

    report = {"presets": []}
    print(f"Backtesting {len(xmps)} preset(s) in {PRESET_DIR.name}\n")

    for path in xmps:
        name = path.stem
        settings = parse_xmp(path)
        result = validate(name, settings)
        print(f"== {name} ==")
        if result.ok:
            print("  validation: OK")
        else:
            print("  validation: ISSUES")
            for issue in result.issues:
                print(f"    - {issue}")

        chart_after = render(chart, settings, seed=1)
        save(stack(chart, chart_after), OUT_DIR / f"{name} - chart.png")

        before_means = measure(chart, regions)
        after_means = measure(chart_after, regions)
        deltas = {
            label: [round(a - b, 4) for a, b in zip(after_means[label], before_means[label])]
            for label in before_means
        }

        if photo is not None:
            photo_after = render(photo, settings, seed=2)
            save(stack(photo, photo_after), OUT_DIR / f"{name} - photo.png")

        report["presets"].append(
            {
                "name": name,
                "validation_ok": result.ok,
                "issues": result.issues,
                "swatch_rgb_after": {k: [round(v, 4) for v in vs] for k, vs in after_means.items()},
                "swatch_rgb_delta": deltas,
            }
        )
        print(f"  saved chart preview: {OUT_DIR.name}/{name} - chart.png")
        if photo is not None:
            print(f"  saved photo preview: {OUT_DIR.name}/{name} - photo.png")
        print()

    (OUT_DIR / "backtest.json").write_text(json.dumps(report, indent=2))
    print(f"Wrote {OUT_DIR.name}/backtest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
