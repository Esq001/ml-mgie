"""Reusable file upload panel widget."""

import os
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Callable, Optional

from . import styles


class UploadPanel(ttk.LabelFrame):
    """A panel for uploading one or more tax documents."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        multi_file: bool = False,
        on_change: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, text=f"  {title}  ", **kwargs)
        self._multi_file = multi_file
        self._on_change = on_change
        self._files: list[str] = []

        self._build_ui()

    def _build_ui(self) -> None:
        # Top row: buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=styles.PAD_X, pady=(styles.PAD_Y, 0))

        self._browse_btn = ttk.Button(
            btn_frame, text="Browse...", command=self._browse
        )
        self._browse_btn.pack(side=tk.LEFT, padx=(0, 4))

        self._remove_btn = ttk.Button(
            btn_frame, text="Remove", command=self._remove_selected, state=tk.DISABLED
        )
        self._remove_btn.pack(side=tk.LEFT, padx=(0, 4))

        self._clear_btn = ttk.Button(
            btn_frame, text="Clear All", command=self._clear_all, state=tk.DISABLED
        )
        self._clear_btn.pack(side=tk.LEFT)

        # File count label
        self._count_label = ttk.Label(
            btn_frame, text="No files selected", font=styles.FONT_SMALL
        )
        self._count_label.pack(side=tk.RIGHT)

        # File listbox with scrollbar
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=styles.PAD_X, pady=styles.PAD_Y)

        self._listbox = tk.Listbox(
            list_frame, height=3, font=styles.FONT_SMALL,
            selectmode=tk.EXTENDED, activestyle="none"
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=scrollbar.set)

        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._listbox.bind("<<ListboxSelect>>", self._on_select)

    def _browse(self) -> None:
        filetypes = styles.FILE_FILTERS
        if self._multi_file:
            paths = filedialog.askopenfilenames(
                title="Select files",
                filetypes=filetypes,
            )
            if paths:
                for path in paths:
                    if path not in self._files:
                        self._files.append(path)
        else:
            path = filedialog.askopenfilename(
                title="Select file",
                filetypes=filetypes,
            )
            if path:
                self._files = [path]

        self._refresh_display()

    def _remove_selected(self) -> None:
        selected = list(self._listbox.curselection())
        for idx in reversed(selected):
            if idx < len(self._files):
                self._files.pop(idx)
        self._refresh_display()

    def _clear_all(self) -> None:
        self._files.clear()
        self._refresh_display()

    def _on_select(self, _event: tk.Event) -> None:
        has_selection = bool(self._listbox.curselection())
        self._remove_btn.configure(state=tk.NORMAL if has_selection else tk.DISABLED)

    def _refresh_display(self) -> None:
        self._listbox.delete(0, tk.END)
        for filepath in self._files:
            display_name = os.path.basename(filepath)
            self._listbox.insert(tk.END, display_name)

        count = len(self._files)
        if count == 0:
            self._count_label.configure(text="No files selected")
        elif count == 1:
            self._count_label.configure(text="1 file selected")
        else:
            self._count_label.configure(text=f"{count} files selected")

        self._clear_btn.configure(state=tk.NORMAL if count > 0 else tk.DISABLED)
        self._remove_btn.configure(state=tk.DISABLED)

        if self._on_change:
            self._on_change()

    @property
    def files(self) -> list[str]:
        """Return the list of selected file paths."""
        return list(self._files)

    @property
    def has_files(self) -> bool:
        """Return True if at least one file is selected."""
        return len(self._files) > 0
