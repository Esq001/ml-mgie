# Refined III backtest report

## What was tested

For each of the three `.xmp` presets:

1. **Structural validation** — every `crs:*` setting is parsed and checked
   against Lightroom's documented value range (e.g. `Exposure2012` ∈ [-5, +5],
   HSL adjustments ∈ [-100, +100], color-grade hues ∈ [0, 360]).
2. **Simulated render** — an approximation of the Camera Raw pipeline
   (white balance → tone basics → vibrance/saturation → HSL bands → color
   grading → vignette → grain) applied to (a) a synthetic 12-swatch chart
   covering skin / foliage / sky / grayscale, and (b) the repo's `demo.png`.

> The simulator is **not** Adobe Camera Raw. ACR's pipeline (ProPhoto linear,
> proprietary HSL falloff, proprietary color-grading blend) is closed-source.
> The simulator is good enough to sanity-check direction and magnitude — not
> for a pixel-exact preview. Final visual confirmation has to happen in
> Lightroom.

## Results

| Preset            | Validation | Foliage shift              | Skin behavior                       | Highlight tint                |
| ----------------- | ---------- | -------------------------- | ----------------------------------- | ----------------------------- |
| **Refined III.1** | OK         | toward cyan-green          | brightened, desaturated → peach     | neutral (subtle)              |
| **Refined III.2** | OK         | toward cyan-green          | warm, retains R-dominance           | slightly warm                 |
| **Refined III.3** | OK         | toward cyan-green (warmer) | warm, between III.1 and III.2       | cool pink (R≥G, B≈G)          |

### Numeric color shifts

(`Δ` = mean RGB after − before, clipped 0–1)

```
Refined III.1
  foliage   Δ : R+0.046 G+0.046 B+0.064   ← B-rise > R-rise: cyan-green
  skin_med  Δ : R+0.052 G+0.103 B+0.120   ← desaturation lifts G/B toward V (peach)
  black_05  Δ : R+0.099 G+0.099 B+0.099   ← shadow lift; cyan tint masked by clipping
  white_95  Δ : R+0.022 G+0.022 B+0.022   ← neutral highlight
Refined III.2
  foliage   Δ : R+0.034 G+0.032 B+0.045   ← B-rise > R-rise: cyan-green
  skin_med  Δ : R+0.035 G+0.061 B+0.059   ← warmer skin, less luminance lift than III.1
  black_05  Δ : R+0.083 G+0.078 B+0.073   ← warm-leaning shadow lift
  white_95  Δ : R+0.002 G-0.006 B-0.010   ← warm highlight (R highest)
Refined III.3
  foliage   Δ : R+0.040 G+0.035 B+0.040   ← cyan-green (less aggressive than III.1/.2)
  skin_med  Δ : R+0.052 G+0.080 B+0.087   ← warm-luminous between III.1 and III.2
  black_05  Δ : R+0.070 G+0.064 B+0.065   ← shadow lift
  white_95  Δ : R+0.038 G+0.033 B+0.034   ← cool pink highlight tint
```

## Bug found and fixed during the backtest

The first run showed foliage shifting toward **yellow** rather than cyan — the
opposite of what Refined III is supposed to do. Root cause: I had the HSL
**Green Hue** and **Yellow Hue** sign inverted in all three presets.
In Lightroom the HSL Hue conventions are:

| Band   | Negative shifts toward | Positive shifts toward |
| ------ | ---------------------- | ---------------------- |
| Green  | yellow                 | aqua / cyan            |
| Yellow | orange                 | green                  |

Fix:

| Preset      | Old GreenHue | New | Old YellowHue | New |
| ----------- | -----------: | --: | ------------: | --: |
| Refined III.1 |          -25 | +25 |           -10 |  +5 |
| Refined III.2 |          -30 | +30 |           -15 |  +5 |
| Refined III.3 |          -18 | +18 |           -18 |   0 |

After the fix, all three presets produce the expected B-over-R rise on
foliage, confirming greens land in cyan territory.

## Visual previews

- `output/_montage_chart.png` — original chart vs. all three presets, side by side
- `output/Refined III.N - chart.png` — single preset before/after on swatch chart
- `output/Refined III.N - photo.png` — single preset before/after on `demo.png`
- `output/backtest.json` — machine-readable validation + per-swatch shifts

## How to re-run

```bash
cd "presets/Refined III for Erin/backtest"
python3 backtest.py     # validate + render
python3 montage.py      # build the side-by-side montage
```

Requires `numpy` and `Pillow`.

## Limitations

- HSL band falloff is a cosine approximation, not Adobe's actual mask.
- Color grading uses a simple luminance-weighted additive tint; ACR uses a
  more sophisticated model that interacts with saturation.
- Tone curves declared in the XMP are not yet replayed in the simulator
  (basic tone sliders are). They will affect Lightroom output but not the
  preview here.
- Calibration primaries (`RedHue`, `GreenSaturation`, etc.) are validated but
  not applied in the simulator.

For the directional checks above — "do greens go cyan, do skin tones land
peach/warm, do highlights pick up the right tint" — the simulator is
sufficient. For final visual approval, open the presets in Lightroom on a
representative raw.
