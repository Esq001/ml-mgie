"""Image quality assessment module.

Scores photos on technical quality metrics: sharpness, exposure,
noise, contrast, saturation, and composition (rule-of-thirds).
Each metric is normalized to [0, 1] and combined into a weighted
overall quality score.
"""

import numpy as np
from PIL import Image


def sharpness_score(img_array: np.ndarray) -> float:
    """Estimate sharpness via Laplacian variance on the luminance channel."""
    if img_array.ndim == 3:
        gray = np.mean(img_array[:, :, :3], axis=2)
    else:
        gray = img_array.astype(np.float64)

    laplacian_kernel = np.array([[0, 1, 0],
                                  [1, -4, 1],
                                  [0, 1, 0]], dtype=np.float64)

    from scipy.signal import convolve2d
    lap = convolve2d(gray, laplacian_kernel, mode="valid")
    variance = np.var(lap)

    # Normalize: typical sharp images have variance > 500, blurry < 100
    score = min(variance / 800.0, 1.0)
    return float(score)


def exposure_score(img_array: np.ndarray) -> float:
    """Score exposure based on how close mean brightness is to the midpoint.

    Well-exposed images tend to have mean luminance near 128.
    Severely under/over-exposed images score lower.
    """
    if img_array.ndim == 3:
        # Rec. 709 luminance weights
        lum = (0.2126 * img_array[:, :, 0]
               + 0.7152 * img_array[:, :, 1]
               + 0.0722 * img_array[:, :, 2])
    else:
        lum = img_array.astype(np.float64)

    mean_lum = np.mean(lum)
    # Distance from ideal midpoint (128), normalized
    deviation = abs(mean_lum - 128.0) / 128.0
    return float(max(1.0 - deviation, 0.0))


def contrast_score(img_array: np.ndarray) -> float:
    """Score contrast using the standard deviation of luminance.

    Low-contrast images have tightly clustered pixel values.
    """
    if img_array.ndim == 3:
        lum = (0.2126 * img_array[:, :, 0]
               + 0.7152 * img_array[:, :, 1]
               + 0.0722 * img_array[:, :, 2])
    else:
        lum = img_array.astype(np.float64)

    std = np.std(lum)
    # Good contrast typically has std > 50
    return float(min(std / 64.0, 1.0))


def saturation_score(img_array: np.ndarray) -> float:
    """Score color saturation using the HSV saturation channel.

    Avoids penalizing intentionally desaturated (B&W) images too heavily
    by using a gentle curve.
    """
    if img_array.ndim != 3 or img_array.shape[2] < 3:
        return 0.5  # grayscale — neutral score

    r, g, b = (img_array[:, :, i].astype(np.float64) for i in range(3))
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    delta = max_c - min_c

    # Avoid division by zero
    safe_max = np.where(max_c > 0, max_c, 1.0)
    sat = np.where(max_c > 0, delta / safe_max, 0.0)
    mean_sat = np.mean(sat)

    # Mean saturation in [0,1]; moderate saturation (~0.4-0.6) is ideal
    # Penalize very low or very high
    return float(1.0 - abs(mean_sat - 0.45) / 0.55)


def noise_score(img_array: np.ndarray) -> float:
    """Estimate noise level using the median absolute deviation of high-freq.

    Lower noise yields a higher score.
    """
    if img_array.ndim == 3:
        gray = np.mean(img_array[:, :, :3], axis=2)
    else:
        gray = img_array.astype(np.float64)

    # Simple high-pass: difference from 3x3 mean
    from scipy.ndimage import uniform_filter
    smoothed = uniform_filter(gray, size=3)
    residual = gray - smoothed
    mad = np.median(np.abs(residual))

    # Lower MAD = less noise = higher score
    score = max(1.0 - (mad / 15.0), 0.0)
    return float(score)


def composition_score(img_array: np.ndarray) -> float:
    """Approximate rule-of-thirds composition scoring.

    Checks whether high-energy regions (edges) align with the
    rule-of-thirds grid intersections.
    """
    if img_array.ndim == 3:
        gray = np.mean(img_array[:, :, :3], axis=2)
    else:
        gray = img_array.astype(np.float64)

    from scipy.signal import convolve2d
    # Sobel magnitude as energy map
    sx = convolve2d(gray, np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
                                    dtype=np.float64), mode="same")
    sy = convolve2d(gray, np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
                                    dtype=np.float64), mode="same")
    energy = np.sqrt(sx ** 2 + sy ** 2)

    h, w = energy.shape
    total_energy = energy.sum()
    if total_energy == 0:
        return 0.5

    # Rule-of-thirds intersection points
    thirds_y = [h // 3, 2 * h // 3]
    thirds_x = [w // 3, 2 * w // 3]
    radius_y = max(h // 12, 1)
    radius_x = max(w // 12, 1)

    roi_energy = 0.0
    for ty in thirds_y:
        for tx in thirds_x:
            y0, y1 = max(ty - radius_y, 0), min(ty + radius_y, h)
            x0, x1 = max(tx - radius_x, 0), min(tx + radius_x, w)
            roi_energy += energy[y0:y1, x0:x1].sum()

    # Fraction of energy near rule-of-thirds points
    fraction = roi_energy / total_energy
    # Normalize — typical strong composition ~0.15-0.25
    return float(min(fraction / 0.20, 1.0))


# Default weights for combining sub-scores
DEFAULT_WEIGHTS = {
    "sharpness": 0.30,
    "exposure": 0.20,
    "contrast": 0.10,
    "saturation": 0.10,
    "noise": 0.15,
    "composition": 0.15,
}

METRIC_FUNCTIONS = {
    "sharpness": sharpness_score,
    "exposure": exposure_score,
    "contrast": contrast_score,
    "saturation": saturation_score,
    "noise": noise_score,
    "composition": composition_score,
}


def assess_quality(
    image: Image.Image,
    weights: dict[str, float] | None = None,
) -> dict:
    """Run all quality metrics on a PIL Image and return individual + overall scores.

    Returns a dict with keys for each metric, plus "overall".
    """
    weights = weights or DEFAULT_WEIGHTS
    arr = np.array(image, dtype=np.float64)

    scores = {}
    for name, func in METRIC_FUNCTIONS.items():
        scores[name] = round(func(arr), 4)

    overall = sum(scores[k] * weights.get(k, 0.0) for k in scores)
    scores["overall"] = round(overall, 4)
    return scores
