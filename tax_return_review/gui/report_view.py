"""Report display widget using Treeview and Text."""

import tkinter as tk
from tkinter import ttk, filedialog
from decimal import Decimal
from typing import Optional

from . import styles
from ..models.enums import DiscrepancyLevel
from ..reports.report_model import ComparisonReport, ReportItem
from ..reports.report_export import export_csv, export_text, save_report


def _fmt(amount: Optional[Decimal]) -> str:
    if amount is None:
        return "-"
    return f"${amount:,.2f}"


class ReportView(ttk.Frame):
    """Widget for displaying comparison report results."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)
        self._report: Optional[ComparisonReport] = None
        self._build_ui()

    def _build_ui(self) -> None:
        # Summary bar
        summary_frame = ttk.Frame(self)
        summary_frame.pack(fill=tk.X, padx=styles.PAD_X, pady=styles.PAD_Y)

        self._summary_label = ttk.Label(
            summary_frame, text="No report generated yet.",
            font=styles.FONT_HEADING,
        )
        self._summary_label.pack(side=tk.LEFT)

        self._export_btn = ttk.Button(
            summary_frame, text="Export Report...",
            command=self._export_report, state=tk.DISABLED,
        )
        self._export_btn.pack(side=tk.RIGHT)

        # Notebook with two tabs
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill=tk.BOTH, expand=True, padx=styles.PAD_X, pady=styles.PAD_Y)

        # Tab 1: Treeview table
        tree_frame = ttk.Frame(self._notebook)
        self._notebook.add(tree_frame, text="  Comparison Table  ")

        columns = ("line", "label", "prior", "source", "draft", "status", "notes")
        self._tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            selectmode="browse",
        )

        # Column headers
        self._tree.heading("line", text="Line")
        self._tree.heading("label", text="Label")
        self._tree.heading("prior", text="Prior Year")
        self._tree.heading("source", text="Source Docs")
        self._tree.heading("draft", text="Draft")
        self._tree.heading("status", text="Status")
        self._tree.heading("notes", text="Notes")

        # Column widths
        self._tree.column("line", width=60, minwidth=50, anchor=tk.CENTER)
        self._tree.column("label", width=200, minwidth=150)
        self._tree.column("prior", width=110, minwidth=90, anchor=tk.E)
        self._tree.column("source", width=110, minwidth=90, anchor=tk.E)
        self._tree.column("draft", width=110, minwidth=90, anchor=tk.E)
        self._tree.column("status", width=80, minwidth=70, anchor=tk.CENTER)
        self._tree.column("notes", width=300, minwidth=150)

        # Row tags for coloring
        self._tree.tag_configure("match", background=styles.COLORS["match"])
        self._tree.tag_configure("warning", background=styles.COLORS["warning"])
        self._tree.tag_configure("error", background=styles.COLORS["error"])
        self._tree.tag_configure("missing", background=styles.COLORS["missing"])

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Tab 2: Detail text view
        text_frame = ttk.Frame(self._notebook)
        self._notebook.add(text_frame, text="  Detail View  ")

        self._text = tk.Text(
            text_frame, wrap=tk.WORD, font=styles.FONT_MONO,
            state=tk.DISABLED, padx=10, pady=10,
        )
        text_vsb = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self._text.yview)
        self._text.configure(yscrollcommand=text_vsb.set)

        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def display_report(self, report: ComparisonReport) -> None:
        """Populate the view with report data."""
        self._report = report

        # Update summary
        self._summary_label.configure(text=f"Results: {report.summary}")
        self._export_btn.configure(state=tk.NORMAL)

        # Clear and populate treeview
        for item_id in self._tree.get_children():
            self._tree.delete(item_id)

        for item in report.items:
            tag = item.status.value
            self._tree.insert("", tk.END, values=(
                item.line,
                item.label,
                _fmt(item.prior_year_value),
                _fmt(item.source_doc_value),
                _fmt(item.draft_value),
                item.status.value.upper(),
                item.notes,
            ), tags=(tag,))

        # Update detail text
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", export_text(report))
        self._text.configure(state=tk.DISABLED)

    def clear(self) -> None:
        """Clear the report display."""
        self._report = None
        self._summary_label.configure(text="No report generated yet.")
        self._export_btn.configure(state=tk.DISABLED)

        for item_id in self._tree.get_children():
            self._tree.delete(item_id)

        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.configure(state=tk.DISABLED)

    def _export_report(self) -> None:
        if not self._report:
            return

        filepath = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if filepath:
            save_report(self._report, filepath)
