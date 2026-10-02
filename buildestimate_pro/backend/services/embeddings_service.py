from typing import List
import hashlib


def _deterministic_embedding(text: str, dim: int = 32) -> List[float]:
    """Create a deterministic pseudo-embedding from text using SHA256.

    This is a lightweight, dependency-free fallback for local development.
    Embeddings are stable but NOT semantically meaningful compared to ML models.
    """
    if text is None:
        text = ""
    seed = text.encode("utf8")
    out = []
    h = hashlib.sha256(seed).digest()
    # expand hash material until we have enough bytes
    while len(out) < dim:
        h = hashlib.sha256(h).digest()
        for i in range(0, len(h), 4):
            if len(out) >= dim:
                break
            chunk = h[i : i + 4]
            v = int.from_bytes(chunk, "big", signed=False)
            # normalize 0..2^32-1 -> -1..1
            out.append(((v / 0xFFFFFFFF) * 2.0) - 1.0)
    return out[:dim]


def embed_texts(texts: List[str], dim: int = 32) -> List[List[float]]:
    return [_deterministic_embedding(t or "", dim=dim) for t in texts]
