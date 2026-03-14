"""Near-duplicate and similarity detection module.

Uses perceptual hashing (average hash + difference hash) and optional
CLIP embeddings to group similar photos so the photographer can pick
the best from each burst/series.
"""

from __future__ import annotations

import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Perceptual hashing
# ---------------------------------------------------------------------------

def average_hash(image: Image.Image, hash_size: int = 16) -> np.ndarray:
    """Compute an average perceptual hash (boolean array)."""
    img = image.convert("L").resize((hash_size, hash_size), Image.LANCZOS)
    pixels = np.array(img, dtype=np.float64)
    return pixels >= np.mean(pixels)


def difference_hash(image: Image.Image, hash_size: int = 16) -> np.ndarray:
    """Compute a difference hash (gradient-based, more robust to gamma)."""
    img = image.convert("L").resize((hash_size + 1, hash_size), Image.LANCZOS)
    pixels = np.array(img, dtype=np.float64)
    return pixels[:, 1:] > pixels[:, :-1]


def hamming_distance(h1: np.ndarray, h2: np.ndarray) -> int:
    """Bit-level Hamming distance between two boolean hash arrays."""
    return int(np.count_nonzero(h1 != h2))


def hash_similarity(h1: np.ndarray, h2: np.ndarray) -> float:
    """Similarity in [0, 1] derived from Hamming distance."""
    total_bits = h1.size
    return 1.0 - hamming_distance(h1, h2) / total_bits


# ---------------------------------------------------------------------------
# Histogram similarity (fast, no ML dependencies)
# ---------------------------------------------------------------------------

def color_histogram(image: Image.Image, bins: int = 64) -> np.ndarray:
    """Compute a normalized RGB color histogram."""
    arr = np.array(image.convert("RGB"))
    hist = np.zeros(bins * 3, dtype=np.float64)
    for ch in range(3):
        h, _ = np.histogram(arr[:, :, ch], bins=bins, range=(0, 256))
        hist[ch * bins:(ch + 1) * bins] = h
    total = hist.sum()
    if total > 0:
        hist /= total
    return hist


def histogram_similarity(h1: np.ndarray, h2: np.ndarray) -> float:
    """Bhattacharyya coefficient between two normalized histograms."""
    return float(np.sum(np.sqrt(h1 * h2)))


# ---------------------------------------------------------------------------
# CLIP-based semantic similarity (optional — requires torch + transformers)
# ---------------------------------------------------------------------------

_clip_model = None
_clip_processor = None


def _load_clip():
    """Lazily load CLIP model (only when semantic similarity is requested)."""
    global _clip_model, _clip_processor
    if _clip_model is not None:
        return

    import torch
    from transformers import CLIPModel, CLIPProcessor

    model_name = "openai/clip-vit-base-patch32"
    _clip_processor = CLIPProcessor.from_pretrained(model_name)
    _clip_model = CLIPModel.from_pretrained(model_name)
    _clip_model.eval()
    if torch.cuda.is_available():
        _clip_model = _clip_model.cuda()


def clip_embedding(image: Image.Image) -> np.ndarray:
    """Return the L2-normalized CLIP image embedding for a single image."""
    _load_clip()
    import torch

    inputs = _clip_processor(images=image, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}

    with torch.no_grad():
        emb = _clip_model.get_image_features(**inputs)
    emb = emb.cpu().numpy().flatten().astype(np.float64)
    emb /= np.linalg.norm(emb) + 1e-9
    return emb


def clip_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Cosine similarity between two CLIP embeddings (already L2-normed)."""
    return float(np.dot(emb1, emb2))


# ---------------------------------------------------------------------------
# Combined similarity
# ---------------------------------------------------------------------------

def combined_similarity(
    image_a: Image.Image,
    image_b: Image.Image,
    use_clip: bool = False,
    ahash_a: np.ndarray | None = None,
    ahash_b: np.ndarray | None = None,
    dhash_a: np.ndarray | None = None,
    dhash_b: np.ndarray | None = None,
    hist_a: np.ndarray | None = None,
    hist_b: np.ndarray | None = None,
    clip_emb_a: np.ndarray | None = None,
    clip_emb_b: np.ndarray | None = None,
) -> float:
    """Compute a blended similarity score in [0, 1].

    Pre-computed features can be passed in to avoid redundant work.
    """
    ah_a = ahash_a if ahash_a is not None else average_hash(image_a)
    ah_b = ahash_b if ahash_b is not None else average_hash(image_b)
    dh_a = dhash_a if dhash_a is not None else difference_hash(image_a)
    dh_b = dhash_b if dhash_b is not None else difference_hash(image_b)
    hi_a = hist_a if hist_a is not None else color_histogram(image_a)
    hi_b = hist_b if hist_b is not None else color_histogram(image_b)

    s_ahash = hash_similarity(ah_a, ah_b)
    s_dhash = hash_similarity(dh_a, dh_b)
    s_hist = histogram_similarity(hi_a, hi_b)

    if use_clip:
        ce_a = clip_emb_a if clip_emb_a is not None else clip_embedding(image_a)
        ce_b = clip_emb_b if clip_emb_b is not None else clip_embedding(image_b)
        s_clip = clip_similarity(ce_a, ce_b)
        return 0.25 * s_ahash + 0.25 * s_dhash + 0.20 * s_hist + 0.30 * s_clip
    else:
        return 0.35 * s_ahash + 0.35 * s_dhash + 0.30 * s_hist


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

def group_similar(
    images: dict[str, Image.Image],
    threshold: float = 0.85,
    use_clip: bool = False,
) -> list[list[str]]:
    """Group images by similarity using union-find.

    Args:
        images: mapping of filename -> PIL Image.
        threshold: similarity above which two images are considered duplicates.
        use_clip: whether to include CLIP semantic similarity.

    Returns:
        List of groups (each group is a list of filenames).
    """
    names = list(images.keys())
    n = len(names)

    # Pre-compute features
    ahashes = {k: average_hash(v) for k, v in images.items()}
    dhashes = {k: difference_hash(v) for k, v in images.items()}
    hists = {k: color_histogram(v) for k, v in images.items()}
    clip_embs = {}
    if use_clip:
        clip_embs = {k: clip_embedding(v) for k, v in images.items()}

    # Union-find
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i + 1, n):
            na, nb = names[i], names[j]
            sim = combined_similarity(
                images[na], images[nb],
                use_clip=use_clip,
                ahash_a=ahashes[na], ahash_b=ahashes[nb],
                dhash_a=dhashes[na], dhash_b=dhashes[nb],
                hist_a=hists[na], hist_b=hists[nb],
                clip_emb_a=clip_embs.get(na), clip_emb_b=clip_embs.get(nb),
            )
            if sim >= threshold:
                union(i, j)

    groups: dict[int, list[str]] = {}
    for i, name in enumerate(names):
        root = find(i)
        groups.setdefault(root, []).append(name)

    return list(groups.values())
