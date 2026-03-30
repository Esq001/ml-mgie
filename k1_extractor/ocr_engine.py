"""
PDF to text extraction engine.

Strategy: Try native PDF text extraction (PyMuPDF) first. If the PDF is
scanned (image-based) and yields insufficient text, fall back to Tesseract OCR
via pdf2image + pytesseract.
"""

import os
import sys
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def extract_text(pdf_path: str) -> Tuple[str, str]:
    """
    Extract text from a PDF file.

    Returns:
        (text, method) where method is "native" or "ocr".

    Raises:
        RuntimeError: If text extraction fails entirely.
    """
    # Try native extraction first
    native_text = _extract_native(pdf_path)
    if _is_sufficient_text(native_text):
        return native_text, "native"

    # Fall back to OCR
    if not check_tesseract_available():
        if native_text.strip():
            logger.warning(
                "Native extraction yielded minimal text and Tesseract is not "
                "available. Returning partial native text for: %s", pdf_path
            )
            return native_text, "native"
        raise RuntimeError(
            f"Could not extract text from '{os.path.basename(pdf_path)}'. "
            "The PDF appears to be scanned but Tesseract OCR is not installed. "
            "Please install Tesseract to process scanned PDFs."
        )

    ocr_text = _extract_ocr(pdf_path)
    if ocr_text.strip():
        return ocr_text, "ocr"

    # If OCR also fails, return whatever native gave us
    if native_text.strip():
        return native_text, "native"

    raise RuntimeError(
        f"Could not extract any text from '{os.path.basename(pdf_path)}'. "
        "The file may be corrupted or contain only images that OCR cannot read."
    )


def _extract_native(pdf_path: str) -> str:
    """Extract text using PyMuPDF (fitz) native text extraction."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not installed. Skipping native extraction.")
        return ""

    text_parts = []
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
    except Exception as e:
        logger.error("PyMuPDF extraction failed for %s: %s", pdf_path, e)
        return ""

    return "\n".join(text_parts)


def _extract_ocr(pdf_path: str) -> str:
    """Extract text using Tesseract OCR (pdf2image + pytesseract)."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError as e:
        logger.error("OCR dependencies not installed: %s", e)
        return ""

    try:
        # Convert PDF pages to images at 300 DPI
        images = convert_from_path(pdf_path, dpi=300)
    except Exception as e:
        logger.error("PDF to image conversion failed for %s: %s", pdf_path, e)
        return ""

    text_parts = []
    for i, image in enumerate(images):
        try:
            processed = _preprocess_image(image)
            # PSM 6: Assume a single uniform block of text
            text = pytesseract.image_to_string(
                processed,
                config="--psm 6 --oem 3"
            )
            text_parts.append(text)
        except Exception as e:
            logger.error("OCR failed on page %d of %s: %s", i + 1, pdf_path, e)

    return "\n".join(text_parts)


def _preprocess_image(image):
    """
    Preprocess an image for better OCR results.
    Converts to grayscale, enhances contrast, and applies sharpening.
    """
    from PIL import ImageEnhance, ImageFilter

    # Convert to grayscale
    gray = image.convert("L")

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(1.5)

    # Sharpen
    sharpened = enhanced.filter(ImageFilter.SHARPEN)

    # Apply threshold to get cleaner black/white
    threshold = 160
    binary = sharpened.point(lambda x: 255 if x > threshold else 0, "1")

    return binary


def _is_sufficient_text(text: str) -> bool:
    """
    Check if extracted text is sufficient to be a valid K-1 form.
    A real K-1 form should have at least a few hundred characters of text.
    """
    stripped = text.strip()
    if len(stripped) < 100:
        return False
    # Check for at least some K-1-related keywords
    keywords = ["schedule", "k-1", "k1", "form", "income", "partner",
                 "shareholder", "beneficiary", "tax year", "ein"]
    text_lower = stripped.lower()
    matches = sum(1 for kw in keywords if kw in text_lower)
    return matches >= 2


def check_tesseract_available() -> bool:
    """Check if Tesseract OCR is installed and accessible."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def get_tesseract_path_hint() -> str:
    """Return a hint about where to install Tesseract on the current platform."""
    if sys.platform == "win32":
        return (
            "Download Tesseract for Windows from:\n"
            "https://github.com/UB-Mannheim/tesseract/wiki\n\n"
            "After installing, add the installation directory "
            "(e.g., C:\\Program Files\\Tesseract-OCR) to your system PATH,\n"
            "or set the TESSERACT_CMD environment variable to the full path "
            "of tesseract.exe."
        )
    elif sys.platform == "darwin":
        return "Install Tesseract via Homebrew: brew install tesseract"
    else:
        return "Install Tesseract via your package manager: sudo apt install tesseract-ocr"
