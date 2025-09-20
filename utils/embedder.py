# utils/embedder.py
from typing import List, Dict
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings

embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# utils/embedder.py

def build_chroma_persistent(docs: List[Dict], persist_dir="db/chroma", collection_name="legal_docs"):
    import shutil
    # Remove old DB to avoid type mismatch
    shutil.rmtree(persist_dir, ignore_errors=True)

    client = chromadb.PersistentClient(path=persist_dir)
    col = client.create_collection(collection_name, metadata={"hnsw:space": "cosine"})

    ids = [d["id"] for d in docs]
    texts = [d["text"] for d in docs]
    metas = [d["metadata"] for d in docs]
    embs = embedder.embed_documents(texts)

    B = 256
    for i in range(0, len(ids), B):
        col.add(ids=ids[i:i+B], documents=texts[i:i+B], embeddings=embs[i:i+B], metadatas=metas[i:i+B])
    return col


def load_chroma_collection(persist_dir="db/chroma", collection_name="legal_docs"):
    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_or_create_collection(collection_name)

from utils.loader import load_single_file

def process_uploaded_file(path: str, persist_dir="db/chroma", collection_name="legal_docs"):
    """Embed a newly uploaded PDF/DOCX/TXT and add to Chroma DB."""
    docs = load_single_file(path)
    if not docs:
        return None
    
    client = chromadb.PersistentClient(path=persist_dir)
    col = client.get_or_create_collection(collection_name)

    ids = [d["id"] for d in docs]
    texts = [d["text"] for d in docs]
    metas = [d["metadata"] for d in docs]
    embs = embedder.embed_documents(texts)

    col.add(ids=ids, documents=texts, embeddings=embs, metadatas=metas)
    return docs

def query_collection(collection, query: str, k: int = 6) -> List[Dict]:
    q_emb = embedder.embed_query(query)
    res = collection.query(query_embeddings=[q_emb], n_results=k, include=["documents", "metadatas", "distances"])
    out: List[Dict] = []
    if not res or not res.get("documents"):
        return out

    docs0, metas0, dists0 = res["documents"][0], res["metadatas"][0], res.get("distances", [[None]*len(res["documents"][0])])[0]
    for content, meta, dist in zip(docs0, metas0, dists0):
        sim = None
        if dist is not None:
            try:
                sim = max(0.0, min(1.0, 1.0 - float(dist)))
            except Exception:
                sim = None
        out.append({"content": content, "source": meta.get("source", meta.get("file", "unknown")), "file": meta.get("file", "unknown"), "distance": dist, "similarity": sim})
    out.sort(key=lambda d: (d["distance"] if d["distance"] is not None else 9e9))
    return out
