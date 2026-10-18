"""
Healthcare RAG — FAISS Vector Store
Manages index creation, persistence, search, and metadata.
"""
import faiss
import numpy as np
import pickle
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class FAISSVectorStore:
    def __init__(self, dim: int = 384):
        self.dim   = dim
        self.index = faiss.IndexFlatIP(dim)   # Inner-product (cosine after normalize)
        self.docs: List[Dict[str, Any]] = []  # parallel to index rows

    def add(self, vectors: np.ndarray, metadata: List[Dict]):
        """Add embeddings and their metadata."""
        assert vectors.shape[1] == self.dim
        self.index.add(vectors.astype('float32'))
        self.docs.extend(metadata)

    def search(self, query_vec: np.ndarray, k: int = 6,
               filters: Optional[Dict] = None) -> List[Dict]:
        """Semantic search; returns top-k chunks with scores."""
        if self.index.ntotal == 0:
            return []
        k = min(k, self.index.ntotal)
        scores, idxs = self.index.search(query_vec.reshape(1,-1).astype('float32'), k*3)
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0:
                continue
            doc = dict(self.docs[idx])
            doc['score'] = float(score)
            # Apply metadata filters
            if filters:
                if not all(doc.get(fk) == fv for fk, fv in filters.items()):
                    continue
            results.append(doc)
            if len(results) >= k:
                break
        return results

    def save(self, dir_path: str):
        p = Path(dir_path); p.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(p / 'index.faiss'))
        with open(p / 'docs.pkl', 'wb') as f:
            pickle.dump(self.docs, f)
        with open(p / 'meta.json', 'w') as f:
            json.dump({'dim': self.dim, 'total': self.index.ntotal}, f)

    @classmethod
    def load(cls, dir_path: str) -> 'FAISSVectorStore':
        p = Path(dir_path)
        with open(p / 'meta.json') as f:
            meta = json.load(f)
        obj = cls(dim=meta['dim'])
        obj.index = faiss.read_index(str(p / 'index.faiss'))
        with open(p / 'docs.pkl', 'rb') as f:
            obj.docs = pickle.load(f)
        return obj

    @property
    def total(self):
        return self.index.ntotal
