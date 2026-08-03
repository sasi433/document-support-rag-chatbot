from pathlib import Path

import pytest

from app.services.document_management import (
    DocumentManagementService,
    DocumentNotFoundError,
)
from app.services.vector_store import VectorStore


@pytest.fixture
def vector_store(tmp_path: Path) -> VectorStore:
    store = VectorStore(tmp_path / "chroma", "test_documents")
    store.add_documents(
        ids=["manual.txt:0", "manual.txt:1", "billing.md:0"],
        documents=["Restart.", "Update.", "Pay monthly."],
        embeddings=[[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]],
        metadatas=[
            {"source": "manual.txt", "chunk_index": 0},
            {"source": "manual.txt", "chunk_index": 1},
            {"source": "billing.md", "chunk_index": 0},
        ],
    )
    return store


def test_list_documents_returns_sorted_sources_with_chunk_counts(
    tmp_path: Path,
    vector_store: VectorStore,
) -> None:
    service = DocumentManagementService(tmp_path / "uploads", vector_store)

    documents = service.list_documents()

    assert [(document.filename, document.chunk_count) for document in documents] == [
        ("billing.md", 1),
        ("manual.txt", 2),
    ]


def test_delete_document_removes_file_and_indexed_chunks(
    tmp_path: Path,
    vector_store: VectorStore,
) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    document_path = upload_dir / "manual.txt"
    document_path.write_text("Support instructions", encoding="utf-8")
    service = DocumentManagementService(upload_dir, vector_store)

    service.delete_document("manual.txt")

    assert not document_path.exists()
    assert vector_store.source_counts() == {"billing.md": 1}


def test_delete_document_removes_orphaned_index_entries(
    tmp_path: Path,
    vector_store: VectorStore,
) -> None:
    service = DocumentManagementService(tmp_path / "uploads", vector_store)

    service.delete_document("manual.txt")

    assert vector_store.source_counts() == {"billing.md": 1}


def test_delete_document_rejects_unknown_document(tmp_path: Path) -> None:
    service = DocumentManagementService(
        tmp_path / "uploads",
        VectorStore(tmp_path / "chroma", "test_documents"),
    )

    with pytest.raises(DocumentNotFoundError, match="Document not found: missing.txt"):
        service.delete_document("missing.txt")


@pytest.mark.parametrize("filename", ["../escape.txt", "folder\\escape.txt"])
def test_delete_document_rejects_unsafe_filename(
    tmp_path: Path,
    filename: str,
) -> None:
    service = DocumentManagementService(
        tmp_path / "uploads",
        VectorStore(tmp_path / "chroma", "test_documents"),
    )

    with pytest.raises(ValueError, match="must not include a path"):
        service.delete_document(filename)
