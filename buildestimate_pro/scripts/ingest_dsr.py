"""DSR ingestion pipeline skeleton.

This script extracts text/tables from a provided PDF and writes structured JSON records.
It provides a clean abstraction for later semantic embedding and vector store insertion.
"""
import sys
import json
from pathlib import Path
try:
    import pdfplumber
    _PDFPLUMBER_AVAILABLE = True
except Exception:
    pdfplumber = None
    _PDFPLUMBER_AVAILABLE = False

import fitz  # PyMuPDF


def extract_text_pdfplumber(path: Path) -> str:
    if not _PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber is not available")
    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                texts.append("")
    return "\n\n".join(texts)


def extract_text_pymupdf(path: Path) -> str:
    doc = fitz.open(path)
    texts = []
    for page in doc:
        texts.append(page.get_text())
    return "\n\n".join(texts)


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200):
    tokens = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        tokens.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
    return tokens


def ingest(pdf_path: str, out_json: str = None):
    p = Path(pdf_path)
    if not p.exists():
        print("PDF not found:", pdf_path)
        return

    text = None
    if _PDFPLUMBER_AVAILABLE:
        print("Extracting with pdfplumber...")
        try:
            text = extract_text_pdfplumber(p)
        except Exception:
            print("pdfplumber failed, falling back to PyMuPDF")

    if text is None:
        text = extract_text_pymupdf(p)

    print("Chunking text...")
    chunks = chunk_text(text)

    records = []
    for i, c in enumerate(chunks, start=1):
        records.append({"id": i, "text": c, "source": str(p.name)})

    out_path = out_json or (p.with_suffix('.chunks.json'))
    with open(out_path, 'w', encoding='utf8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(records)} chunks to {out_path}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python ingest_dsr.py <path-to-dsr-pdf>")
        sys.exit(1)
    ingest(sys.argv[1])
