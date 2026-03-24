"""Parser for IRS Form 1040 (U.S. Individual Income Tax Return)."""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..models.tax_data import LineItem, TaxReturn
from .base_parser import BaseParser

# Mapping of 1040 line numbers to labels and regex patterns.
# Patterns are designed to match common tax software output formats.
LINE_DEFINITIONS = [
    ("1", "Wages, salaries, tips", [
        r"(?:line\s*)?1\b[^0-9a-z]*wages[^$\d]*(\$?[\d,]+\.?\d*)",
        r"wages[,\s]+salaries[,\s]+tips[^$\d]*(\$?[\d,]+\.?\d*)",
        r"(?:^|\n)\s*1\s+[\d,]+\.?\d*\s+([\d,]+\.?\d*)",
    ]),
    ("2a", "Tax-exempt interest", [
        r"(?:line\s*)?2a\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"tax[- ]exempt\s+interest[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("2b", "Taxable interest", [
        r"(?:line\s*)?2b\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"taxable\s+interest[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("3a", "Qualified dividends", [
        r"(?:line\s*)?3a\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"qualified\s+dividends[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("3b", "Ordinary dividends", [
        r"(?:line\s*)?3b\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"ordinary\s+dividends[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("4a", "IRA distributions", [
        r"(?:line\s*)?4a\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"ira\s+distributions[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("4b", "IRA distributions taxable", [
        r"(?:line\s*)?4b\b[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("5a", "Pensions and annuities", [
        r"(?:line\s*)?5a\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"pensions\s+and\s+annuities[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("5b", "Pensions taxable", [
        r"(?:line\s*)?5b\b[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("6a", "Social security benefits", [
        r"(?:line\s*)?6a\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"social\s+security\s+benefits[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("6b", "Social security taxable", [
        r"(?:line\s*)?6b\b[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("7", "Capital gain or loss", [
        r"(?:line\s*)?7\b[^$\d]*capital\s+gain[^$\d]*(\$?[\d,]+\.?\d*)",
        r"capital\s+gain\s+or\s+\(?loss\)?[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("8", "Other income", [
        r"(?:line\s*)?8\b[^$\d]*other\s+income[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("9", "Total income", [
        r"(?:line\s*)?9\b[^$\d]*total\s+income[^$\d]*(\$?[\d,]+\.?\d*)",
        r"total\s+income[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("10", "Adjustments to income", [
        r"(?:line\s*)?10\b[^$\d]*adjustments[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("11", "Adjusted gross income", [
        r"(?:line\s*)?11\b[^$\d]*adjusted\s+gross[^$\d]*(\$?[\d,]+\.?\d*)",
        r"adjusted\s+gross\s+income[^$\d]*(\$?[\d,]+\.?\d*)",
        r"AGI[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("12", "Standard/itemized deductions", [
        r"(?:line\s*)?12\b[^$\d]*deductions?[^$\d]*(\$?[\d,]+\.?\d*)",
        r"standard\s+deduction[^$\d]*(\$?[\d,]+\.?\d*)",
        r"itemized\s+deductions?[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("13", "Qualified business income deduction", [
        r"(?:line\s*)?13\b[^$\d]*qualified\s+business[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("14", "Total deductions", [
        r"(?:line\s*)?14\b[^$\d]*total\s+deductions[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("15", "Taxable income", [
        r"(?:line\s*)?15\b[^$\d]*taxable\s+income[^$\d]*(\$?[\d,]+\.?\d*)",
        r"taxable\s+income[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("16", "Tax", [
        r"(?:line\s*)?16\b[^$\d]*(?:^|\s)tax(?:\s|$)[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("24", "Total tax", [
        r"(?:line\s*)?24\b[^$\d]*total\s+tax[^$\d]*(\$?[\d,]+\.?\d*)",
        r"total\s+tax[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("25a", "W-2 withholding", [
        r"(?:line\s*)?25a\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"w-?2\s+withholding[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("25b", "1099 withholding", [
        r"(?:line\s*)?25b\b[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("25d", "Total federal tax withheld", [
        r"(?:line\s*)?25d\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"total\s+federal\s+tax\s+withheld[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("26", "Estimated tax payments", [
        r"(?:line\s*)?26\b[^$\d]*estimated\s+tax[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("33", "Total payments", [
        r"(?:line\s*)?33\b[^$\d]*total\s+payments[^$\d]*(\$?[\d,]+\.?\d*)",
        r"total\s+payments[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("34", "Overpayment", [
        r"(?:line\s*)?34\b[^$\d]*overpay[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("35a", "Refund", [
        r"(?:line\s*)?35a\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"refund[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
    ("37", "Amount you owe", [
        r"(?:line\s*)?37\b[^$\d]*(\$?[\d,]+\.?\d*)",
        r"amount\s+you\s+owe[^$\d]*(\$?[\d,]+\.?\d*)",
    ]),
]

FILING_STATUS_PATTERNS = [
    (r"single", "Single"),
    (r"married\s+filing\s+joint", "Married Filing Jointly"),
    (r"married\s+filing\s+separate", "Married Filing Separately"),
    (r"head\s+of\s+household", "Head of Household"),
    (r"qualifying\s+(?:surviving\s+)?(?:widow|spouse)", "Qualifying Surviving Spouse"),
]

TAX_YEAR_PATTERN = re.compile(r"(?:tax\s+year|for\s+(?:the\s+)?year)\s*(\d{4})", re.IGNORECASE)
TAX_YEAR_PATTERN2 = re.compile(r"20[12]\d\s+(?:form\s+)?1040|(?:form\s+)?1040\s+20[12]\d", re.IGNORECASE)


def _parse_amount(raw: str) -> Optional[Decimal]:
    """Parse a dollar amount string into a Decimal."""
    if not raw:
        return None
    cleaned = raw.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


class Form1040Parser(BaseParser):
    """Parser for IRS Form 1040."""

    def can_parse(self, text: str) -> bool:
        text_lower = text.lower()
        return "1040" in text_lower and (
            "individual income tax" in text_lower
            or "u.s. individual" in text_lower
            or "form 1040" in text_lower
            or "adjusted gross income" in text_lower
            or "taxable income" in text_lower
        )

    def parse(self, text: str, source_file: str) -> TaxReturn:
        tax_return = TaxReturn(source_file=source_file, raw_text=text)
        text_lower = text.lower()

        # Extract tax year
        m = TAX_YEAR_PATTERN.search(text)
        if m:
            tax_return.tax_year = int(m.group(1))
        else:
            m2 = TAX_YEAR_PATTERN2.search(text)
            if m2:
                years = re.findall(r"(20[12]\d)", m2.group(0))
                if years:
                    tax_return.tax_year = int(years[0])

        # Extract filing status
        for pattern, status in FILING_STATUS_PATTERNS:
            if re.search(pattern, text_lower):
                tax_return.filing_status = status
                break

        # Extract line items
        for line_num, label, patterns in LINE_DEFINITIONS:
            for pattern in patterns:
                m = re.search(pattern, text_lower)
                if m:
                    amount = _parse_amount(m.group(1))
                    if amount is not None:
                        tax_return.line_items.append(LineItem(
                            form="1040",
                            line=line_num,
                            label=label,
                            amount=amount,
                            source_file=source_file,
                        ))
                        break

        return tax_return
