"""
Regex-based parser for extracting structured data from K-1 form text.

Handles all three K-1 variants:
- Form 1065 (Partnership)
- Form 1120-S (S-Corporation)
- Form 1041 (Estates/Trusts)
"""

import re
import logging
from typing import Optional

from .models import K1Data
from .constants import FORM_DEFINITIONS

logger = logging.getLogger(__name__)


def parse_k1(text: str, source_file: str = "",
             extraction_method: str = "") -> K1Data:
    """
    Parse OCR/extracted text from a K-1 form and return structured data.

    Args:
        text: Full text extracted from the PDF.
        source_file: Original PDF filename for reference.
        extraction_method: "native" or "ocr".

    Returns:
        K1Data with all extracted fields.
    """
    form_type = _detect_form_type(text)
    entity_info = _extract_entity_info(text, form_type)
    recipient_info = _extract_recipient_info(text, form_type)
    boxes = _extract_boxes(text, form_type)

    warnings = []

    # Assess confidence
    confidence = _assess_confidence(
        form_type, entity_info, recipient_info, boxes, warnings
    )

    return K1Data(
        source_file=source_file,
        form_type=form_type,
        entity_name=entity_info.get("name", ""),
        entity_ein=entity_info.get("ein", ""),
        tax_year_begin=entity_info.get("tax_year_begin", ""),
        tax_year_end=entity_info.get("tax_year_end", ""),
        recipient_name=recipient_info.get("name", ""),
        recipient_id=recipient_info.get("id", ""),
        recipient_address=recipient_info.get("address", ""),
        recipient_type=recipient_info.get("type", ""),
        boxes=boxes,
        raw_text=text,
        extraction_method=extraction_method,
        confidence=confidence,
        warnings=warnings,
    )


# =============================================================================
# Form Type Detection
# =============================================================================

def _detect_form_type(text: str) -> str:
    """
    Detect which K-1 variant the text belongs to.

    Returns "1065", "1120S", or "1041". Defaults to "1065" if unclear.
    """
    text_lower = text.lower()

    # Look for explicit form numbers
    if re.search(r"form\s*1120[\-\s]?s", text_lower):
        return "1120S"
    if re.search(r"form\s*1041", text_lower):
        return "1041"
    if re.search(r"form\s*1065", text_lower):
        return "1065"

    # Keyword heuristics
    shareholder_score = sum(1 for kw in ["shareholder", "s corporation", "s corp"]
                           if kw in text_lower)
    beneficiary_score = sum(1 for kw in ["beneficiary", "estate", "trust", "fiduciary"]
                           if kw in text_lower)
    partner_score = sum(1 for kw in ["partner", "partnership", "general partner",
                                      "limited partner"]
                        if kw in text_lower)

    scores = {"1065": partner_score, "1120S": shareholder_score, "1041": beneficiary_score}
    best = max(scores, key=scores.get)

    if scores[best] > 0:
        return best

    # Default to 1065 (most common)
    return "1065"


# =============================================================================
# Entity Info Extraction (Part I)
# =============================================================================

_EIN_PATTERN = re.compile(r"\b(\d{2})[\-\u2014\u2013](\d{7})\b")

_DATE_PATTERN = re.compile(
    r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})"
)

_TAX_YEAR_PATTERN = re.compile(
    r"(?:tax\s*year|calendar\s*year|fiscal\s*year).*?(\d{4})",
    re.IGNORECASE
)


def _extract_entity_info(text: str, form_type: str) -> dict:
    """Extract Part I entity information (name, EIN, tax year)."""
    info = {"name": "", "ein": "", "tax_year_begin": "", "tax_year_end": ""}

    # Extract EIN - first occurrence is usually the entity EIN
    ein_matches = _EIN_PATTERN.findall(text)
    if ein_matches:
        info["ein"] = f"{ein_matches[0][0]}-{ein_matches[0][1]}"

    # Extract entity name based on form type
    definition = FORM_DEFINITIONS.get(form_type, FORM_DEFINITIONS["1065"])
    entity_label = definition["entity_label"].lower()

    # Try patterns like "Partnership's name..." or "Name of partnership"
    name_patterns = [
        re.compile(
            rf"{entity_label}(?:'?s)?\s*(?:name|legal\s*name)[:\s]*([^\n]+)",
            re.IGNORECASE
        ),
        re.compile(
            rf"name\s*of\s*{entity_label}[:\s]*([^\n]+)",
            re.IGNORECASE
        ),
        re.compile(
            r"(?:A\s+)?(?:name\s*,?\s*address)[:\s]*([^\n]+)",
            re.IGNORECASE
        ),
    ]
    for pattern in name_patterns:
        match = pattern.search(text)
        if match:
            name = match.group(1).strip()
            # Clean up: remove trailing form numbers, addresses
            name = re.split(r"\d{2}[\-]\d{7}", name)[0].strip()
            name = name.rstrip(",;: ")
            if len(name) > 2:
                info["name"] = name
                break

    # Extract tax year
    # Look for "beginning ... ending" or "calendar year YYYY"
    begin_match = re.search(
        r"(?:beginning|begin)[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        text, re.IGNORECASE
    )
    end_match = re.search(
        r"(?:ending|end)[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        text, re.IGNORECASE
    )
    if begin_match:
        info["tax_year_begin"] = begin_match.group(1)
    if end_match:
        info["tax_year_end"] = end_match.group(1)

    # Try calendar year pattern
    if not info["tax_year_end"]:
        year_match = _TAX_YEAR_PATTERN.search(text)
        if year_match:
            info["tax_year_end"] = year_match.group(1)

    # Try standalone 4-digit year near "20XX" at top of document
    if not info["tax_year_end"]:
        top_text = text[:500]
        year_match = re.search(r"\b(20\d{2})\b", top_text)
        if year_match:
            info["tax_year_end"] = year_match.group(1)

    return info


# =============================================================================
# Recipient Info Extraction (Part II)
# =============================================================================

_SSN_PATTERN = re.compile(r"\b(\d{3})[\-\u2014\u2013](\d{2})[\-\u2014\u2013](\d{4})\b")


def _extract_recipient_info(text: str, form_type: str) -> dict:
    """Extract Part II recipient information (name, SSN/EIN, address, type)."""
    info = {"name": "", "id": "", "address": "", "type": ""}

    # Extract SSN (XXX-XX-XXXX format) - typically in Part II
    ssn_matches = _SSN_PATTERN.findall(text)
    if ssn_matches:
        info["id"] = f"{ssn_matches[0][0]}-{ssn_matches[0][1]}-{ssn_matches[0][2]}"
    else:
        # May be an EIN (second occurrence if entity EIN is first)
        ein_matches = _EIN_PATTERN.findall(text)
        if len(ein_matches) >= 2:
            info["id"] = f"{ein_matches[1][0]}-{ein_matches[1][1]}"

    # Extract recipient name
    definition = FORM_DEFINITIONS.get(form_type, FORM_DEFINITIONS["1065"])
    recipient_label = definition["recipient_label"].lower()

    name_patterns = [
        re.compile(
            rf"{recipient_label}(?:'?s)?\s*(?:name|legal\s*name)[:\s]*([^\n]+)",
            re.IGNORECASE
        ),
        re.compile(
            rf"name\s*of\s*{recipient_label}[:\s]*([^\n]+)",
            re.IGNORECASE
        ),
    ]
    for pattern in name_patterns:
        match = pattern.search(text)
        if match:
            name = match.group(1).strip()
            name = re.split(r"\d{3}[\-]\d{2}[\-]\d{4}", name)[0].strip()
            name = name.rstrip(",;: ")
            if len(name) > 1:
                info["name"] = name
                break

    # Extract partner type (for 1065)
    if form_type == "1065":
        if re.search(r"general\s*partner", text, re.IGNORECASE):
            info["type"] = "General partner"
        elif re.search(r"limited\s*partner", text, re.IGNORECASE):
            info["type"] = "Limited partner"
    elif form_type == "1120S":
        info["type"] = "Shareholder"
    elif form_type == "1041":
        info["type"] = "Beneficiary"

    # Extract address - look for typical address patterns after recipient name
    addr_match = re.search(
        r"(?:address|street)[:\s]*([^\n]+(?:\n[^\n]+){0,2})",
        text, re.IGNORECASE
    )
    if addr_match:
        addr = addr_match.group(1).strip()
        addr = re.sub(r"\s+", " ", addr)
        info["address"] = addr[:200]  # Cap length

    return info


# =============================================================================
# Box Value Extraction (Part III)
# =============================================================================

# Regex for dollar amounts, including negatives and parenthesized values
_CURRENCY_PATTERN = re.compile(
    r"[\$]?\s*[\(\-]?\s*[\d,]+\.?\d{0,2}\s*[\)]?"
)


def _extract_boxes(text: str, form_type: str) -> dict:
    """
    Extract Part III box values from the text.

    Uses a two-pass strategy:
    1. Look for box numbers followed by dollar amounts
    2. Look for box labels followed by dollar amounts
    """
    definition = FORM_DEFINITIONS.get(form_type, FORM_DEFINITIONS["1065"])
    box_defs = definition["boxes"]
    boxes = {}

    for box_id, box_label in box_defs.items():
        value = _extract_single_box(text, box_id, box_label)
        if value is not None:
            boxes[box_id] = value

    return boxes


# Currency capture: handles ($1,234.56), $(1,234), -$1,234, $1,234.56, (1,234), etc.
_CURRENCY_CAPTURE = r"([\(\-]?\s*[\$]?\s*[\(\-]?\s*[\d,]+\.?\d?\d?\s*[\)]?)"


def _extract_single_box(text: str, box_id: str, box_label: str) -> Optional[str]:
    """
    Try to extract a single box value from the text.

    Tries multiple strategies:
    1. Line-anchored box number: "1a" at start of line followed by label/amount
    2. "Box 1a" pattern anywhere
    3. Label-based: "Ordinary business income" followed by a dollar amount
    """
    escaped_id = re.escape(box_id)

    patterns = [
        # Strategy 1: Box ID at the start of a line (with optional whitespace),
        # followed by label text and then a dollar amount.
        # e.g., "  1  Ordinary business income (loss)  $45,000"
        re.compile(
            r"^\s*" + escaped_id + r"\s+[A-Za-z].*?" + _CURRENCY_CAPTURE,
            re.IGNORECASE | re.MULTILINE
        ),
        # Strategy 2: "Box 1a" explicitly labeled
        re.compile(
            r"\bbox\s+" + escaped_id + r"\b[.\s:]*?" + _CURRENCY_CAPTURE,
            re.IGNORECASE
        ),
        # Strategy 3: Match the label text followed by a dollar amount on the same line
        re.compile(
            re.escape(box_label[:30]) + r"[^$\d\n]*?" + _CURRENCY_CAPTURE,
            re.IGNORECASE
        ),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            raw_value = match.group(1).strip()
            cleaned = clean_currency(raw_value)
            if cleaned and cleaned != "0":
                return cleaned

    return None


def clean_currency(raw: str) -> str:
    """
    Clean and normalize a raw currency string from OCR output.

    Handles:
    - Dollar signs: "$1,234.56" -> "1234.56"
    - Parenthesized negatives: "(1,234.56)" -> "-1234.56"
    - Dash negatives: "-1,234.56" -> "-1234.56"
    - Comma removal: "1,234,567" -> "1234567"
    - Common OCR errors: "S" for "$", "l" for "1", "O" for "0"
    """
    if not raw:
        return ""

    s = raw.strip()

    # Fix common OCR misreads
    s = s.replace("S", "$", 1) if s.startswith("S") and len(s) > 1 and s[1:2].isdigit() else s
    s = s.replace("$", "")
    s = s.replace(" ", "")

    # Handle parenthesized negatives
    is_negative = False
    if s.startswith("(") and s.endswith(")"):
        is_negative = True
        s = s[1:-1]
    elif s.startswith("-"):
        is_negative = True
        s = s[1:]

    # Remove commas
    s = s.replace(",", "")

    # Fix OCR: 'l' or 'I' at start often means '1'
    if s and s[0] in ("l", "I") and len(s) > 1:
        s = "1" + s[1:]

    # Fix OCR: 'O' often means '0'
    s = s.replace("O", "0")

    # Validate it's a number
    try:
        val = float(s)
    except (ValueError, TypeError):
        return ""

    if val == 0:
        return ""

    if is_negative:
        val = -val

    # Format: remove unnecessary decimals
    if val == int(val):
        return str(int(val))
    return f"{val:.2f}"


# =============================================================================
# Confidence Assessment
# =============================================================================

def _assess_confidence(form_type: str, entity_info: dict,
                       recipient_info: dict, boxes: dict,
                       warnings: list) -> str:
    """
    Assess extraction confidence based on how many fields were found.

    Returns "high", "medium", or "low".
    """
    score = 0
    max_score = 0

    # Entity info
    max_score += 3
    if entity_info.get("name"):
        score += 1
    else:
        warnings.append("Entity name not found")
    if entity_info.get("ein"):
        score += 1
    else:
        warnings.append("Entity EIN not found")
    if entity_info.get("tax_year_end") or entity_info.get("tax_year_begin"):
        score += 1
    else:
        warnings.append("Tax year not found")

    # Recipient info
    max_score += 2
    if recipient_info.get("name"):
        score += 1
    else:
        warnings.append("Recipient name not found")
    if recipient_info.get("id"):
        score += 1
    else:
        warnings.append("Recipient ID (SSN/EIN) not found")

    # Box values - at least some should be present
    max_score += 3
    num_boxes = len(boxes)
    if num_boxes >= 3:
        score += 3
    elif num_boxes >= 1:
        score += 2
    elif num_boxes == 0:
        warnings.append("No box values extracted")

    ratio = score / max_score if max_score > 0 else 0

    if ratio >= 0.75:
        return "high"
    elif ratio >= 0.5:
        return "medium"
    return "low"
