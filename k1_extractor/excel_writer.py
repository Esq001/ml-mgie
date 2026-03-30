"""
Excel (.xlsx) output writer for K-1 extracted data.

Generates a formatted workbook with three sheets:
1. K-1 Data - Main data table with all extracted fields
2. Summary - Aggregated totals and form counts
3. Extraction Log - Per-file processing details
"""

import logging
from typing import List

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter

from .models import K1Data
from .constants import FORM_DEFINITIONS, ALL_BOX_IDS

logger = logging.getLogger(__name__)

# Styling constants
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center", wrap_text=True)
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)
CURRENCY_FORMAT = '#,##0.00;(#,##0.00);"-"'
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1F4E79")
SUBTITLE_FONT = Font(name="Calibri", size=11, italic=True, color="404040")
HIGH_CONFIDENCE_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
MEDIUM_CONFIDENCE_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
LOW_CONFIDENCE_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")


def write_excel(data: List[K1Data], output_path: str) -> None:
    """
    Write extracted K-1 data to a formatted Excel workbook.

    Args:
        data: List of K1Data objects (one per K-1 form processed).
        output_path: Path to the output .xlsx file.
    """
    wb = Workbook()

    _write_data_sheet(wb, data)
    _write_summary_sheet(wb, data)
    _write_log_sheet(wb, data)

    wb.save(output_path)
    logger.info("Excel file saved to: %s", output_path)


# =============================================================================
# Sheet 1: K-1 Data
# =============================================================================

def _write_data_sheet(wb: Workbook, data: List[K1Data]) -> None:
    """Write the main data sheet with all K-1 fields."""
    ws = wb.active
    ws.title = "K-1 Data"

    # Define columns: fixed columns + one column per box ID
    fixed_columns = [
        "Source File",
        "Form Type",
        "Entity Name",
        "Entity EIN",
        "Tax Year",
        "Recipient Name",
        "Recipient ID",
        "Recipient Type",
        "Confidence",
    ]

    # Build box columns with labels
    box_columns = []
    for box_id in ALL_BOX_IDS:
        # Get label from any form that has this box
        label = ""
        for form_def in FORM_DEFINITIONS.values():
            if box_id in form_def["boxes"]:
                label = form_def["boxes"][box_id]
                break
        box_columns.append((box_id, f"Box {box_id}: {label}"))

    all_headers = fixed_columns + [col[1] for col in box_columns]

    # Write header row
    for col_idx, header in enumerate(all_headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGNMENT
        cell.border = THIN_BORDER

    # Freeze header row
    ws.freeze_panes = "A2"

    # Write data rows
    for row_idx, k1 in enumerate(data, start=2):
        # Fixed columns
        fixed_values = [
            k1.source_file,
            k1.form_type,
            k1.entity_name,
            k1.entity_ein,
            k1.tax_year,
            k1.recipient_name,
            k1.recipient_id,
            k1.recipient_type,
            k1.confidence,
        ]

        for col_idx, value in enumerate(fixed_values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = THIN_BORDER

            # Color-code confidence
            if col_idx == len(fixed_values):  # Confidence column
                if value == "high":
                    cell.fill = HIGH_CONFIDENCE_FILL
                elif value == "medium":
                    cell.fill = MEDIUM_CONFIDENCE_FILL
                elif value == "low":
                    cell.fill = LOW_CONFIDENCE_FILL

        # Box value columns
        box_start_col = len(fixed_values) + 1
        for i, (box_id, _) in enumerate(box_columns):
            col_idx = box_start_col + i
            raw_value = k1.boxes.get(box_id, "")
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = THIN_BORDER

            if raw_value:
                try:
                    numeric = float(raw_value.replace(",", ""))
                    cell.value = numeric
                    cell.number_format = CURRENCY_FORMAT
                except (ValueError, TypeError):
                    cell.value = raw_value

    # Auto-fit column widths
    _auto_fit_columns(ws)

    # Add auto-filter
    if data:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(all_headers))}{len(data) + 1}"


# =============================================================================
# Sheet 2: Summary
# =============================================================================

def _write_summary_sheet(wb: Workbook, data: List[K1Data]) -> None:
    """Write a summary sheet with totals and counts."""
    ws = wb.create_sheet("Summary")

    # Title
    ws.cell(row=1, column=1, value="K-1 Extraction Summary").font = TITLE_FONT
    ws.merge_cells("A1:D1")

    row = 3

    # Form type counts
    ws.cell(row=row, column=1, value="Forms Processed").font = Font(bold=True, size=12)
    row += 1
    type_counts = {}
    for k1 in data:
        type_counts[k1.form_type] = type_counts.get(k1.form_type, 0) + 1

    for header in ["Form Type", "Count"]:
        col = 1 if header == "Form Type" else 2
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER

    row += 1
    for form_type, count in sorted(type_counts.items()):
        form_title = FORM_DEFINITIONS.get(form_type, {}).get("form_title", form_type)
        ws.cell(row=row, column=1, value=form_title).border = THIN_BORDER
        ws.cell(row=row, column=2, value=count).border = THIN_BORDER
        row += 1

    ws.cell(row=row, column=1, value="Total").font = Font(bold=True)
    ws.cell(row=row, column=1).border = THIN_BORDER
    ws.cell(row=row, column=2, value=len(data)).font = Font(bold=True)
    ws.cell(row=row, column=2).border = THIN_BORDER

    row += 2

    # Confidence breakdown
    ws.cell(row=row, column=1, value="Extraction Confidence").font = Font(bold=True, size=12)
    row += 1
    for header_text, col in [("Level", 1), ("Count", 2)]:
        cell = ws.cell(row=row, column=col, value=header_text)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER

    row += 1
    conf_counts = {"high": 0, "medium": 0, "low": 0}
    for k1 in data:
        conf_counts[k1.confidence] = conf_counts.get(k1.confidence, 0) + 1

    fills = {"high": HIGH_CONFIDENCE_FILL, "medium": MEDIUM_CONFIDENCE_FILL,
             "low": LOW_CONFIDENCE_FILL}
    for level in ["high", "medium", "low"]:
        cell = ws.cell(row=row, column=1, value=level.capitalize())
        cell.fill = fills[level]
        cell.border = THIN_BORDER
        ws.cell(row=row, column=2, value=conf_counts[level]).border = THIN_BORDER
        row += 1

    row += 2

    # Aggregate totals for key boxes
    ws.cell(row=row, column=1, value="Aggregate Box Totals").font = Font(bold=True, size=12)
    row += 1
    ws.cell(row=row, column=1, value="(Across all forms)").font = SUBTITLE_FONT
    row += 1

    for header_text, col in [("Box", 1), ("Description", 2), ("Total", 3), ("Count", 4)]:
        cell = ws.cell(row=row, column=col, value=header_text)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = THIN_BORDER

    row += 1
    for box_id in ALL_BOX_IDS:
        total = 0.0
        count = 0
        for k1 in data:
            val = k1.box_value_as_float(box_id)
            if val is not None:
                total += val
                count += 1

        if count == 0:
            continue

        label = ""
        for form_def in FORM_DEFINITIONS.values():
            if box_id in form_def["boxes"]:
                label = form_def["boxes"][box_id]
                break

        ws.cell(row=row, column=1, value=f"Box {box_id}").border = THIN_BORDER
        ws.cell(row=row, column=2, value=label).border = THIN_BORDER
        total_cell = ws.cell(row=row, column=3, value=total)
        total_cell.number_format = CURRENCY_FORMAT
        total_cell.border = THIN_BORDER
        ws.cell(row=row, column=4, value=count).border = THIN_BORDER
        row += 1

    _auto_fit_columns(ws)


# =============================================================================
# Sheet 3: Extraction Log
# =============================================================================

def _write_log_sheet(wb: Workbook, data: List[K1Data]) -> None:
    """Write the extraction log sheet with per-file details."""
    ws = wb.create_sheet("Extraction Log")

    headers = [
        "Source File",
        "Form Type",
        "Extraction Method",
        "Confidence",
        "Boxes Found",
        "Warnings",
    ]

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = HEADER_ALIGNMENT
        cell.border = THIN_BORDER

    ws.freeze_panes = "A2"

    for row_idx, k1 in enumerate(data, start=2):
        values = [
            k1.source_file,
            k1.form_type,
            k1.extraction_method,
            k1.confidence,
            len(k1.boxes),
            "; ".join(k1.warnings) if k1.warnings else "None",
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = THIN_BORDER

            if col_idx == 4:  # Confidence column
                if value == "high":
                    cell.fill = HIGH_CONFIDENCE_FILL
                elif value == "medium":
                    cell.fill = MEDIUM_CONFIDENCE_FILL
                elif value == "low":
                    cell.fill = LOW_CONFIDENCE_FILL

    _auto_fit_columns(ws)


# =============================================================================
# Utility
# =============================================================================

def _auto_fit_columns(ws, min_width: int = 10, max_width: int = 50) -> None:
    """Auto-fit column widths based on cell content."""
    for column_cells in ws.columns:
        max_length = 0
        col_letter = get_column_letter(column_cells[0].column)
        for cell in column_cells:
            if cell.value:
                cell_length = len(str(cell.value))
                if cell_length > max_length:
                    max_length = cell_length
        adjusted_width = min(max(max_length + 2, min_width), max_width)
        ws.column_dimensions[col_letter].width = adjusted_width
