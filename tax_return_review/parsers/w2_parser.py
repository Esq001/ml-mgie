"""Parser for W-2 Wage and Tax Statement."""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..models.tax_data import W2Data
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


# Patterns for each W-2 box
BOX_PATTERNS = {
    "wages": [
        r"(?:box\s*)?1\b[^0-9$]*wages[^$\d]*(\$?[\d,]+\.?\d*)",
        r"wages[,\s]+(?:tips[,\s]+)?(?:other\s+)?comp[^$\d]*(\$?[\d,]+\.?\d*)",
        r"(?:box\s+1|box1)\s*[:\.]?\s*(\$?[\d,]+\.?\d*)",
    ],
    "federal_tax_withheld": [
        r"(?:box\s*)?2\b[^0-9$]*federal[^$\d]*(\$?[\d,]+\.?\d*)",
        r"federal\s+(?:income\s+)?tax\s+withheld[^$\d]*(\$?[\d,]+\.?\d*)",
        r"(?:box\s+2|box2)\s*[:\.]?\s*(\$?[\d,]+\.?\d*)",
    ],
    "ss_wages": [
        r"(?:box\s*)?3\b[^0-9$]*social\s+security\s+wages[^$\d]*(\$?[\d,]+\.?\d*)",
        r"social\s+security\s+wages[^$\d]*(\$?[\d,]+\.?\d*)",
        r"(?:box\s+3|box3)\s*[:\.]?\s*(\$?[\d,]+\.?\d*)",
    ],
    "ss_tax": [
        r"(?:box\s*)?4\b[^0-9$]*social\s+security\s+tax[^$\d]*(\$?[\d,]+\.?\d*)",
        r"social\s+security\s+tax\s+withheld[^$\d]*(\$?[\d,]+\.?\d*)",
        r"(?:box\s+4|box4)\s*[:\.]?\s*(\$?[\d,]+\.?\d*)",
    ],
    "medicare_wages": [
        r"(?:box\s*)?5\b[^0-9$]*medicare\s+wages[^$\d]*(\$?[\d,]+\.?\d*)",
        r"medicare\s+wages\s+and\s+tips[^$\d]*(\$?[\d,]+\.?\d*)",
        r"(?:box\s+5|box5)\s*[:\.]?\s*(\$?[\d,]+\.?\d*)",
    ],
    "medicare_tax": [
        r"(?:box\s*)?6\b[^0-9$]*medicare\s+tax[^$\d]*(\$?[\d,]+\.?\d*)",
        r"medicare\s+tax\s+withheld[^$\d]*(\$?[\d,]+\.?\d*)",
        r"(?:box\s+6|box6)\s*[:\.]?\s*(\$?[\d,]+\.?\d*)",
    ],
    "state_wages": [
        r"(?:box\s*)?16\b[^0-9$]*state\s+wages[^$\d]*(\$?[\d,]+\.?\d*)",
        r"state\s+wages[^$\d]*(\$?[\d,]+\.?\d*)",
    ],
    "state_tax": [
        r"(?:box\s*)?17\b[^0-9$]*state\s+(?:income\s+)?tax[^$\d]*(\$?[\d,]+\.?\d*)",
        r"state\s+(?:income\s+)?tax\s+withheld[^$\d]*(\$?[\d,]+\.?\d*)",
    ],
}

EMPLOYER_NAME_PATTERN = re.compile(
    r"employer['\u2019]?s?\s+name[^:\n]*[:\s]+([^\n]+)", re.IGNORECASE
)
EMPLOYER_EIN_PATTERN = re.compile(
    r"employer['\u2019]?s?\s+(?:identification\s+number|EIN|ID)[^:\n]*[:\s]+"
    r"(\d{2}-?\d{7})", re.IGNORECASE
)
EMPLOYEE_NAME_PATTERN = re.compile(
    r"employee['\u2019]?s?\s+(?:first\s+)?name[^:\n]*[:\s]+([^\n]+)", re.IGNORECASE
)


class W2Parser(BaseParser):
    """Parser for W-2 Wage and Tax Statement."""

    def can_parse(self, text: str) -> bool:
        text_lower = text.lower()
        return (
            "w-2" in text_lower
            or "w2" in text_lower
            or "wage and tax statement" in text_lower
        ) and (
            "wages" in text_lower
            or "federal" in text_lower
            or "employer" in text_lower
        )

    def parse(self, text: str, source_file: str) -> W2Data:
        text_lower = text.lower()
        w2 = W2Data(source_file=source_file)

        # Extract employer info
        m = EMPLOYER_NAME_PATTERN.search(text)
        if m:
            w2.employer_name = m.group(1).strip()

        m = EMPLOYER_EIN_PATTERN.search(text)
        if m:
            w2.employer_ein = m.group(1).strip()

        m = EMPLOYEE_NAME_PATTERN.search(text)
        if m:
            w2.employee_name = m.group(1).strip()

        # Extract box amounts
        for field_name, patterns in BOX_PATTERNS.items():
            for pattern in patterns:
                m = re.search(pattern, text_lower)
                if m:
                    setattr(w2, field_name, _parse_amount(m.group(1)))
                    break

        return w2
