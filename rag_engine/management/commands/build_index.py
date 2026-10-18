"""
Management command: python manage.py build_index
Builds the FAISS RAG index from all active Knowledge Documents.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from documents.models import KnowledgeDocument
from rag_engine.phi_detector import redact_phi
from rag_engine.embeddings import LocalEmbedder
from rag_engine.vector_store import FAISSVectorStore
from rag_engine.pipeline import RAGPipeline
from pathlib import Path
from django.conf import settings


def chunk_text(text, size=400, overlap=80):
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = ' '.join(words[i:i+size])
        if chunk.strip():
            chunks.append(chunk)
        i += (size - overlap)
        if i >= len(words):
            break
    return chunks


class Command(BaseCommand):
    help = 'Build FAISS vector index from all active Knowledge Documents'

    def add_arguments(self, parser):
        parser.add_argument('--chunk-size',  type=int, default=400)
        parser.add_argument('--overlap',     type=int, default=80)

    def handle(self, *args, **options):
        INDEX_DIR     = Path(settings.RAG_INDEX_DIR)
        EMBEDDER_PATH = INDEX_DIR / 'embedder.pkl'
        STORE_DIR     = INDEX_DIR / 'faiss_store'
        INDEX_DIR.mkdir(parents=True, exist_ok=True)

        docs = KnowledgeDocument.objects.filter(is_active=True)
        if not docs.exists():
            self.stdout.write(self.style.WARNING('No active documents found.'))
            return

        chunk_size = options['chunk_size']
        overlap    = options['overlap']
        all_chunks, all_meta = [], []

        for doc in docs:
            text   = redact_phi(doc.content)
            chunks = chunk_text(text, chunk_size, overlap)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_meta.append({
                    'doc_id':    doc.id,
                    'source_id': doc.source_id,
                    'title':     doc.title,
                    'doc_type':  doc.doc_type,
                    'date':      doc.created_at.strftime('%Y-%m-%d'),
                    'chunk_idx': i,
                    'content':   chunk,
                })

        self.stdout.write(f'Chunked {docs.count()} docs → {len(all_chunks)} chunks')

        n_components = min(384, len(all_chunks) - 1)
        embedder = LocalEmbedder(dim=n_components)
        embedder.fit(all_chunks)
        vectors  = embedder.embed(all_chunks)
        actual_dim = vectors.shape[1]

        store = FAISSVectorStore(dim=actual_dim)
        store.add(vectors, all_meta)

        embedder.save(str(EMBEDDER_PATH))
        store.save(str(STORE_DIR))

        docs.update(is_indexed=True, indexed_at=timezone.now())
        RAGPipeline.reset()

        self.stdout.write(self.style.SUCCESS(
            f'✅ Index built: {store.total} vectors (dim={actual_dim}) from {docs.count()} documents'))
