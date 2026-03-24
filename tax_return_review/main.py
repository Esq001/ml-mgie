"""Entry point for the Tax Return Review Tool.

Usage:
    python -m tax_return_review.main

Requires: Python 3.10+, pdfplumber (pip install pdfplumber)
"""

import sys
import tkinter as tk
from tkinter import messagebox


def main():
    """Launch the Tax Return Review Tool."""
    root = tk.Tk()

    # Check pdfplumber availability and show warning if missing
    try:
        import pdfplumber  # noqa: F401
    except ImportError:
        messagebox.showwarning(
            "Optional Dependency Missing",
            "pdfplumber is not installed. PDF parsing will not be available.\n\n"
            "Install it with:\n  pip install pdfplumber\n\n"
            "You can still use CSV/JSON file imports.",
        )

    from .gui.app import TaxReviewApp

    app = TaxReviewApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
