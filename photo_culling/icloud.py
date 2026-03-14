"""iCloud Photos integration: local folder detection and remote download.

Supports:
- Local sync folder detection (macOS Photos Library, iCloud Drive, icloudpd)
- Custom paths via environment variable ICLOUD_PHOTOS_DIR
- Direct iCloud API download via pyicloud (requires ``pip install pyicloud``)
"""

from __future__ import annotations

import getpass
import os
import sys
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Local sync-folder detection
# ---------------------------------------------------------------------------

_CANDIDATE_PATHS: list[tuple[str, str]] = [
    (
        "~/Pictures/Photos Library.photoslibrary/originals",
        "macOS Photos Library (originals)",
    ),
    (
        "~/Library/Mobile Documents/com~apple~CloudDocs/Photos",
        "iCloud Drive Photos folder",
    ),
    (
        "~/icloud-photos",
        "icloudpd download folder",
    ),
    (
        "~/iCloud Photos",
        "iCloud Photos sync folder",
    ),
]

ENV_VAR = "ICLOUD_PHOTOS_DIR"

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".tiff", ".tif", ".bmp", ".webp"}


def find_icloud_photos_dir() -> Path | None:
    """Return the first existing iCloud Photos directory, or None."""
    env_path = os.environ.get(ENV_VAR)
    if env_path:
        p = Path(env_path).expanduser()
        if p.is_dir():
            return p

    for raw_path, _label in _CANDIDATE_PATHS:
        p = Path(raw_path).expanduser()
        if p.is_dir():
            return p

    return None


def list_icloud_sources() -> list[dict[str, str]]:
    """Return a list of detected iCloud photo sources with metadata."""
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


# ---------------------------------------------------------------------------
# Direct iCloud API download
# ---------------------------------------------------------------------------

def _require_pyicloud():
    """Import and return the pyicloud module, with a helpful error on failure."""
    try:
        from pyicloud import PyiCloudService
        return PyiCloudService
    except ImportError:
        print(
            "Error: pyicloud is required for --icloud-download.\n"
            "Install it with:  pip install pyicloud keyring",
            file=sys.stderr,
        )
        sys.exit(1)


def icloud_login(apple_id: str | None = None) -> object:
    """Authenticate with iCloud and return a PyiCloudService instance.

    Handles two-factor authentication interactively.
    """
    PyiCloudService = _require_pyicloud()

    if apple_id is None:
        apple_id = os.environ.get("ICLOUD_APPLE_ID")
    if apple_id is None:
        apple_id = input("Apple ID: ").strip()

    password = os.environ.get("ICLOUD_PASSWORD")
    if password is None:
        password = getpass.getpass("iCloud password: ")

    api = PyiCloudService(apple_id, password)

    # Handle two-factor / two-step auth
    if api.requires_2fa:
        code = input("Enter the 2FA code sent to your devices: ").strip()
        if not api.validate_2fa_code(code):
            print("Error: invalid 2FA code.", file=sys.stderr)
            sys.exit(1)
    elif api.requires_2sa:
        devices = api.trusted_devices
        for i, d in enumerate(devices):
            name = d.get("deviceName", d.get("phoneNumber", f"Device {i}"))
            print(f"  [{i}] {name}")
        idx = int(input("Choose a trusted device: ").strip())
        device = devices[idx]
        if not api.send_verification_code(device):
            print("Error: failed to send verification code.", file=sys.stderr)
            sys.exit(1)
        code = input("Enter the verification code: ").strip()
        if not api.validate_verification_code(device, code):
            print("Error: invalid verification code.", file=sys.stderr)
            sys.exit(1)

    return api


def download_icloud_photos(
    api: object,
    dest_dir: str | None = None,
    album: str | None = None,
    limit: int | None = None,
    recent_days: int | None = None,
) -> Path:
    """Download photos from iCloud to a local directory.

    Args:
        api: Authenticated PyiCloudService instance.
        dest_dir: Destination directory. Created if needed; uses a temp dir if None.
        album: Album name to download from (default: "All Photos").
        limit: Maximum number of photos to download.
        recent_days: Only download photos from the last N days.

    Returns:
        Path to the directory containing downloaded photos.
    """
    from datetime import datetime, timedelta, timezone

    if dest_dir:
        out = Path(dest_dir)
    else:
        out = Path(tempfile.mkdtemp(prefix="icloud_photos_"))
    out.mkdir(parents=True, exist_ok=True)

    # Select album
    if album:
        if album not in api.photos.albums:
            available = ", ".join(api.photos.albums.keys())
            print(f"Error: album '{album}' not found. Available: {available}", file=sys.stderr)
            sys.exit(1)
        photos = api.photos.albums[album]
    else:
        photos = api.photos.all

    # Apply date filter
    cutoff = None
    if recent_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=recent_days)

    downloaded = 0
    skipped = 0

    print(f"Downloading iCloud photos to: {out}")

    for photo in photos:
        # Date filter
        if cutoff and hasattr(photo, "added_date") and photo.added_date:
            if photo.added_date < cutoff:
                continue

        filename = photo.filename
        if not filename:
            continue

        # Only download supported image types
        ext = Path(filename).suffix.lower()
        if ext not in PHOTO_EXTENSIONS:
            continue

        dest_file = out / filename
        if dest_file.exists():
            skipped += 1
            continue

        try:
            response = photo.download()
            with open(dest_file, "wb") as f:
                f.write(response.content)
            downloaded += 1
            print(f"  [{downloaded}] {filename}")
        except Exception as exc:
            print(f"  Warning: failed to download {filename}: {exc}")

        if limit and downloaded >= limit:
            break

    print(f"Done: {downloaded} downloaded, {skipped} already existed.")
    return out


def list_icloud_albums(api: object) -> list[str]:
    """Return a list of album names from the iCloud account."""
    return list(api.photos.albums.keys())
