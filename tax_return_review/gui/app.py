"""Main application window for Tax Return Review Tool."""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from . import styles
from .upload_panel import UploadPanel
from .report_view import ReportView
from ..models.tax_data import (
    Form1099Data, ParsedDocuments, TaxReturn, W2Data,
)
from ..parsers.pdf_parser import parse_file
from ..engine.aggregator import aggregate_source_documents
from ..engine.comparator import compare_returns


class TaxReviewApp:
    """Main application class for the Tax Return Review Tool."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self._configure_window()
        self._configure_styles()
        self._build_ui()

    def _configure_window(self) -> None:
        self.root.title(styles.WINDOW_TITLE)
        self.root.geometry(styles.WINDOW_DEFAULT_GEOMETRY)
        self.root.minsize(styles.WINDOW_MIN_WIDTH, styles.WINDOW_MIN_HEIGHT)

        # Try to set icon (Windows)
        try:
            self.root.iconbitmap(default="")
        except tk.TclError:
            pass

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("vista")  # Windows native look
        except tk.TclError:
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

        style.configure("TLabelframe", font=styles.FONT_HEADING)
        style.configure("TLabelframe.Label", font=styles.FONT_HEADING)
        style.configure("TButton", font=styles.FONT_NORMAL, padding=4)
        style.configure("Accent.TButton", font=styles.FONT_HEADING, padding=8)
        style.configure("Treeview", font=styles.FONT_TREE, rowheight=24)
        style.configure("Treeview.Heading", font=(styles.FONT_FAMILY, 9, "bold"))

    def _build_ui(self) -> None:
        # Main container
        main_frame = ttk.Frame(self.root, padding=styles.PAD_FRAME)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame, text="Tax Return Review Tool",
            font=(styles.FONT_FAMILY, 16, "bold"),
        )
        title_label.pack(pady=(0, 8))

        subtitle = ttk.Label(
            main_frame,
            text="Compare prior year return, current year source documents, and draft return",
            font=styles.FONT_SMALL,
        )
        subtitle.pack(pady=(0, 12))

        # Upload panels container
        upload_frame = ttk.Frame(main_frame)
        upload_frame.pack(fill=tk.X, pady=(0, 8))
        upload_frame.columnconfigure(0, weight=1)
        upload_frame.columnconfigure(1, weight=1)
        upload_frame.columnconfigure(2, weight=1)

        self._prior_panel = UploadPanel(
            upload_frame, "Prior Year Return",
            multi_file=False, on_change=self._update_run_button,
        )
        self._prior_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self._source_panel = UploadPanel(
            upload_frame, "Source Documents (W-2, 1099, etc.)",
            multi_file=True, on_change=self._update_run_button,
        )
        self._source_panel.grid(row=0, column=1, sticky="nsew", padx=4)

        self._draft_panel = UploadPanel(
            upload_frame, "Draft Tax Return",
            multi_file=False, on_change=self._update_run_button,
        )
        self._draft_panel.grid(row=0, column=2, sticky="nsew", padx=(4, 0))

        # Run button and status
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 8))

        self._run_btn = ttk.Button(
            action_frame, text="  Run Comparison  ",
            command=self._run_comparison,
            style="Accent.TButton",
            state=tk.DISABLED,
        )
        self._run_btn.pack(side=tk.LEFT)

        self._status_label = ttk.Label(
            action_frame, text="Upload documents to begin.",
            font=styles.FONT_SMALL,
        )
        self._status_label.pack(side=tk.LEFT, padx=12)

        self._progress = ttk.Progressbar(
            action_frame, mode="indeterminate", length=150,
        )
        self._progress.pack(side=tk.RIGHT)

        # Report view
        self._report_view = ReportView(main_frame)
        self._report_view.pack(fill=tk.BOTH, expand=True)

    def _update_run_button(self) -> None:
        """Enable Run button when at least a draft is provided."""
        has_draft = self._draft_panel.has_files
        has_any_comparison = self._prior_panel.has_files or self._source_panel.has_files

        if has_draft and has_any_comparison:
            self._run_btn.configure(state=tk.NORMAL)
            self._status_label.configure(text="Ready to run comparison.")
        elif has_draft:
            self._run_btn.configure(state=tk.NORMAL)
            self._status_label.configure(
                text="Tip: Add prior year return or source docs for comparison."
            )
        else:
            self._run_btn.configure(state=tk.DISABLED)
            self._status_label.configure(text="Upload at least a draft return.")

    def _run_comparison(self) -> None:
        """Start the comparison process in a background thread."""
        self._run_btn.configure(state=tk.DISABLED)
        self._progress.start(10)
        self._status_label.configure(text="Parsing documents...")
        self._report_view.clear()

        thread = threading.Thread(target=self._do_comparison, daemon=True)
        thread.start()

    def _do_comparison(self) -> None:
        """Perform parsing and comparison (runs in background thread)."""
        try:
            # Parse prior year return
            prior_year = None
            if self._prior_panel.has_files:
                filepath = self._prior_panel.files[0]
                self._set_status(f"Parsing prior year: {os.path.basename(filepath)}...")
                result = parse_file(filepath)
                if isinstance(result, TaxReturn):
                    prior_year = result

            # Parse source documents
            source_docs = ParsedDocuments()
            for filepath in self._source_panel.files:
                self._set_status(f"Parsing: {os.path.basename(filepath)}...")
                result = parse_file(filepath)
                source_docs.source_files.append(filepath)
                if isinstance(result, W2Data):
                    source_docs.w2s.append(result)
                elif isinstance(result, Form1099Data):
                    source_docs.form_1099s.append(result)
                elif isinstance(result, TaxReturn):
                    # If a 1040 is uploaded as a source doc, treat its line items
                    # as reference data
                    for item in result.line_items:
                        source_docs.source_files.append(result.source_file)

            # Aggregate source documents
            source_expected = None
            if source_docs.w2s or source_docs.form_1099s:
                self._set_status("Aggregating source documents...")
                source_expected = aggregate_source_documents(source_docs)

            # Parse draft return
            draft = None
            if self._draft_panel.has_files:
                filepath = self._draft_panel.files[0]
                self._set_status(f"Parsing draft: {os.path.basename(filepath)}...")
                result = parse_file(filepath)
                if isinstance(result, TaxReturn):
                    draft = result

            # Run comparison
            self._set_status("Running comparison...")
            report = compare_returns(prior_year, source_expected, draft)

            # Display results on main thread
            self.root.after(0, self._show_results, report)

        except Exception as e:
            self.root.after(0, self._show_error, str(e))

    def _set_status(self, text: str) -> None:
        """Update the status label (thread-safe)."""
        self.root.after(0, self._status_label.configure, {"text": text})

    def _show_results(self, report) -> None:
        """Display comparison results (called on main thread)."""
        self._progress.stop()
        self._run_btn.configure(state=tk.NORMAL)
        self._status_label.configure(text=f"Complete: {report.summary}")
        self._report_view.display_report(report)

    def _show_error(self, message: str) -> None:
        """Show an error message (called on main thread)."""
        self._progress.stop()
        self._run_btn.configure(state=tk.NORMAL)
        self._status_label.configure(text="Error occurred.")
        messagebox.showerror("Error", f"An error occurred during processing:\n\n{message}")
