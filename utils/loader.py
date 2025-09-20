# utils/loader.py
import os
from typing import List, Dict
from pypdf import PdfReader
from docx import Document

def _read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _read_pdf(path: str) -> str:
    text = []
    with open(path, "rb") as f:
        reader = PdfReader(f)
        for p in reader.pages:
            text.append(p.extract_text() or "")
    return "\n".join(text)

def _read_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def _chunk(text: str, chunk_size=800, overlap=120) -> List[str]:
    text = text.replace("\r", "")
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        start = start + chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]

def load_single_file(path: str) -> List[Dict]:
    """Load and chunk a single uploaded file into docs."""
    fn = os.path.basename(path)
    try:
        if fn.lower().endswith(".txt"):
            text = _read_txt(path)
        elif fn.lower().endswith(".pdf"):
            text = _read_pdf(path)
        elif fn.lower().endswith(".docx"):
            text = _read_docx(path)
        else:
            raise ValueError("Unsupported file format")
    except Exception as e:
        raise RuntimeError(f"Failed to read {fn}: {e}")

    docs = []
    for i, chunk in enumerate(_chunk(text)):
        docs.append({
            "id": f"{fn}-{i}",
            "text": chunk,
            "metadata": {"source": path, "file": fn}
        })
    return docs

def load_documents(root_dir: str = "data") -> List[Dict]:
    docs = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            try:
                if fn.lower().endswith(".txt"):
                    text = _read_txt(path)
                elif fn.lower().endswith(".pdf"):
                    text = _read_pdf(path)
                elif fn.lower().endswith(".docx"):
                    text = _read_docx(path)
                else:
                    continue
                for i, chunk in enumerate(_chunk(text)):
                    docs.append({"id": f"{fn}-{i}", "text": chunk, "metadata": {"source": os.path.relpath(path, root_dir), "file": fn}})
            except Exception:
                continue
    return docs
