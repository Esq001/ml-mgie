"""Detect iCloud Photos sync folders on the local filesystem.

Supports:
- macOS Photos library originals
- iCloud Drive photos folder
- icloudpd (third-party iCloud downloader) default paths
- Custom paths via environment variable ICLOUD_PHOTOS_DIR
"""

from __future__ import annotations

import os
import platform
from pathlib import Path


# Well-known iCloud Photos locations, checked in priority order.
_CANDIDATE_PATHS: list[tuple[str, str]] = [
    # macOS Photos app originals (Catalina+)
    (
        "~/Pictures/Photos Library.photoslibrary/originals",
        "macOS Photos Library (originals)",
    ),
    # macOS iCloud Drive photos folder
    (
        "~/Library/Mobile Documents/com~apple~CloudDocs/Photos",
        "iCloud Drive Photos folder",
    ),
    # icloudpd default download directory
    (
        "~/icloud-photos",
        "icloudpd download folder",
    ),
    # Linux common convention
    (
        "~/iCloud Photos",
        "iCloud Photos sync folder",
    ),
]

ENV_VAR = "ICLOUD_PHOTOS_DIR"


def find_icloud_photos_dir() -> Path | None:
    """Return the first existing iCloud Photos directory, or None.

    Resolution order:
    1. ``ICLOUD_PHOTOS_DIR`` environment variable (if set and valid).
    2. Well-known candidate paths for the current platform.
    """
    # 1. Explicit env override
    env_path = os.environ.get(ENV_VAR)
    if env_path:
        p = Path(env_path).expanduser()
        if p.is_dir():
            return p

    # 2. Walk candidate paths
    for raw_path, _label in _CANDIDATE_PATHS:
        p = Path(raw_path).expanduser()
        if p.is_dir():
            return p

    return None


def list_icloud_sources() -> list[dict[str, str]]:
    """Return a list of detected iCloud photo sources with metadata.

    Each entry has keys ``path`` and ``label``.
    """
    sources: list[dict[str, str]] = []

    env_path = os.environ.get(ENV_VAR)
    if env_path:
        p = Path(env_path).expanduser()
        if p.is_dir():
            sources.append({"path": str(p), "label": f"{ENV_VAR} override"})

    for raw_path, label in _CANDIDATE_PATHS:
        p = Path(raw_path).expanduser()
        if p.is_dir():
            sources.append({"path": str(p), "label": label})

    return sources
