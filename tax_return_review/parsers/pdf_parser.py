"""PDF text extraction and form-type auto-detection."""

import os
from typing import Union

from ..models.enums import FormType
from ..models.tax_data import Form1099Data, TaxReturn, W2Data
from .form_1040_parser import Form1040Parser
from .form_1099_parser import Form1099Parser
from .w2_parser import W2Parser

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def extract_text_from_pdf(filepath: str) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    if not HAS_PDFPLUMBER:
        raise ImportError(
            "pdfplumber is required for PDF parsing. "
            "Install it with: pip install pdfplumber"
        )

    text_parts = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

            # Also try extracting tables for structured forms like W-2
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row:
                        cleaned = [str(cell).strip() if cell else "" for cell in row]
                        text_parts.append("  ".join(cleaned))

    return "\n".join(text_parts)


def detect_form_type(text: str) -> FormType:
    """Detect which tax form type the text represents."""
    text_lower = text.lower()

    # Check W-2 first (it's a very distinct form)
    if ("w-2" in text_lower or "wage and tax statement" in text_lower) and \
       "w-2" in text_lower:
        return FormType.W2

    # Check 1099 variants
    if "1099" in text_lower:
        if "1099-int" in text_lower or "interest income" in text_lower:
            return FormType.FORM_1099_INT
        if "1099-div" in text_lower or "dividends" in text_lower:
            return FormType.FORM_1099_DIV
        if "1099-nec" in text_lower or "nonemployee" in text_lower:
            return FormType.FORM_1099_NEC
        if "1099-misc" in text_lower:
            return FormType.FORM_1099_MISC
        if "1099-r" in text_lower:
            return FormType.FORM_1099_R
        if "1099-g" in text_lower:
            return FormType.FORM_1099_G
        return FormType.FORM_1099_INT  # default 1099

    # Check Form 1040
    if "1040" in text_lower or "individual income tax" in text_lower or \
       "adjusted gross income" in text_lower:
        return FormType.FORM_1040

    return FormType.UNKNOWN


def parse_pdf(filepath: str) -> Union[TaxReturn, W2Data, Form1099Data]:
    """Parse a PDF tax document and return the appropriate data model.

    Auto-detects the form type and delegates to the correct parser.
    """
    text = extract_text_from_pdf(filepath)

    if not text.strip():
        raise ValueError(
            f"Could not extract text from '{os.path.basename(filepath)}'. "
            "The PDF may be a scanned image. Please provide a text-based PDF."
        )

    form_type = detect_form_type(text)
    filename = os.path.basename(filepath)

    if form_type == FormType.W2:
        parser = W2Parser()
        return parser.parse(text, filename)
    elif form_type in (
        FormType.FORM_1099_INT, FormType.FORM_1099_DIV, FormType.FORM_1099_NEC,
        FormType.FORM_1099_MISC, FormType.FORM_1099_R, FormType.FORM_1099_G,
    ):
        parser = Form1099Parser()
        return parser.parse(text, filename)
    elif form_type == FormType.FORM_1040:
        parser = Form1040Parser()
        return parser.parse(text, filename)
    else:
        # Default to 1040 parser as a best effort
        parser = Form1040Parser()
        result = parser.parse(text, filename)
        if not result.line_items:
            raise ValueError(
                f"Could not identify the form type in '{filename}'. "
                "Supported forms: 1040, W-2, 1099."
            )
        return result


def parse_file(filepath: str) -> Union[TaxReturn, W2Data, Form1099Data]:
    """Parse any supported file type (PDF, CSV, JSON)."""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return parse_pdf(filepath)
    elif ext in (".csv", ".json"):
        from .csv_parser import parse_structured_file
        return parse_structured_file(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF, CSV, or JSON.")
