# build_index.py
from utils.loader import load_documents
from utils.embedder import build_chroma_persistent

if __name__ == "__main__":
    print("📂 Loading documents from data/ ...")
    docs = load_documents("data")
    print(f"✅ Loaded {len(docs)} chunks")

    print("🔧 Building Chroma index ...")
    build_chroma_persistent(docs, persist_dir="db/chroma", collection_name="legal_docs")
    print("✅ Index built & persisted at db/chroma")
