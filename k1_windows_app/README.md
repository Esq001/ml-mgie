# Windows Schedule K-1 PDF to Excel App

This is a lightweight Windows desktop app (Tkinter) that:

1. Loads one or more scanned **Schedule K-1 (Form 1065)** PDFs.
2. Uses OCR to read text from each page.
3. Extracts common K-1 fields (name, EIN/TIN, line-item amounts).
4. Exports all records to a single `.xlsx` file.

## 1) Install prerequisites on Windows

1. Install Python 3.10+.
2. Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).
3. Install [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases).
4. Add both binaries to your PATH:
   - `...\Tesseract-OCR\`
   - `...\poppler-xx\Library\bin\`

## 2) Install Python packages

```powershell
cd k1_windows_app
python -m pip install -r requirements.txt
```

## 3) Run the app

```powershell
python app.py
```

## Notes

- OCR quality depends on scan quality and orientation.
- The regex parser is intentionally easy to edit in `FIELD_PATTERNS` for your specific K-1 variants.
- If Tesseract is not in PATH, you can set it in code:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```
