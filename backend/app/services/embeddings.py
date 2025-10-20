from __future__ import annotations
import os, json, hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

STORAGE = Path(__file__).resolve().parent.parent / "storage"
STORAGE.mkdir(exist_ok=True)
INDEX_PATH = STORAGE / "index.faiss"
DOCSTORE_PATH = STORAGE / "docstore.json"

# lazy imports so app boots fast
_embedder = None
_index = None
_docstore: Dict[str, Any] = {}

def _lazy_models():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        import torch
        # Fix for PyTorch meta tensor issue
        try:
            # Try to use CPU explicitly to avoid device transfer issues
            _embedder = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
        except Exception as e:
            print(f"[embeddings] Warning: {e}")
            # Fallback: force CPU and ignore warnings
            import os
            os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
            _embedder = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
    return _embedder

def _lazy_index(d: int):
    global _index
    import faiss
    if _index is None:
        if INDEX_PATH.exists():
            _index = faiss.read_index(str(INDEX_PATH))
        else:
            _index = faiss.IndexFlatIP(d)  # cosine via normalized vectors
    return _index

def _save_index():
    import faiss
    if _index is not None:
        faiss.write_index(_index, str(INDEX_PATH))
    with open(DOCSTORE_PATH, "w", encoding="utf-8") as f:
        json.dump(_docstore, f, ensure_ascii=False, indent=2)

def _load_docstore():
    global _docstore
    if DOCSTORE_PATH.exists():
        _docstore = json.loads(DOCSTORE_PATH.read_text(encoding="utf-8"))

_load_docstore()

def _hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]

def chunk_text(txt: str, size: int = 900, overlap: int = 150) -> List[str]:
    txt = " ".join(txt.split())
    chunks = []
    i = 0
    while i < len(txt):
        chunk = txt[i:i+size]
        if not chunk:
            break
        chunks.append(chunk)
        i += size - overlap
    return chunks

def add_document(doc_title: str, source: str, text: str) -> Dict[str, Any]:
    """Chunk, embed, add to FAISS, update docstore."""
    _ = _lazy_models()
    chunks = chunk_text(text)
    if not chunks:
        return {"added": 0}

    vecs = _embedder.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
    index = _lazy_index(vecs.shape[1])
    start_id = len(_docstore.get("chunks", [])) if _docstore else 0

    # ensure docstore structure
    _docstore.setdefault("docs", {})
    _docstore.setdefault("chunks", [])

    doc_id = _hash(doc_title + source)
    _docstore["docs"][doc_id] = {"title": doc_title, "source": source}

    # add to index and docstore
    ids = []
    for j, c in enumerate(chunks):
        chunk_id = f"{doc_id}:{j}"
        ids.append(chunk_id)
        _docstore["chunks"].append({"id": chunk_id, "doc_id": doc_id, "text": c})

    # map ids to vectors for FAISS add with IDs (FlatIP has no add_with_ids, so keep parallel store)
    # We’ll append vectors; FAISS keeps order, we track positions via an array
    # Maintain a numpy file with positions → chunk_ids
    posmap_path = STORAGE / "positions.npy"
    existing = np.load(posmap_path, allow_pickle=True).tolist() if posmap_path.exists() else []
    new_positions = existing + ids
    np.save(posmap_path, np.array(new_positions, dtype=object))

    index.add(vecs.astype(np.float32))
    _save_index()
    return {"added": len(chunks), "doc_id": doc_id}

def retrieve(query: str, k: int = 3) -> List[Dict[str, Any]]:
    _ = _lazy_models()
    index = _lazy_index(384)  # MiniLM dim
    if index.ntotal == 0:
        return []
    import numpy as np
    q = _embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
    sims, idxs = index.search(q, k)
    posmap_path = STORAGE / "positions.npy"
    if not posmap_path.exists():
        return []
    positions = np.load(posmap_path, allow_pickle=True).tolist()
    out = []
    for rank, pos in enumerate(idxs[0]):
        if pos < 0 or pos >= len(positions):
            continue
        chunk_id = positions[pos]
        chunk = next((c for c in _docstore.get("chunks", []) if c["id"] == chunk_id), None)
        if not chunk:
            continue
        doc = _docstore["docs"].get(chunk["doc_id"], {})
        out.append({
            "rank": rank+1,
            "score": float(sims[0][rank]),
            "chunk_id": chunk_id,
            "text": chunk["text"],
            "doc": {"id": chunk["doc_id"], "title": doc.get("title"), "source": doc.get("source")}
        })
    return out
