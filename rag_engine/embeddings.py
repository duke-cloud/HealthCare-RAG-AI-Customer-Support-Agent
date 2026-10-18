"""
Healthcare RAG — Embedding Engine
Uses TF-IDF + SVD for local embeddings (no API required).
Falls back gracefully; compatible with FAISS index.
"""
import numpy as np
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import normalize

EMBEDDING_DIM = 384


class LocalEmbedder:
    """TF-IDF + TruncatedSVD embedder — fully local, no API needed."""

    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=50000,
                ngram_range=(1, 2),
                sublinear_tf=True,
                min_df=1,
            )),
            ('svd', TruncatedSVD(n_components=dim, random_state=42)),
        ])
        self.is_fitted = False

    def fit(self, texts: list[str]):
        self.pipeline.fit(texts)
        self.is_fitted = True

    def embed(self, texts: list[str]) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Embedder not fitted. Call fit() first.")
        vecs = self.pipeline.transform(texts)
        return normalize(vecs).astype('float32')

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump({'pipeline': self.pipeline, 'is_fitted': self.is_fitted, 'dim': self.dim}, f)

    @classmethod
    def load(cls, path: str) -> 'LocalEmbedder':
        with open(path, 'rb') as f:
            state = pickle.load(f)
        obj = cls(dim=state['dim'])
        obj.pipeline   = state['pipeline']
        obj.is_fitted  = state['is_fitted']
        return obj
