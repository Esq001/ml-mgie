"""
Entry point for running the K-1 Extractor as a module:
    python -m k1_extractor
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

from k1_extractor.gui import K1ExtractorApp


def main():
    app = K1ExtractorApp()
    app.run()


if __name__ == "__main__":
    main()
