"""
Tkinter-based GUI for the K-1 PDF to Excel Extractor.

Provides file/folder selection, progress tracking, and log output.
Processing runs in a background thread to keep the GUI responsive.
"""

import os
import threading
import logging
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, Listbox, Scrollbar, Text,
    filedialog, messagebox, StringVar, END, BOTH, LEFT, RIGHT,
    TOP, BOTTOM, X, Y, W, E, N, S, HORIZONTAL, VERTICAL, DISABLED, NORMAL,
)
from tkinter import ttk

from .ocr_engine import extract_text, check_tesseract_available, get_tesseract_path_hint
from .k1_parser import parse_k1
from .excel_writer import write_excel
from .models import K1Data

logger = logging.getLogger(__name__)


class K1ExtractorApp:
    """Main application window for K-1 PDF to Excel extraction."""

    def __init__(self):
        self.root = Tk()
        self.root.title("K-1 PDF to Excel Extractor")
        self.root.geometry("750x700")
        self.root.minsize(600, 550)

        self.pdf_files: list[str] = []
        self.results: list[K1Data] = []
        self._processing = False

        self._build_ui()
        self._check_tesseract()

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()

    # =========================================================================
    # UI Construction
    # =========================================================================

    def _build_ui(self):
        """Build the complete GUI layout."""
        # Main container with padding
        main = Frame(self.root, padx=15, pady=10)
        main.pack(fill=BOTH, expand=True)

        # Title
        title = Label(
            main, text="K-1 PDF to Excel Extractor",
            font=("Segoe UI", 16, "bold"), anchor=W,
        )
        title.pack(fill=X, pady=(0, 10))

        # --- Input Section ---
        input_frame = ttk.LabelFrame(main, text="Input PDF Files", padding=10)
        input_frame.pack(fill=BOTH, expand=False, pady=(0, 8))

        btn_row = Frame(input_frame)
        btn_row.pack(fill=X)

        ttk.Button(btn_row, text="Select Files...", command=self._select_files).pack(side=LEFT, padx=(0, 5))
        ttk.Button(btn_row, text="Select Folder...", command=self._select_folder).pack(side=LEFT, padx=(0, 5))
        ttk.Button(btn_row, text="Clear", command=self._clear_files).pack(side=LEFT)

        # File listbox with scrollbar
        list_frame = Frame(input_frame)
        list_frame.pack(fill=BOTH, expand=True, pady=(5, 0))

        scrollbar = Scrollbar(list_frame, orient=VERTICAL)
        self.file_listbox = Listbox(
            list_frame, height=5, yscrollcommand=scrollbar.set,
            selectmode="extended", font=("Consolas", 9),
        )
        scrollbar.config(command=self.file_listbox.yview)
        self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.file_count_var = StringVar(value="No files selected")
        Label(input_frame, textvariable=self.file_count_var, font=("Segoe UI", 9)).pack(anchor=W)

        # --- Output Section ---
        output_frame = ttk.LabelFrame(main, text="Output Excel File", padding=10)
        output_frame.pack(fill=X, pady=(0, 8))

        output_row = Frame(output_frame)
        output_row.pack(fill=X)

        self.output_var = StringVar()
        ttk.Entry(output_row, textvariable=self.output_var, font=("Consolas", 9)).pack(
            side=LEFT, fill=X, expand=True, padx=(0, 5)
        )
        ttk.Button(output_row, text="Browse...", command=self._select_output).pack(side=LEFT)

        # --- Tesseract Status ---
        self.tesseract_var = StringVar(value="Checking Tesseract OCR...")
        self.tesseract_label = Label(
            main, textvariable=self.tesseract_var,
            font=("Segoe UI", 9), anchor=W,
        )
        self.tesseract_label.pack(fill=X, pady=(0, 8))

        # --- Progress Section ---
        progress_frame = Frame(main)
        progress_frame.pack(fill=X, pady=(0, 8))

        self.progress_var = StringVar(value="Ready")
        Label(progress_frame, textvariable=self.progress_var, font=("Segoe UI", 9)).pack(anchor=W)

        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill=X, pady=(3, 0))

        # --- Action Buttons ---
        action_frame = Frame(main)
        action_frame.pack(fill=X, pady=(0, 8))

        self.extract_btn = ttk.Button(
            action_frame, text="Extract to Excel",
            command=self._start_extraction,
        )
        self.extract_btn.pack(side=LEFT, padx=(0, 10))

        ttk.Button(action_frame, text="Exit", command=self.root.quit).pack(side=RIGHT)

        # --- Log Section ---
        log_frame = ttk.LabelFrame(main, text="Processing Log", padding=5)
        log_frame.pack(fill=BOTH, expand=True)

        log_scroll = Scrollbar(log_frame, orient=VERTICAL)
        self.log_text = Text(
            log_frame, height=8, font=("Consolas", 9),
            yscrollcommand=log_scroll.set, state=DISABLED, wrap="word",
        )
        log_scroll.config(command=self.log_text.yview)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        log_scroll.pack(side=RIGHT, fill=Y)

    # =========================================================================
    # File Selection
    # =========================================================================

    def _select_files(self):
        """Open file dialog to select individual PDF files."""
        files = filedialog.askopenfilenames(
            title="Select K-1 PDF Files",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )
        if files:
            for f in files:
                if f not in self.pdf_files:
                    self.pdf_files.append(f)
            self._refresh_file_list()

    def _select_folder(self):
        """Open folder dialog and add all PDFs in the selected folder."""
        folder = filedialog.askdirectory(title="Select Folder Containing K-1 PDFs")
        if folder:
            for f in sorted(Path(folder).glob("*.pdf")):
                path = str(f)
                if path not in self.pdf_files:
                    self.pdf_files.append(path)
            self._refresh_file_list()

    def _clear_files(self):
        """Clear all selected files."""
        self.pdf_files.clear()
        self._refresh_file_list()

    def _refresh_file_list(self):
        """Update the file listbox and count label."""
        self.file_listbox.delete(0, END)
        for f in self.pdf_files:
            self.file_listbox.insert(END, os.path.basename(f))
        count = len(self.pdf_files)
        self.file_count_var.set(
            f"{count} file{'s' if count != 1 else ''} selected"
            if count > 0 else "No files selected"
        )

    def _select_output(self):
        """Open save dialog to choose output Excel path."""
        path = filedialog.asksaveasfilename(
            title="Save Excel Output As",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
        )
        if path:
            self.output_var.set(path)

    # =========================================================================
    # Tesseract Check
    # =========================================================================

    def _check_tesseract(self):
        """Check Tesseract availability and update status label."""
        if check_tesseract_available():
            self.tesseract_var.set("Tesseract OCR: Available (scanned PDFs supported)")
            self.tesseract_label.config(fg="green")
        else:
            self.tesseract_var.set(
                "Tesseract OCR: Not detected (only digital PDFs will be processed)"
            )
            self.tesseract_label.config(fg="orange")

    # =========================================================================
    # Extraction
    # =========================================================================

    def _start_extraction(self):
        """Validate inputs and start extraction in a background thread."""
        if self._processing:
            return

        if not self.pdf_files:
            messagebox.showwarning("No Files", "Please select at least one PDF file.")
            return

        output_path = self.output_var.get().strip()
        if not output_path:
            messagebox.showwarning("No Output", "Please specify an output Excel file path.")
            return

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                messagebox.showerror("Error", f"Cannot create output directory: {e}")
                return

        self._processing = True
        self.extract_btn.config(state=DISABLED)
        self.results.clear()
        self._clear_log()
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = len(self.pdf_files)

        thread = threading.Thread(
            target=self._extraction_worker,
            args=(list(self.pdf_files), output_path),
            daemon=True,
        )
        thread.start()

    def _extraction_worker(self, files: list[str], output_path: str):
        """Background worker that processes all PDFs and writes Excel."""
        results = []
        total = len(files)

        for i, pdf_path in enumerate(files):
            filename = os.path.basename(pdf_path)
            self._update_progress(i, total, f"Processing: {filename} ({i + 1}/{total})")

            try:
                text, method = extract_text(pdf_path)
                k1_data = parse_k1(text, source_file=filename, extraction_method=method)
                results.append(k1_data)

                method_str = "native text" if method == "native" else "OCR"
                confidence_icon = {
                    "high": "[OK]", "medium": "[WARN]", "low": "[LOW]"
                }.get(k1_data.confidence, "?")

                self._log(
                    f"{confidence_icon} {filename} - "
                    f"Form {k1_data.form_type} detected via {method_str}, "
                    f"confidence: {k1_data.confidence}, "
                    f"{len(k1_data.boxes)} boxes extracted"
                )

                if k1_data.warnings:
                    for warning in k1_data.warnings:
                        self._log(f"  Warning: {warning}")

            except Exception as e:
                self._log(f"[ERROR] {filename} - {e}")
                logger.exception("Failed to process %s", pdf_path)

        # Write Excel output
        if results:
            self._update_progress(total, total, "Writing Excel file...")
            try:
                write_excel(results, output_path)
                self._log(f"\nExcel file saved: {output_path}")
                self._log(f"Total forms processed: {len(results)}/{total}")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Complete",
                    f"Successfully processed {len(results)} of {total} files.\n"
                    f"Output saved to:\n{output_path}"
                ))
            except Exception as e:
                self._log(f"[ERROR] Failed to write Excel: {e}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Failed to write Excel file: {e}"
                ))
        else:
            self._log("\nNo forms were successfully extracted.")
            self.root.after(0, lambda: messagebox.showwarning(
                "No Results", "No K-1 data could be extracted from the selected files."
            ))

        self._update_progress(total, total, "Done")
        self.root.after(0, lambda: self.extract_btn.config(state=NORMAL))
        self._processing = False

    # =========================================================================
    # UI Updates (thread-safe)
    # =========================================================================

    def _update_progress(self, current: int, total: int, message: str):
        """Update progress bar and status label from any thread."""
        self.root.after(0, lambda: self._set_progress(current, total, message))

    def _set_progress(self, current: int, total: int, message: str):
        self.progress_bar["value"] = current
        self.progress_bar["maximum"] = total
        self.progress_var.set(message)

    def _log(self, message: str):
        """Append a message to the log area from any thread."""
        self.root.after(0, lambda: self._append_log(message))

    def _append_log(self, message: str):
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)

    def _clear_log(self):
        self.log_text.config(state=NORMAL)
        self.log_text.delete("1.0", END)
        self.log_text.config(state=DISABLED)
