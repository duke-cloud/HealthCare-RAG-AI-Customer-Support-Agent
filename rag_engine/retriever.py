"""
Healthcare RAG — Retriever + Reranker
Combines FAISS semantic search with TF-IDF reranking.
"""
from typing import List, Dict, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from .vector_store import FAISSVectorStore
from .embeddings import LocalEmbedder


class RAGRetriever:
    def __init__(self, store: FAISSVectorStore, embedder: LocalEmbedder):
        self.store   = store
        self.embedder = embedder

    def retrieve(self, query: str, k: int = 6,
                 filters: Optional[Dict] = None) -> List[Dict]:
        """Semantic retrieval with optional metadata filters."""
        q_vec = self.embedder.embed_query(query)
        return self.store.search(q_vec, k=k, filters=filters)

    def rerank(self, query: str, chunks: List[Dict], top_k: int = 3) -> List[Dict]:
        """TF-IDF reranker — scores chunks by term overlap with query."""
        if not chunks:
            return []
        texts   = [query] + [c['content'] for c in chunks]
        try:
            tfidf   = TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)
            mat     = tfidf.fit_transform(texts)
            scores  = cosine_similarity(mat[0:1], mat[1:]).flatten()
            for i, c in enumerate(chunks):
                c['rerank_score'] = float(scores[i]) if i < len(scores) else 0.0
            ranked = sorted(chunks, key=lambda x: x.get('rerank_score',0), reverse=True)
            return ranked[:top_k]
        except Exception:
            return chunks[:top_k]

    def retrieve_and_rerank(self, query: str, k: int = 6,
                            rerank_k: int = 3, filters: Optional[Dict] = None) -> List[Dict]:
        candidates = self.retrieve(query, k=k, filters=filters)
        return self.rerank(query, candidates, top_k=rerank_k)
