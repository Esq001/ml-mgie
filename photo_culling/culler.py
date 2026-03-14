"""Main photo culling orchestrator.

Scans a directory of images, scores each for technical quality,
groups near-duplicates, and produces a culling report that
recommends which photos to keep, review, or reject.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal

from PIL import Image

from .quality import assess_quality
from .similarity import group_similar

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp",
}

# Thresholds for keep / review / reject buckets
KEEP_THRESHOLD = 0.60
REJECT_THRESHOLD = 0.35


@dataclass
class PhotoResult:
    """Quality assessment result for a single photo."""
    filename: str
    path: str
    scores: dict[str, float] = field(default_factory=dict)
    verdict: Literal["keep", "review", "reject"] = "review"
    group_id: int | None = None
    is_best_in_group: bool = False


@dataclass
class CullReport:
    """Full culling report for a directory of photos."""
    source_dir: str
    total_photos: int = 0
    keep: list[PhotoResult] = field(default_factory=list)
    review: list[PhotoResult] = field(default_factory=list)
    reject: list[PhotoResult] = field(default_factory=list)
    groups: list[list[str]] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Photo Culling Report for: {self.source_dir}",
            f"{'=' * 50}",
            f"Total photos scanned : {self.total_photos}",
            f"  Keep               : {len(self.keep)}",
            f"  Review             : {len(self.review)}",
            f"  Reject             : {len(self.reject)}",
            f"  Duplicate groups   : {len([g for g in self.groups if len(g) > 1])}",
            "",
        ]

        if self.keep:
            lines.append("--- KEEP (best shots) ---")
            for p in sorted(self.keep, key=lambda x: -x.scores.get("overall", 0)):
                lines.append(f"  {p.filename:40s}  overall={p.scores['overall']:.3f}")
            lines.append("")

        if self.review:
            lines.append("--- REVIEW (borderline) ---")
            for p in sorted(self.review, key=lambda x: -x.scores.get("overall", 0)):
                lines.append(f"  {p.filename:40s}  overall={p.scores['overall']:.3f}")
            lines.append("")

        if self.reject:
            lines.append("--- REJECT (low quality / duplicates) ---")
            for p in sorted(self.reject, key=lambda x: x.scores.get("overall", 0)):
                lines.append(f"  {p.filename:40s}  overall={p.scores['overall']:.3f}")
            lines.append("")

        dup_groups = [g for g in self.groups if len(g) > 1]
        if dup_groups:
            lines.append("--- DUPLICATE / SIMILAR GROUPS ---")
            for i, grp in enumerate(dup_groups, 1):
                lines.append(f"  Group {i}: {', '.join(grp)}")
            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def _load_image(path: str, max_dim: int = 1024) -> Image.Image:
    """Load an image and downscale for faster processing."""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img


def cull_photos(
    source_dir: str,
    *,
    keep_threshold: float = KEEP_THRESHOLD,
    reject_threshold: float = REJECT_THRESHOLD,
    similarity_threshold: float = 0.85,
    use_clip: bool = False,
    quality_weights: dict[str, float] | None = None,
    organize: bool = False,
    output_dir: str | None = None,
) -> CullReport:
    """Scan a directory, assess quality, detect duplicates, and build a report.

    Args:
        source_dir: Path to the folder containing photos.
        keep_threshold: Minimum overall score to auto-keep.
        reject_threshold: Below this score, auto-reject.
        similarity_threshold: Similarity above which images are grouped.
        use_clip: Use CLIP embeddings for semantic similarity (slower).
        quality_weights: Custom weights for quality sub-scores.
        organize: If True, copy files into keep/review/reject sub-folders.
        output_dir: Where to write organized folders (defaults to source_dir).

    Returns:
        A CullReport with per-photo scores and recommendations.
    """
    src = Path(source_dir)
    if not src.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    # Discover images
    image_paths: dict[str, str] = {}
    for entry in sorted(src.iterdir()):
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_EXTENSIONS:
            image_paths[entry.name] = str(entry)

    if not image_paths:
        raise ValueError(f"No supported images found in {source_dir}")

    # Load images (downscaled for speed)
    images: dict[str, Image.Image] = {}
    for name, path in image_paths.items():
        try:
            images[name] = _load_image(path)
        except Exception as exc:
            print(f"Warning: skipping {name} ({exc})")

    # 1. Quality assessment
    results: dict[str, PhotoResult] = {}
    for name, img in images.items():
        scores = assess_quality(img, weights=quality_weights)
        overall = scores["overall"]

        if overall >= keep_threshold:
            verdict = "keep"
        elif overall < reject_threshold:
            verdict = "reject"
        else:
            verdict = "review"

        results[name] = PhotoResult(
            filename=name,
            path=image_paths[name],
            scores=scores,
            verdict=verdict,
        )

    # 2. Similarity grouping
    groups = group_similar(
        images, threshold=similarity_threshold, use_clip=use_clip,
    )

    # Within each duplicate group, mark the best and demote the rest
    for gid, group in enumerate(groups):
        for name in group:
            results[name].group_id = gid

        if len(group) > 1:
            best_name = max(group, key=lambda n: results[n].scores.get("overall", 0))
            results[best_name].is_best_in_group = True

            for name in group:
                if name != best_name and results[name].verdict != "reject":
                    # Demote non-best duplicates to reject
                    results[name].verdict = "reject"

    # 3. Build report
    report = CullReport(
        source_dir=source_dir,
        total_photos=len(results),
        groups=[g for g in groups],
    )
    for r in results.values():
        if r.verdict == "keep":
            report.keep.append(r)
        elif r.verdict == "reject":
            report.reject.append(r)
        else:
            report.review.append(r)

    # 4. Optionally organize files into sub-folders
    if organize:
        out = Path(output_dir) if output_dir else src
        for bucket in ("keep", "review", "reject"):
            (out / bucket).mkdir(parents=True, exist_ok=True)

        for r in results.values():
            dest = out / r.verdict / r.filename
            shutil.copy2(r.path, dest)

    return report
