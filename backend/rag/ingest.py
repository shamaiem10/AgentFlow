import pdfplumber
from pypdf import PdfReader
from docx import Document as DocxDocument
import openpyxl
import csv
import os

def parse_pdf(file_path):
    reader = PdfReader(file_path)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    return full_text

def parse_docx(file_path):
    doc = DocxDocument(file_path)
    full_text = ""
    for para in doc.paragraphs:
        if para.text.strip():
            full_text += para.text + "\n"

    # also pull text out of tables in the docx
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells)
            full_text += row_text + "\n"

    return full_text

def parse_xlsx(file_path):
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    full_text = ""
    for sheet in workbook.worksheets:
        full_text += f"\n--- Sheet: {sheet.title} ---\n"
        for row in sheet.iter_rows(values_only=True):
            row_values = [str(cell) for cell in row if cell is not None]
            if row_values:
                full_text += " | ".join(row_values) + "\n"
    return full_text

def parse_csv(file_path):
    full_text = ""
    with open(file_path, newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for row in reader:
            full_text += " | ".join(row) + "\n"
    return full_text

def parse_document(file_path):
    """
    Detects file type by extension and routes to the correct parser.
    This is the single entry point everything else should call.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".docx":
        return parse_docx(file_path)
    elif ext in [".xlsx", ".xls"]:
        return parse_xlsx(file_path)
    elif ext == ".csv":
        return parse_csv(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")