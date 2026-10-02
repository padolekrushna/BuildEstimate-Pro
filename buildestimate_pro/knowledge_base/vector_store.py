"""Vector store abstraction for semantic search (pluggable backends).

This module defines a simple interface and a JSON-file fallback implementation.
Replace or extend with FAISS/Chroma/pgvector adapters later.
"""
from typing import List, Dict, Any
from pathlib import Path
import json


class VectorStore:
    def add(self, embeddings: List[Dict[str, Any]]):
        raise NotImplementedError()

    def search(self, query_embedding, top_k: int = 5):
        raise NotImplementedError()


class JSONVectorStore(VectorStore):
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._data = []
            self._flush()
        else:
            self._data = json.loads(self.path.read_text(encoding='utf8'))

    def _flush(self):
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding='utf8')

    def add(self, embeddings: List[Dict[str, Any]]):
        self._data.extend(embeddings)
        self._flush()

    def search(self, query_embedding, top_k: int = 5):
        # Deterministic fallback: simple substring match on text field
        q = query_embedding if isinstance(query_embedding, str) else str(query_embedding)
        hits = [r for r in self._data if q.lower() in (r.get('text') or '').lower()]
        return hits[:top_k]
