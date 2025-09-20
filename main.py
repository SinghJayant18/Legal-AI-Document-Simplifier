# main.py
import os, io
from typing import List, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from pypdf import PdfReader
except Exception:
    from PyPDF2 import PdfReader
from docx import Document

from utils.embedder import (
    load_chroma_collection,
    query_collection,
    process_uploaded_file,   # ✅ NEW import
)
from utils.rag_handler import generate_response, generate_case_pdf

PERSIST_DIR = "db/chroma"
COLLECTION_NAME = "legal_docs"
REPORTS_DIR = "files"
UPLOAD_DIR = "uploads"

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Legal RAG Backend", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/files", StaticFiles(directory=REPORTS_DIR), name="files")

try:
    collection = load_chroma_collection(PERSIST_DIR, COLLECTION_NAME)
except Exception:
    collection = None



def _is_relevant(hits: List[Dict], min_sim: float = 0.78) -> bool:
    if not hits:
        return False
    best = max([h.get("similarity") or 0.0 for h in hits])
    return best >= min_sim


def _read_pdf_bytes(b: bytes) -> str:
    text = []
    reader = PdfReader(io.BytesIO(b))
    for p in getattr(reader, "pages", []):
        try:
            text.append(p.extract_text() or "")
        except Exception:
            continue
    return "\n".join(text).strip()


def _read_docx_bytes(b: bytes) -> str:
    doc = Document(io.BytesIO(b))
    return "\n".join(p.text for p in doc.paragraphs).strip()


def fetch_cases_from_api(query: str) -> str:
    # Stub: replace with real case-law API
    return f"Fetched prominent cases for query: {query}"


@app.get("/")
def root():
    try:
        count = collection.count() if collection else 0
    except Exception:
        count = 0
    return {"message": "Legal RAG backend running ✅", "indexed_chunks": count}

from pydantic import BaseModel
class AskPayload(BaseModel):
    query: str

@app.post("/ask")
async def ask(request: Request, payload: AskPayload):
    q = payload.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Missing query")

    retrieved = query_collection(collection, q, k=6) if collection else []
    use_ctx = _is_relevant(retrieved)

    if not use_ctx:
        q += f"\n\nExtra context: {fetch_cases_from_api(q)}"

    answer = generate_response(q, retrieved_docs=retrieved if use_ctx else None)
    pdf_file, _ = generate_case_pdf(q, answer, retrieved if use_ctx else None, reports_dir=REPORTS_DIR)
    pdf_url = f"{request.base_url}files/{pdf_file}"

    return {"answer": answer, "references": [{"type": "pdf", "file": pdf_file, "url": pdf_url}]}

@app.get("/health")
def health():
    return {"status": "ok"}
@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(raw)

    # ✅ Embed uploaded file into Chroma DB
    docs = process_uploaded_file(save_path, persist_dir=PERSIST_DIR, collection_name=COLLECTION_NAME)

    name = file.filename.lower()
    if name.endswith(".pdf"):
        content = _read_pdf_bytes(raw)
    elif name.endswith(".docx"):
        content = _read_docx_bytes(raw)
    elif name.endswith(".txt"):
        content = raw.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(status_code=415, detail="Unsupported file")

    if not content.strip():
        content = "No readable text could be extracted."

    q = (
        "Simplify this legal document for a layperson. Add IPC/Acts, "
        "prominent cases and compare verdict outcomes. "
        "Give pros/cons of filing vs not filing, and suggestions.\n\n"
        f"Document:\n{content[:8000]}"
    )

    retrieved = query_collection(collection, q, k=6) if collection else []
    use_ctx = _is_relevant(retrieved)

    if not use_ctx:
        q += f"\n\nExtra context: {fetch_cases_from_api('document analysis')}"

    answer = generate_response(q, retrieved_docs=retrieved if use_ctx else None)
    pdf_file, _ = generate_case_pdf(q, answer, retrieved if use_ctx else None, reports_dir=REPORTS_DIR)
    pdf_url = f"{request.base_url}files/{pdf_file}"

    return {
        "filename": file.filename,
        "chunks_added": len(docs),   # ✅ show how many chunks embedded
        "analysis": answer,
        "references": [{"type": "pdf", "file": pdf_file, "url": pdf_url}],
    }


@app.post("/ask-with-doc")
async def ask_with_doc(request: Request, query: str = Form(...), file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(raw)

    # ✅ Embed uploaded file into Chroma DB
    docs = process_uploaded_file(save_path, persist_dir=PERSIST_DIR, collection_name=COLLECTION_NAME)

    name = file.filename.lower()
    if name.endswith(".pdf"):
        doc_text = _read_pdf_bytes(raw)
    elif name.endswith(".docx"):
        doc_text = _read_docx_bytes(raw)
    elif name.endswith(".txt"):
        doc_text = raw.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(status_code=415, detail="Unsupported file")

    if not doc_text.strip():
        doc_text = "No readable text could be extracted."

    q = (
        f"User query: {query}\n\nDocument:\n{doc_text[:8000]}\n\n"
        "Task: Provide overview, IPC/Acts/Sections, amendments, cases, "
        "precautions, pros/cons, and solution suggestion."
    )

    retrieved = query_collection(collection, q, k=6) if collection else []
    use_ctx = _is_relevant(retrieved)

    if not use_ctx:
        q += f"\n\nExtra context: {fetch_cases_from_api(query)}"

    answer = generate_response(q, retrieved_docs=retrieved if use_ctx else None)
    pdf_file, _ = generate_case_pdf(q, answer, retrieved if use_ctx else None, reports_dir=REPORTS_DIR)
    pdf_url = f"{request.base_url}files/{pdf_file}"

    return {
        "query": query,
        "filename": file.filename,
        "chunks_added": len(docs),   # ✅ new info
        "analysis": answer,
        "references": [{"type": "pdf", "file": pdf_file, "url": pdf_url}],
    }
