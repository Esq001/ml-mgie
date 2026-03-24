"""Parser for 1099 information returns (INT, DIV, NEC, MISC, R, G)."""

import re
from decimal import Decimal, InvalidOperation

from ..models.tax_data import Form1099Data
from .base_parser import BaseParser


def _parse_amount(raw: str) -> Decimal:
    """Parse a dollar amount string into a Decimal."""
    if not raw:
        return Decimal("0")
    cleaned = raw.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return Decimal("0")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


# Variant detection patterns
VARIANT_PATTERNS = [
    ("INT", [r"1099-?\s*INT", r"interest\s+income"]),
    ("DIV", [r"1099-?\s*DIV", r"dividends\s+and\s+distributions"]),
    ("NEC", [r"1099-?\s*NEC", r"nonemployee\s+compensation"]),
    ("MISC", [r"1099-?\s*MISC", r"miscellaneous\s+(?:income|information)"]),
    ("R", [r"1099-?\s*R\b", r"distributions\s+from\s+pensions"]),
    ("G", [r"1099-?\s*G\b", r"government\s+payments"]),
]

# Box definitions per variant: {variant: [(box_num, label, [patterns])]}
VARIANT_BOXES = {
    "INT": [
        ("1", "Interest income", [r"(?:box\s*)?1[^0-9]*interest\s+income[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("2", "Early withdrawal penalty", [r"(?:box\s*)?2[^0-9]*early\s+withdrawal[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("3", "Interest on U.S. savings bonds", [r"(?:box\s*)?3[^0-9]*(?:u\.?s\.?\s+)?savings\s+bonds[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("4", "Federal income tax withheld", [r"(?:box\s*)?4[^0-9]*federal[^$\d]*(\$?[\d,]+\.?\d*)"]),
    ],
    "DIV": [
        ("1a", "Total ordinary dividends", [r"(?:box\s*)?1a[^0-9]*(?:total\s+)?ordinary\s+dividends[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("1b", "Qualified dividends", [r"(?:box\s*)?1b[^0-9]*qualified\s+dividends[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("2a", "Total capital gain distributions", [r"(?:box\s*)?2a[^0-9]*capital\s+gain[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("4", "Federal income tax withheld", [r"(?:box\s*)?4[^0-9]*federal[^$\d]*(\$?[\d,]+\.?\d*)"]),
    ],
    "NEC": [
        ("1", "Nonemployee compensation", [r"(?:box\s*)?1[^0-9]*nonemployee\s+comp[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("4", "Federal income tax withheld", [r"(?:box\s*)?4[^0-9]*federal[^$\d]*(\$?[\d,]+\.?\d*)"]),
    ],
    "MISC": [
        ("1", "Rents", [r"(?:box\s*)?1[^0-9]*rents[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("2", "Royalties", [r"(?:box\s*)?2[^0-9]*royalties[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("3", "Other income", [r"(?:box\s*)?3[^0-9]*other\s+income[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("4", "Federal income tax withheld", [r"(?:box\s*)?4[^0-9]*federal[^$\d]*(\$?[\d,]+\.?\d*)"]),
    ],
    "R": [
        ("1", "Gross distribution", [r"(?:box\s*)?1[^0-9]*gross\s+distribution[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("2a", "Taxable amount", [r"(?:box\s*)?2a[^0-9]*taxable\s+amount[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("4", "Federal income tax withheld", [r"(?:box\s*)?4[^0-9]*federal[^$\d]*(\$?[\d,]+\.?\d*)"]),
    ],
    "G": [
        ("1", "Unemployment compensation", [r"(?:box\s*)?1[^0-9]*unemployment[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("2", "State or local income tax refunds", [r"(?:box\s*)?2[^0-9]*(?:state|local)\s+.*refund[^$\d]*(\$?[\d,]+\.?\d*)"]),
        ("4", "Federal income tax withheld", [r"(?:box\s*)?4[^0-9]*federal[^$\d]*(\$?[\d,]+\.?\d*)"]),
    ],
}

PAYER_PATTERN = re.compile(
    r"payer['\u2019]?s?\s+name[^:\n]*[:\s]+([^\n]+)", re.IGNORECASE
)


class Form1099Parser(BaseParser):
    """Parser for all 1099 variants."""

    def can_parse(self, text: str) -> bool:
        text_lower = text.lower()
        return "1099" in text_lower

    def parse(self, text: str, source_file: str) -> Form1099Data:
        text_lower = text.lower()
        data = Form1099Data(source_file=source_file)

        # Detect variant
        for variant, patterns in VARIANT_PATTERNS:
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    data.variant = variant
                    break
            if data.variant:
                break

        if not data.variant:
            data.variant = "UNKNOWN"

        # Extract payer name
        m = PAYER_PATTERN.search(text)
        if m:
            data.payer_name = m.group(1).strip()

        # Extract box amounts based on variant
        box_defs = VARIANT_BOXES.get(data.variant, [])
        for box_num, _label, patterns in box_defs:
            for pattern in patterns:
                m = re.search(pattern, text_lower)
                if m:
                    amount = _parse_amount(m.group(1))
                    if amount > 0:
                        data.box_amounts[box_num] = amount
                    break

        # Fallback: try generic box pattern extraction
        if not data.box_amounts:
            generic_pattern = r"box\s*(\d+[a-z]?)\s*[:\.]?\s*(\$?[\d,]+\.?\d*)"
            for m in re.finditer(generic_pattern, text_lower):
                box_num = m.group(1)
                amount = _parse_amount(m.group(2))
                if amount > 0:
                    data.box_amounts[box_num] = amount

        return data
