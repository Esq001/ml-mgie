"""Export comparison reports to CSV and text formats."""

import csv
import io
from decimal import Decimal
from typing import Optional

from .report_model import ComparisonReport


def _fmt(amount: Optional[Decimal]) -> str:
    """Format an optional decimal as a dollar string."""
    if amount is None:
        return ""
    return f"${amount:,.2f}"


def export_csv(report: ComparisonReport) -> str:
    """Export the report as a CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Line", "Label", "Prior Year", "Source Docs",
        "Draft", "Status", "Notes"
    ])

    for item in report.items:
        writer.writerow([
            item.line,
            item.label,
            _fmt(item.prior_year_value),
            _fmt(item.source_doc_value),
            _fmt(item.draft_value),
            item.status.value,
            item.notes,
        ])

    return output.getvalue()


def export_text(report: ComparisonReport) -> str:
    """Export the report as formatted plain text."""
    lines = []
    lines.append("=" * 80)
    lines.append("TAX RETURN REVIEW REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Prior Year Return: {report.prior_year_file or 'Not provided'}")
    lines.append(f"Source Documents: {', '.join(report.source_doc_files) or 'Not provided'}")
    lines.append(f"Draft Return: {report.draft_file or 'Not provided'}")
    lines.append("")
    lines.append(f"Summary: {report.summary}")
    lines.append("-" * 80)
    lines.append("")

    # Header
    lines.append(
        f"{'Line':<8} {'Label':<30} {'Prior Year':>14} {'Source Docs':>14} "
        f"{'Draft':>14} {'Status':<10}"
    )
    lines.append("-" * 95)

    for item in report.items:
        status_marker = {
            "match": "  ",
            "warning": "! ",
            "error": "X ",
            "missing": "? ",
        }.get(item.status.value, "  ")

        lines.append(
            f"{status_marker}{item.line:<6} {item.label:<30} "
            f"{_fmt(item.prior_year_value):>14} {_fmt(item.source_doc_value):>14} "
            f"{_fmt(item.draft_value):>14} {item.status.value:<10}"
        )
        if item.notes and item.notes != "OK":
            lines.append(f"         >> {item.notes}")

    lines.append("")
    lines.append("=" * 80)
    lines.append(f"Legend: X = Error, ! = Warning, ? = Missing")
    lines.append("=" * 80)

    return "\n".join(lines)


def save_report(report: ComparisonReport, filepath: str) -> None:
    """Save report to file. Format auto-detected from extension."""
    if filepath.endswith(".csv"):
        content = export_csv(report)
    else:
        content = export_text(report)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
