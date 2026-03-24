"""Comparison rules for tax return review."""

from dataclasses import dataclass
from decimal import Decimal

from ..models.enums import DiscrepancyLevel


@dataclass
class ComparisonRule:
    """Rule defining how to compare a specific line item."""
    line: str
    label: str
    tolerance_dollars: Decimal = Decimal("1.00")
    tolerance_percent: Decimal = Decimal("0")
    yoy_variance_warning_pct: Decimal = Decimal("20")  # year-over-year warning threshold


# Default rules for key 1040 lines
DEFAULT_RULES = [
    ComparisonRule("1", "Wages, salaries, tips"),
    ComparisonRule("2b", "Taxable interest"),
    ComparisonRule("3a", "Qualified dividends"),
    ComparisonRule("3b", "Ordinary dividends"),
    ComparisonRule("4b", "IRA distributions taxable"),
    ComparisonRule("5b", "Pensions taxable"),
    ComparisonRule("6b", "Social security taxable"),
    ComparisonRule("7", "Capital gain or loss"),
    ComparisonRule("8", "Other income"),
    ComparisonRule("9", "Total income"),
    ComparisonRule("11", "Adjusted gross income"),
    ComparisonRule("12", "Standard/itemized deductions"),
    ComparisonRule("15", "Taxable income"),
    ComparisonRule("16", "Tax"),
    ComparisonRule("24", "Total tax"),
    ComparisonRule("25a", "W-2 withholding"),
    ComparisonRule("25d", "Total federal tax withheld"),
    ComparisonRule("26", "Estimated tax payments"),
    ComparisonRule("33", "Total payments"),
    ComparisonRule("35a", "Refund"),
    ComparisonRule("37", "Amount you owe"),
]


def get_rule_for_line(line: str) -> ComparisonRule:
    """Get the comparison rule for a given line number."""
    for rule in DEFAULT_RULES:
        if rule.line == line:
            return rule
    return ComparisonRule(line=line, label=f"Line {line}")
