import os
from datetime import UTC, datetime
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

    assert [
        (
            document.filename,
            document.chunk_count,
            document.size_bytes,
            document.modified_at,
            document.download_available,
        )
        for document in documents
    ] == [
        ("billing.md", 1, None, None, False),
        ("manual.txt", 2, None, None, False),
    ]


def test_list_documents_includes_uploaded_file_metadata(
    tmp_path: Path,
    vector_store: VectorStore,
) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    document_path = upload_dir / "manual.txt"
    document_path.write_text("Support instructions", encoding="utf-8")
    modified_at = datetime(2026, 8, 11, 10, 30, tzinfo=UTC)
    timestamp = modified_at.timestamp()
    os.utime(document_path, (timestamp, timestamp))
    service = DocumentManagementService(upload_dir, vector_store)

    documents = {document.filename: document for document in service.list_documents()}

    assert documents["manual.txt"].size_bytes == len(b"Support instructions")
    assert documents["manual.txt"].modified_at == modified_at
    assert documents["manual.txt"].download_available is True
    assert documents["billing.md"].size_bytes is None
    assert documents["billing.md"].modified_at is None
    assert documents["billing.md"].download_available is False


def test_get_document_path_returns_safe_uploaded_file(
    tmp_path: Path,
    vector_store: VectorStore,
) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    document_path = upload_dir / "manual.txt"
    document_path.write_text("Support instructions", encoding="utf-8")
    service = DocumentManagementService(upload_dir, vector_store)

    assert service.get_document_path("manual.txt") == document_path


def test_get_document_path_rejects_missing_file(
    tmp_path: Path,
    vector_store: VectorStore,
) -> None:
    service = DocumentManagementService(tmp_path / "uploads", vector_store)

    with pytest.raises(DocumentNotFoundError, match="Document not found: manual.txt"):
        service.get_document_path("manual.txt")


@pytest.mark.parametrize("filename", ["../manual.txt", "folder\\manual.txt"])
def test_get_document_path_rejects_unsafe_filename(
    tmp_path: Path,
    vector_store: VectorStore,
    filename: str,
) -> None:
    service = DocumentManagementService(tmp_path / "uploads", vector_store)

    with pytest.raises(ValueError, match="must not include a path"):
        service.get_document_path(filename)


def test_get_document_path_rejects_symlink_outside_upload_directory(
    tmp_path: Path,
    vector_store: VectorStore,
) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    outside_document = tmp_path / "outside.txt"
    outside_document.write_text("Private content", encoding="utf-8")
    (upload_dir / "manual.txt").symlink_to(outside_document)
    service = DocumentManagementService(upload_dir, vector_store)

    with pytest.raises(ValueError, match="must stay inside the upload directory"):
        service.get_document_path("manual.txt")


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
