"""Data models for tax return review application."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class LineItem:
    """A single line item from a tax form."""
    form: str
    line: str
    label: str
    amount: Decimal
    source_file: str = ""


@dataclass
class TaxReturn:
    """Parsed representation of a tax return (1040)."""
    tax_year: Optional[int] = None
    filing_status: str = ""
    line_items: list[LineItem] = field(default_factory=list)
    raw_text: str = ""
    source_file: str = ""

    def get_line(self, line: str) -> Optional[LineItem]:
        """Get a line item by line number."""
        for item in self.line_items:
            if item.line == line:
                return item
        return None

    def get_amount(self, line: str) -> Optional[Decimal]:
        """Get the amount for a specific line number."""
        item = self.get_line(line)
        return item.amount if item else None


@dataclass
class W2Data:
    """Parsed W-2 wage and tax statement."""
    employer_ein: str = ""
    employer_name: str = ""
    employee_name: str = ""
    wages: Decimal = Decimal("0")                  # Box 1
    federal_tax_withheld: Decimal = Decimal("0")   # Box 2
    ss_wages: Decimal = Decimal("0")               # Box 3
    ss_tax: Decimal = Decimal("0")                 # Box 4
    medicare_wages: Decimal = Decimal("0")         # Box 5
    medicare_tax: Decimal = Decimal("0")           # Box 6
    state_wages: Decimal = Decimal("0")            # Box 16
    state_tax: Decimal = Decimal("0")              # Box 17
    source_file: str = ""


@dataclass
class Form1099Data:
    """Parsed 1099 information return."""
    payer_name: str = ""
    variant: str = ""  # INT, DIV, NEC, MISC, R, G
    box_amounts: dict[str, Decimal] = field(default_factory=dict)
    source_file: str = ""

    @property
    def primary_amount(self) -> Decimal:
        """Return the primary reportable amount (typically Box 1)."""
        return self.box_amounts.get("1", Decimal("0"))

    @property
    def federal_tax_withheld(self) -> Decimal:
        """Return federal tax withheld amount."""
        withheld_keys = {"4", "7"}  # Box 4 for most 1099s, Box 7 for some
        for key in withheld_keys:
            if key in self.box_amounts:
                return self.box_amounts[key]
        return Decimal("0")


@dataclass
class ParsedDocuments:
    """Collection of all parsed source documents."""
    w2s: list[W2Data] = field(default_factory=list)
    form_1099s: list[Form1099Data] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
