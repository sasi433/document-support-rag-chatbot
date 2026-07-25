from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.services.chunker import chunk_document
from app.services.document_loader import load_document
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


class DocumentIngestionError(RuntimeError):
    """Raised when a document cannot be prepared for indexing."""


class IngestionService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ) -> None:
        self._embedding_service = embedding_service
        self._vector_store = vector_store

    def ingest_document(self, file_path: str | Path) -> int:
        path = Path(file_path)
        chunks = chunk_document(load_document(path), source=path.name)

        if not chunks:
            raise DocumentIngestionError("Document does not contain indexable text")

        embeddings = self._embedding_service.embed_texts(
            [chunk.text for chunk in chunks]
        )

        self._vector_store.add_documents(
            ids=[f"{chunk.source}:{chunk.chunk_index}" for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ],
        )

        return len(chunks)


@lru_cache
def get_ingestion_service() -> IngestionService:
    settings = get_settings()
    embedding_service = EmbeddingService(
        api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
    )
    vector_store = VectorStore(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
    )
    return IngestionService(embedding_service, vector_store)
