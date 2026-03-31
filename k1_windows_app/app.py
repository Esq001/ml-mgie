from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List

import tkinter as tk
from tkinter import filedialog, messagebox

import pandas as pd
import pytesseract
from pdf2image import convert_from_path


@dataclass
class K1Record:
    source_file: str
    tax_year: str = ""
    partnership_name: str = ""
    partnership_ein: str = ""
    partner_name: str = ""
    partner_ssn: str = ""
    ordinary_business_income_loss: str = ""
    net_rental_real_estate_income_loss: str = ""
    other_net_rental_income_loss: str = ""
    guaranteed_payments: str = ""
    interest_income: str = ""
    ordinary_dividends: str = ""
    royalties: str = ""
    net_short_term_capital_gain_loss: str = ""
    net_long_term_capital_gain_loss: str = ""


FIELD_PATTERNS = {
    "tax_year": [r"Schedule\s*K-1\s*\(Form\s*1065\).*?(20\d{2})", r"For\s+calendar\s+year\s+(20\d{2})"],
    "partnership_name": [
        r"Part\s*I.*?Information\s+About\s+the\s+Partnership.*?A\s+(.+?)\s+B\s+",
        r"A\s+Partnership'?s\s+name,\s+address,\s+city,\s+state,\s+and\s+ZIP\s+code\s+(.+?)\s+B\s+",
    ],
    "partnership_ein": [r"B\s+Partnership'?s\s+EIN\s+([\d\-Xx]+)", r"Partnership'?s\s+EIN\s+([\d\-Xx]+)"],
    "partner_name": [r"Part\s*II.*?Information\s+About\s+the\s+Partner.*?E\s+(.+?)\s+F\s+"],
    "partner_ssn": [r"F\s+Partner'?s\s+SSN\s+or\s+TIN\s+([\d\-Xx]+)", r"Partner'?s\s+SSN\s+or\s+TIN\s+([\d\-Xx]+)"],
    "ordinary_business_income_loss": [r"1\s+Ordinary\s+business\s+income\s+\(loss\)\s+([\-\(\)\d\.,]+)"],
    "net_rental_real_estate_income_loss": [r"2\s+Net\s+rental\s+real\s+estate\s+income\s+\(loss\)\s+([\-\(\)\d\.,]+)"],
    "other_net_rental_income_loss": [r"3\s+Other\s+net\s+rental\s+income\s+\(loss\)\s+([\-\(\)\d\.,]+)"],
    "guaranteed_payments": [r"4\s+Guaranteed\s+payments\s+([\-\(\)\d\.,]+)"],
    "interest_income": [r"5\s+Interest\s+income\s+([\-\(\)\d\.,]+)"],
    "ordinary_dividends": [r"6a?\s+Ordinary\s+dividends\s+([\-\(\)\d\.,]+)"],
    "royalties": [r"7\s+Royalties\s+([\-\(\)\d\.,]+)"],
    "net_short_term_capital_gain_loss": [r"8\s+Net\s+short-term\s+capital\s+gain\s+\(loss\)\s+([\-\(\)\d\.,]+)"],
    "net_long_term_capital_gain_loss": [r"9a?\s+Net\s+long-term\s+capital\s+gain\s+\(loss\)\s+([\-\(\)\d\.,]+)"],
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_k1_text(text: str, source_file: str) -> K1Record:
    normalized = normalize_text(text)
    record = K1Record(source_file=source_file)

    for field_name, patterns in FIELD_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if match:
                value = match.group(1).strip(" :")
                setattr(record, field_name, value)
                break

    return record


def extract_text_from_pdf(pdf_path: Path, dpi: int = 300) -> str:
    pages = convert_from_path(str(pdf_path), dpi=dpi)
    page_text: List[str] = []

    for page in pages:
        text = pytesseract.image_to_string(page)
        page_text.append(text)

    return "\n".join(page_text)


def extract_records(pdf_paths: Iterable[Path]) -> list[K1Record]:
    records: list[K1Record] = []
    for pdf_path in pdf_paths:
        text = extract_text_from_pdf(pdf_path)
        records.append(parse_k1_text(text, source_file=pdf_path.name))
    return records


def export_to_xlsx(records: list[K1Record], output_path: Path) -> None:
    rows = [asdict(record) for record in records]
    df = pd.DataFrame(rows)
    df.to_excel(output_path, index=False)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Schedule K-1 PDF to Excel")
        self.geometry("720x260")
        self.pdf_paths: list[Path] = []

        self._build_ui()

    def _build_ui(self) -> None:
        title = tk.Label(self, text="Schedule K-1 OCR Extractor", font=("Segoe UI", 14, "bold"))
        title.pack(pady=(16, 4))

        desc = tk.Label(
            self,
            text="Select scanned K-1 PDFs, then export extracted fields to an .xlsx file.",
            font=("Segoe UI", 10),
        )
        desc.pack()

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=14)

        tk.Button(btn_frame, text="Select PDFs", command=self.select_pdfs, width=18).grid(row=0, column=0, padx=8)
        tk.Button(btn_frame, text="Export to Excel", command=self.process_files, width=18).grid(row=0, column=1, padx=8)

        self.status = tk.Label(self, text="No files selected.", justify="left", anchor="w")
        self.status.pack(fill="x", padx=16, pady=12)

    def select_pdfs(self) -> None:
        files = filedialog.askopenfilenames(
            title="Choose scanned Schedule K-1 PDFs",
            filetypes=[("PDF files", "*.pdf")],
        )
        self.pdf_paths = [Path(p) for p in files]
        if self.pdf_paths:
            self.status.configure(text=f"Selected {len(self.pdf_paths)} file(s):\n" + "\n".join(p.name for p in self.pdf_paths[:6]))
        else:
            self.status.configure(text="No files selected.")

    def process_files(self) -> None:
        if not self.pdf_paths:
            messagebox.showwarning("No PDFs selected", "Please select at least one PDF first.")
            return

        output_file = filedialog.asksaveasfilename(
            title="Save output spreadsheet",
            defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx")],
            initialfile="k1_extracted_data.xlsx",
        )

        if not output_file:
            return

        try:
            self.status.configure(text="Processing PDFs... this can take a minute for scanned files.")
            self.update_idletasks()

            records = extract_records(self.pdf_paths)
            export_to_xlsx(records, Path(output_file))

            self.status.configure(text=f"Done. Exported {len(records)} record(s) to:\n{output_file}")
            messagebox.showinfo("Success", f"Exported {len(records)} record(s) to:\n{output_file}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", f"Failed to process files:\n{exc}")
            self.status.configure(text="Failed to process files. Check poppler/tesseract setup and PDF quality.")


if __name__ == "__main__":
    app = App()
    app.mainloop()
