"""Core three-way comparison engine for tax return review."""

from decimal import Decimal
from typing import Optional

from ..models.enums import DiscrepancyLevel
from ..models.tax_data import TaxReturn
from ..reports.report_model import ComparisonReport, ReportItem
from .rules import DEFAULT_RULES, get_rule_for_line


def _compare_values(
    label: str,
    prior: Optional[Decimal],
    source: Optional[Decimal],
    draft: Optional[Decimal],
    tolerance: Decimal = Decimal("1.00"),
    yoy_warning_pct: Decimal = Decimal("20"),
) -> tuple[DiscrepancyLevel, str]:
    """Compare up to three values and return status + notes."""
    notes_parts = []
    worst_level = DiscrepancyLevel.MATCH

    def upgrade_level(current: DiscrepancyLevel, new: DiscrepancyLevel) -> DiscrepancyLevel:
        order = {
            DiscrepancyLevel.MATCH: 0,
            DiscrepancyLevel.WARNING: 1,
            DiscrepancyLevel.ERROR: 2,
            DiscrepancyLevel.MISSING: 3,
        }
        return new if order[new] > order[current] else current

    # Check source docs vs draft (most important comparison)
    if source is not None and draft is not None:
        diff = abs(source - draft)
        if diff > tolerance:
            notes_parts.append(
                f"Draft ({_fmt(draft)}) differs from source docs ({_fmt(source)}) "
                f"by {_fmt(diff)}"
            )
            worst_level = upgrade_level(worst_level, DiscrepancyLevel.ERROR)
        elif diff > 0:
            notes_parts.append(f"Minor rounding difference vs source docs ({_fmt(diff)})")
            worst_level = upgrade_level(worst_level, DiscrepancyLevel.WARNING)
    elif source is not None and draft is None:
        notes_parts.append(f"Source docs show {_fmt(source)} but draft has no value")
        worst_level = upgrade_level(worst_level, DiscrepancyLevel.MISSING)
    elif source is None and draft is not None:
        # Source docs don't have this line - not necessarily an error
        pass

    # Check prior year vs draft (year-over-year variance)
    if prior is not None and draft is not None:
        if prior > 0:
            pct_change = abs(draft - prior) / prior * 100
            if pct_change > yoy_warning_pct:
                direction = "increased" if draft > prior else "decreased"
                notes_parts.append(
                    f"Year-over-year {direction} by {pct_change:.1f}% "
                    f"(prior: {_fmt(prior)}, draft: {_fmt(draft)})"
                )
                worst_level = upgrade_level(worst_level, DiscrepancyLevel.WARNING)
    elif prior is not None and draft is None:
        notes_parts.append(f"Prior year had {_fmt(prior)} but draft has no value")
        worst_level = upgrade_level(worst_level, DiscrepancyLevel.WARNING)

    # Check prior year vs source docs
    if prior is not None and source is not None and prior > 0:
        pct_change = abs(source - prior) / prior * 100
        if pct_change > yoy_warning_pct:
            direction = "up" if source > prior else "down"
            notes_parts.append(
                f"Source docs {direction} {pct_change:.1f}% vs prior year"
            )

    notes = "; ".join(notes_parts) if notes_parts else "OK"
    return worst_level, notes


def _fmt(amount: Optional[Decimal]) -> str:
    """Format a decimal amount as a dollar string."""
    if amount is None:
        return "N/A"
    return f"${amount:,.2f}"


def compare_returns(
    prior_year: Optional[TaxReturn],
    source_expected: Optional[TaxReturn],
    draft: Optional[TaxReturn],
) -> ComparisonReport:
    """Perform three-way comparison of tax return data.

    Args:
        prior_year: Parsed prior year return (may be None)
        source_expected: Aggregated expected values from source documents (may be None)
        draft: Current draft return being reviewed

    Returns:
        ComparisonReport with all discrepancy findings
    """
    report = ComparisonReport()
    report.prior_year_file = prior_year.source_file if prior_year else ""
    report.source_doc_files = [source_expected.source_file] if source_expected else []
    report.draft_file = draft.source_file if draft else ""

    # Collect all unique line numbers across all three sources
    all_lines = set()
    for rule in DEFAULT_RULES:
        all_lines.add(rule.line)

    if prior_year:
        for item in prior_year.line_items:
            all_lines.add(item.line)
    if source_expected:
        for item in source_expected.line_items:
            all_lines.add(item.line)
    if draft:
        for item in draft.line_items:
            all_lines.add(item.line)

    # Sort lines for consistent ordering
    def line_sort_key(line: str) -> tuple:
        """Sort lines numerically, with letter suffixes after."""
        import re
        m = re.match(r"(\d+)([a-z]?)", line)
        if m:
            return (int(m.group(1)), m.group(2))
        return (999, line)

    for line in sorted(all_lines, key=line_sort_key):
        rule = get_rule_for_line(line)

        prior_amount = prior_year.get_amount(line) if prior_year else None
        source_amount = source_expected.get_amount(line) if source_expected else None
        draft_amount = draft.get_amount(line) if draft else None

        # Skip lines where all three are None
        if prior_amount is None and source_amount is None and draft_amount is None:
            continue

        status, notes = _compare_values(
            label=rule.label,
            prior=prior_amount,
            source=source_amount,
            draft=draft_amount,
            tolerance=rule.tolerance_dollars,
            yoy_warning_pct=rule.yoy_variance_warning_pct,
        )

        report.items.append(ReportItem(
            line=line,
            label=rule.label,
            prior_year_value=prior_amount,
            source_doc_value=source_amount,
            draft_value=draft_amount,
            status=status,
            notes=notes,
        ))

    # Generate summary
    counts = {level: 0 for level in DiscrepancyLevel}
    for item in report.items:
        counts[item.status] += 1

    parts = []
    if counts[DiscrepancyLevel.ERROR]:
        parts.append(f"{counts[DiscrepancyLevel.ERROR]} error(s)")
    if counts[DiscrepancyLevel.MISSING]:
        parts.append(f"{counts[DiscrepancyLevel.MISSING]} missing")
    if counts[DiscrepancyLevel.WARNING]:
        parts.append(f"{counts[DiscrepancyLevel.WARNING]} warning(s)")
    if counts[DiscrepancyLevel.MATCH]:
        parts.append(f"{counts[DiscrepancyLevel.MATCH]} match(es)")
    report.summary = ", ".join(parts) if parts else "No items to compare"

    return report
