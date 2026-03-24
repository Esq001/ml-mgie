"""Parser for structured CSV/JSON tax data imports."""

import csv
import io
import json
from decimal import Decimal, InvalidOperation
from typing import Union

from ..models.tax_data import LineItem, TaxReturn


def parse_csv(content: str, source_file: str) -> TaxReturn:
    """Parse CSV content with columns: form, line, label, amount.

    Optionally includes tax_year and filing_status columns.
    """
    tax_return = TaxReturn(source_file=source_file, raw_text=content)
    reader = csv.DictReader(io.StringIO(content))

    for row in reader:
        form = row.get("form", "1040").strip()
        line = row.get("line", "").strip()
        label = row.get("label", "").strip()
        amount_str = row.get("amount", "0").strip().replace("$", "").replace(",", "")

        if not line:
            continue

        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            continue

        tax_return.line_items.append(LineItem(
            form=form,
            line=line,
            label=label,
            amount=amount,
            source_file=source_file,
        ))

        # Pick up metadata if present
        if "tax_year" in row and row["tax_year"].strip():
            try:
                tax_return.tax_year = int(row["tax_year"].strip())
            except ValueError:
                pass
        if "filing_status" in row and row["filing_status"].strip():
            tax_return.filing_status = row["filing_status"].strip()

    return tax_return


def parse_json(content: str, source_file: str) -> TaxReturn:
    """Parse JSON content: list of {form, line, label, amount} objects.

    Top-level object may also include tax_year and filing_status.
    """
    data = json.loads(content)
    tax_return = TaxReturn(source_file=source_file, raw_text=content)

    if isinstance(data, dict):
        tax_return.tax_year = data.get("tax_year")
        tax_return.filing_status = data.get("filing_status", "")
        items = data.get("line_items", data.get("items", []))
    elif isinstance(data, list):
        items = data
    else:
        return tax_return

    for item in items:
        if not isinstance(item, dict):
            continue
        form = str(item.get("form", "1040"))
        line = str(item.get("line", ""))
        label = str(item.get("label", ""))
        amount_str = str(item.get("amount", "0")).replace("$", "").replace(",", "")

        if not line:
            continue

        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            continue

        tax_return.line_items.append(LineItem(
            form=form,
            line=line,
            label=label,
            amount=amount,
            source_file=source_file,
        ))

    return tax_return


def parse_structured_file(filepath: str) -> TaxReturn:
    """Auto-detect and parse a CSV or JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    content_stripped = content.strip()
    if content_stripped.startswith(("{", "[")):
        return parse_json(content, filepath)
    else:
        return parse_csv(content, filepath)
