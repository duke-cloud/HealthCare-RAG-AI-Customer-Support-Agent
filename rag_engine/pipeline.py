"""
Healthcare RAG — Main Pipeline Orchestrator
Singleton that manages the embedder, vector store, retriever, and generator.
"""
import os, re, pickle
from pathlib import Path
from typing import List, Dict, Optional
from django.conf import settings

from .embeddings import LocalEmbedder
from .vector_store import FAISSVectorStore
from .retriever import RAGRetriever
from .phi_detector import detect_phi, redact_phi, classify_query_risk
from .generator import generate_answer

INDEX_DIR    = Path(settings.RAG_INDEX_DIR)
EMBEDDER_PATH = INDEX_DIR / 'embedder.pkl'
STORE_DIR     = INDEX_DIR / 'faiss_store'


class RAGPipeline:
    _instance = None

    def __init__(self):
        self.embedder  = None
        self.store     = None
        self.retriever = None
        self.loaded    = False
        self._try_load()

    @classmethod
    def get(cls) -> 'RAGPipeline':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Force reload on next get() call."""
        cls._instance = None

    def _try_load(self):
        try:
            if EMBEDDER_PATH.exists() and (STORE_DIR / 'index.faiss').exists():
                self.embedder  = LocalEmbedder.load(str(EMBEDDER_PATH))
                self.store     = FAISSVectorStore.load(str(STORE_DIR))
                self.retriever = RAGRetriever(self.store, self.embedder)
                self.loaded    = True
        except Exception as e:
            self.loaded = False

    def is_ready(self) -> bool:
        return self.loaded and self.store and self.store.total > 0

    def query(self, question: str, user_id: Optional[str] = None,
              filters: Optional[Dict] = None) -> Dict:
        """Full RAG query pipeline. Returns answer + metadata."""

        # 1. PHI / safety check on raw question
        risk = classify_query_risk(question)

        # 2. Redact PHI from question before embedding/logging
        safe_q = redact_phi(question)

        result = {
            'question':   safe_q,
            'risk_level': risk,
            'answer':     '',
            'sources':    [],
            'confidence': 0.0,
            'method':     'unknown',
            'escalated':  False,
            'chunks_retrieved': 0,
        }

        if risk in ('phi', 'clinical'):
            gen = generate_answer(safe_q, [], risk_level=risk)
            result.update(gen)
            return result

        # 3. Retrieve
        if not self.is_ready():
            result['answer']  = ("The knowledge base is not yet loaded. "
                                 "Please contact an administrator to index documents.")
            result['method']  = 'no_index'
            result['confidence'] = 0.0
            return result

        top_k    = getattr(settings, 'RAG_TOP_K', 6)
        rerank_k = getattr(settings, 'RAG_RERANK_K', 3)
        chunks   = self.retriever.retrieve_and_rerank(safe_q, k=top_k, rerank_k=rerank_k,
                                                       filters=filters)
        result['chunks_retrieved'] = len(chunks)

        # 4. Generate
        gen = generate_answer(safe_q, chunks, risk_level=risk)
        result.update(gen)
        return result


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
    """Sliding window chunker."""
    words  = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = ' '.join(words[i:i+chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += (chunk_size - overlap)
    return chunks


def ingest_documents(doc_records: List[Dict]) -> Dict:
    """
    Ingest a list of document records into the RAG index.
    Each record: {'id', 'title', 'content', 'doc_type', 'source_id', 'date'}
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    chunk_size = getattr(settings, 'RAG_CHUNK_SIZE', 400)
    overlap    = getattr(settings, 'RAG_CHUNK_OVERLAP', 80)

    all_chunks   = []
    all_metadata = []

    for doc in doc_records:
        text = redact_phi(doc.get('content', ''))
        chunks = chunk_text(text, chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                'doc_id':    doc['id'],
                'source_id': doc.get('source_id', f"doc_{doc['id']}"),
                'title':     doc.get('title', 'Untitled'),
                'doc_type':  doc.get('doc_type', 'general'),
                'date':      doc.get('date', ''),
                'chunk_idx': i,
                'content':   chunk,
            })

    if not all_chunks:
        return {'status': 'error', 'message': 'No chunks generated', 'chunks': 0}

    # Build embedder with auto dim based on data size
    n_components = min(384, len(all_chunks) - 1, 50000)
    embedder = LocalEmbedder(dim=n_components)
    embedder.fit(all_chunks)
    vectors = embedder.embed(all_chunks)
    actual_dim = vectors.shape[1]

    # Build store with actual dimension
    store = FAISSVectorStore(dim=actual_dim)
    store.add(vectors, all_metadata)

    # Save
    embedder.save(str(EMBEDDER_PATH))
    store.save(str(STORE_DIR))

    # Reset singleton so next query reloads
    RAGPipeline.reset()

    return {
        'status':  'success',
        'chunks':  len(all_chunks),
        'docs':    len(doc_records),
        'total_indexed': store.total,
    }
