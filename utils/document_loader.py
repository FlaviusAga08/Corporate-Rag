import os
import re
from collections import Counter
from typing import List

import fitz  # pymupdf
from docx import Document

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def _chunk(text: str) -> List[str]:
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= CHUNK_SIZE:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            if len(para) > CHUNK_SIZE:
                start = 0
                while start < len(para):
                    chunks.append(para[start:start + CHUNK_SIZE].strip())
                    start += CHUNK_SIZE - CHUNK_OVERLAP
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) > 30]


def _strip_pdf_noise(pages_lines: List[List[str]], n_pages: int) -> List[str]:
    # Lines appearing on more than 40% of pages are headers/footers — remove them
    counts = Counter(
        line.strip()
        for lines in pages_lines
        for line in lines
        if line.strip()
    )
    noise = {
        line for line, count in counts.items()
        if count >= max(2, n_pages * 0.4) and len(line) < 120
    }
    cleaned = []
    for lines in pages_lines:
        page_text = "\n".join(l for l in lines if l.strip() not in noise)
        cleaned.append(page_text)
    return cleaned


def load_pdf(file_path: str) -> List[str]:
    doc = fitz.open(file_path)
    pages_lines = [page.get_text().split("\n") for page in doc]
    cleaned_pages = _strip_pdf_noise(pages_lines, len(doc))
    text = "\n\n".join(cleaned_pages)
    return _chunk(text)


def load_docx(file_path: str) -> List[str]:
    doc = Document(file_path)
    parts: List[str] = []

    # Paragraphs
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text.strip())

    # Tables — extract each row as a single line
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    return _chunk("\n\n".join(parts))


def load_documents(directory: str) -> List[str]:
    chunks = []
    for filename in sorted(os.listdir(directory)):
        path = os.path.join(directory, filename)
        if filename.endswith(".pdf"):
            chunks.extend(load_pdf(path))
        elif filename.endswith(".docx"):
            chunks.extend(load_docx(path))
    return chunks
