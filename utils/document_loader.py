import os
from typing import List

import fitz  # pymupdf
from docx import Document

CHUNK_SIZE = 500     # characters per chunk
CHUNK_OVERLAP = 50  # characters of overlap between chunks


def _chunk(text: str) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c]


def load_pdf(file_path: str) -> List[str]:
    doc = fitz.open(file_path)
    text = "\n".join(page.get_text() for page in doc)
    return _chunk(text)


def load_docx(file_path: str) -> List[str]:
    doc = Document(file_path)
    text = "\n".join(para.text for para in doc.paragraphs)
    return _chunk(text)


def load_documents(directory: str) -> List[str]:
    chunks = []
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)
        if filename.endswith(".pdf"):
            chunks.extend(load_pdf(path))
        elif filename.endswith(".docx"):
            chunks.extend(load_docx(path))
    return chunks
