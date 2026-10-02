import os
from pathlib import Path
from typing import List, Dict, Any
from knowledge_base.vector_store import JSONVectorStore

# Import ingest function from scripts
from scripts.ingest_dsr import ingest as ingest_pdf

# Embeddings (deterministic fallback)
from backend.services.embeddings_service import embed_texts


DATA_UPLOADS = Path(__file__).parents[2] / "data" / "uploads"
EMBEDDINGS_PATH = Path(__file__).parents[2] / "knowledge_base" / "embeddings.json"
DATA_UPLOADS.mkdir(parents=True, exist_ok=True)


def ingest_and_index(file_path: str) -> Dict[str, Any]:
    """Ingest a DSR PDF at file_path, chunk it and add to the JSON vector store.

    Returns dict with counts.
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(str(p))

    # Produce chunks JSON next to file
    out_json = str(p.with_suffix('.chunks.json'))
    ingest_pdf(str(p), out_json=out_json)

    # Read chunks
    import json

    with open(out_json, 'r', encoding='utf8') as f:
        records = json.load(f)

    store = JSONVectorStore(str(EMBEDDINGS_PATH))
    # Normalize and add; compute deterministic embeddings for local dev
    embeddings = []
    texts = [r.get("text") for r in records]
    vectors = embed_texts(texts, dim=32)
    for r, vec in zip(records, vectors):
        embeddings.append({
            "id": r.get("id"),
            "text": r.get("text"),
            "source": r.get("source"),
            "embedding": vec,
        })
    store.add(embeddings)
    return {"chunks": len(embeddings)}


def semantic_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    store = JSONVectorStore(str(EMBEDDINGS_PATH))
    return store.search(query, top_k=top_k)
