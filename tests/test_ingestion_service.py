from pathlib import Path
from unittest.mock import Mock

import pytest

from app.services.embeddings import EmbeddingService
from app.services.ingestion_service import DocumentIngestionError, IngestionService
from app.services.vector_store import VectorStore


def test_ingest_document_embeds_and_indexes_chunks(tmp_path: Path) -> None:
    document_path = tmp_path / "manual.txt"
    document_path.write_text("a" * 1200, encoding="utf-8")

    embedding_service = Mock(spec=EmbeddingService)
    embedding_service.embed_texts.return_value = [[1.0, 0.0], [0.0, 1.0]]
    vector_store = VectorStore(tmp_path / "chroma", "test_documents")
    ingestion_service = IngestionService(embedding_service, vector_store)

    chunk_count = ingestion_service.ingest_document(document_path)

    assert chunk_count == 2
    assert vector_store.count() == 2

    embedded_texts = embedding_service.embed_texts.call_args.args[0]
    assert len(embedded_texts) == 2
    assert all(embedded_texts)

    results = vector_store.search([1.0, 0.0], limit=2)
    assert {result.record_id for result in results} == {
        "manual.txt:0",
        "manual.txt:1",
    }
    assert {result.metadata["source"] for result in results} == {"manual.txt"}
    assert {result.metadata["chunk_index"] for result in results} == {0, 1}


def test_ingest_document_rejects_document_without_text(tmp_path: Path) -> None:
    document_path = tmp_path / "empty.txt"
    document_path.write_text("  \n", encoding="utf-8")

    embedding_service = Mock(spec=EmbeddingService)
    vector_store = Mock(spec=VectorStore)
    ingestion_service = IngestionService(embedding_service, vector_store)

    with pytest.raises(
        DocumentIngestionError,
        match="Document does not contain indexable text",
    ):
        ingestion_service.ingest_document(document_path)

    embedding_service.embed_texts.assert_not_called()
    vector_store.add_documents.assert_not_called()
