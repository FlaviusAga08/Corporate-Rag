import os
import re
from typing import List

import fitz  # pymupdf
from docx import Document

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def _chunk(text: str) -> List[str]:
    # Split on paragraph breaks first to keep logical units together
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
                # paragraph is too long — split by character with overlap
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


def load_pdf(file_path: str) -> List[str]:
    doc = fitz.open(file_path)
    text = "\n\n".join(page.get_text() for page in doc)
    return _chunk(text)


def load_docx(file_path: str) -> List[str]:
    doc = Document(file_path)
    text = "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
    return _chunk(text)


def load_documents(directory: str) -> List[str]:
    chunks = []
    for filename in sorted(os.listdir(directory)):
        path = os.path.join(directory, filename)
        if filename.endswith(".pdf"):
            chunks.extend(load_pdf(path))
        elif filename.endswith(".docx"):
            chunks.extend(load_docx(path))
    return chunks
