"""
Data classes for representing extracted K-1 form data.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class K1Data:
    """Represents all extracted data from a single K-1 form."""

    source_file: str
    form_type: str  # "1065", "1120S", or "1041"

    # Part I: Entity information (Partnership / S-Corp / Estate or Trust)
    entity_name: str = ""
    entity_ein: str = ""
    tax_year_begin: str = ""
    tax_year_end: str = ""

    # Part II: Recipient information (Partner / Shareholder / Beneficiary)
    recipient_name: str = ""
    recipient_id: str = ""  # SSN or EIN
    recipient_address: str = ""
    recipient_type: str = ""  # e.g., "General partner", "Limited partner"

    # Part III: Box values as a dict mapping box ID -> extracted value string
    boxes: dict = field(default_factory=dict)

    # Metadata
    raw_text: str = ""
    extraction_method: str = ""  # "native" or "ocr"
    confidence: str = "low"  # "high", "medium", or "low"
    warnings: list = field(default_factory=list)

    @property
    def tax_year(self) -> str:
        """Return a display-friendly tax year string."""
        if self.tax_year_begin and self.tax_year_end:
            return f"{self.tax_year_begin} - {self.tax_year_end}"
        return self.tax_year_end or self.tax_year_begin or ""

    def box_value_as_float(self, box_id: str) -> Optional[float]:
        """Try to convert a box value to float. Returns None if not possible."""
        raw = self.boxes.get(box_id, "")
        if not raw:
            return None
        try:
            cleaned = raw.replace(",", "").replace("$", "").strip()
            # Handle parenthesized negatives: (1234.56) -> -1234.56
            if cleaned.startswith("(") and cleaned.endswith(")"):
                cleaned = "-" + cleaned[1:-1]
            return float(cleaned)
        except (ValueError, TypeError):
            return None
