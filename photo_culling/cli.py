"""Command-line interface for the photo culling tool."""

import argparse
import sys

from .culler import cull_photos
from .icloud import (
    find_icloud_photos_dir,
    list_icloud_sources,
    icloud_login,
    download_icloud_photos,
    list_icloud_albums,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="photo-cull",
        description="Cull photos by scoring quality and detecting duplicates.",
    )
    parser.add_argument(
        "source_dir",
        nargs="?",
        default=None,
        help="Directory containing photos to cull (omit when using --icloud).",
    )
    parser.add_argument(
        "--icloud",
        action="store_true",
        help="Auto-detect iCloud Photos sync folder and use it as source.",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List detected iCloud photo sources and exit.",
    )
    parser.add_argument(
        "--icloud-download",
        action="store_true",
        help="Log in to iCloud and download photos directly from your account.",
    )
    parser.add_argument(
        "--apple-id",
        default=None,
        help="Apple ID for iCloud login (or set ICLOUD_APPLE_ID env var).",
    )
    parser.add_argument(
        "--album",
        default=None,
        help="iCloud album to download from (default: All Photos).",
    )
    parser.add_argument(
        "--list-albums",
        action="store_true",
        help="Log in to iCloud and list available photo albums, then exit.",
    )
    parser.add_argument(
        "--download-limit",
        type=int,
        default=None,
        help="Maximum number of photos to download from iCloud.",
    )
    parser.add_argument(
        "--recent-days",
        type=int,
        default=None,
        help="Only download photos from the last N days.",
    )
    parser.add_argument(
        "--keep-threshold",
        type=float,
        default=0.60,
        help="Minimum overall score to auto-keep (default: 0.60).",
    )
    parser.add_argument(
        "--reject-threshold",
        type=float,
        default=0.35,
        help="Score below which photos are auto-rejected (default: 0.35).",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.85,
        help="Similarity above which photos are grouped as duplicates (default: 0.85).",
    )
    parser.add_argument(
        "--use-clip",
        action="store_true",
        help="Use CLIP for semantic similarity (slower, requires GPU).",
    )
    parser.add_argument(
        "--organize",
        action="store_true",
        help="Copy files into keep/review/reject sub-folders.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Destination for organized folders (defaults to source_dir).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Print results as JSON instead of a human-readable summary.",
    )

    args = parser.parse_args(argv)

    # --list-sources: show detected iCloud directories and exit
    if args.list_sources:
        sources = list_icloud_sources()
        if not sources:
            print("No iCloud Photos folders detected.")
            print(f"Tip: set the ICLOUD_PHOTOS_DIR environment variable to your sync path.")
        else:
            print("Detected iCloud Photos sources:")
            for src in sources:
                print(f"  {src['label']}: {src['path']}")
        return

    # --list-albums: log in and show albums
    if args.list_albums:
        api = icloud_login(apple_id=args.apple_id)
        albums = list_icloud_albums(api)
        print("iCloud Photo albums:")
        for name in albums:
            print(f"  {name}")
        return

    # --icloud-download: pull photos from iCloud API, then cull them
    if args.icloud_download:
        api = icloud_login(apple_id=args.apple_id)
        dest = args.output_dir or args.source_dir
        download_dir = download_icloud_photos(
            api,
            dest_dir=dest,
            album=args.album,
            limit=args.download_limit,
            recent_days=args.recent_days,
        )
        # Use the download directory as the source for culling
        args.source_dir = str(download_dir)

    # Resolve source directory
    source_dir = args.source_dir
    if args.icloud:
        icloud_dir = find_icloud_photos_dir()
        if icloud_dir is None:
            print(
                "Error: no iCloud Photos folder found.\n"
                "Set the ICLOUD_PHOTOS_DIR environment variable to your sync path,\n"
                "or use --list-sources to see detected locations.",
                file=sys.stderr,
            )
            sys.exit(1)
        source_dir = str(icloud_dir)
        print(f"Using iCloud Photos folder: {source_dir}")
    elif source_dir is None:
        parser.error("source_dir is required (or use --icloud)")

    try:
        report = cull_photos(
            source_dir,
            keep_threshold=args.keep_threshold,
            reject_threshold=args.reject_threshold,
            similarity_threshold=args.similarity_threshold,
            use_clip=args.use_clip,
            organize=args.organize,
            output_dir=args.output_dir,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output_json:
        print(report.to_json())
    else:
        print(report.summary())


if __name__ == "__main__":
    main()
