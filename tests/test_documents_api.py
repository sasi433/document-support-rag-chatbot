from collections.abc import Iterator
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services.document_management import (
    DocumentManagementService,
    DocumentNotFoundError,
    IndexedDocument,
    get_document_management_service,
)
from app.services.embeddings import EmbeddingServiceError
from app.services.ingestion_service import (
    DocumentIngestionError,
    IngestionService,
    get_ingestion_service,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    temporary_upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(get_settings(), "upload_dir", temporary_upload_dir)
    return temporary_upload_dir


@pytest.fixture
def ingestion_service() -> Iterator[Mock]:
    service = Mock(spec=IngestionService)
    service.ingest_document.return_value = 1
    app.dependency_overrides[get_ingestion_service] = lambda: service

    yield service

    app.dependency_overrides.pop(get_ingestion_service, None)


@pytest.fixture
def document_management_service() -> Iterator[Mock]:
    service = Mock(spec=DocumentManagementService)
    service.list_documents.return_value = []
    app.dependency_overrides[get_document_management_service] = lambda: service

    yield service

    app.dependency_overrides.pop(get_document_management_service, None)


@pytest.fixture
def client(
    upload_dir: Path,
    ingestion_service: Mock,
    document_management_service: Mock,
) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_list_documents_returns_indexed_documents(
    client: TestClient,
    document_management_service: Mock,
) -> None:
    document_management_service.list_documents.return_value = [
        IndexedDocument(filename="billing.md", chunk_count=1),
        IndexedDocument(filename="manual.txt", chunk_count=2),
    ]

    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == {
        "documents": [
            {"filename": "billing.md", "chunk_count": 1},
            {"filename": "manual.txt", "chunk_count": 2},
        ]
    }


def test_list_documents_returns_empty_list(
    client: TestClient,
    document_management_service: Mock,
) -> None:
    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == {"documents": []}


def test_document_capabilities_returns_upload_constraints(
    client: TestClient,
) -> None:
    response = client.get("/documents/capabilities")

    assert response.status_code == 200
    assert response.json() == {
        "supported_extensions": [".md", ".pdf", ".txt"],
        "max_upload_size_bytes": 10 * 1024 * 1024,
    }


def test_download_document_returns_file_as_attachment(
    client: TestClient,
    upload_dir: Path,
    document_management_service: Mock,
) -> None:
    upload_dir.mkdir()
    document_path = upload_dir / "manual.txt"
    document_path.write_text("Support instructions", encoding="utf-8")
    document_management_service.get_document_path.return_value = document_path

    response = client.get("/documents/manual.txt/download")

    assert response.status_code == 200
    assert response.content == b"Support instructions"
    assert response.headers["content-type"].startswith("text/plain")
    assert response.headers["content-disposition"] == (
        'attachment; filename="manual.txt"'
    )
    assert response.headers["cache-control"] == "no-store"
    document_management_service.get_document_path.assert_called_once_with(
        "manual.txt"
    )


def test_download_document_returns_not_found(
    client: TestClient,
    document_management_service: Mock,
) -> None:
    document_management_service.get_document_path.side_effect = DocumentNotFoundError(
        "Document not found: missing.txt"
    )

    response = client.get("/documents/missing.txt/download")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found: missing.txt"}


def test_download_document_rejects_invalid_filename(
    client: TestClient,
    document_management_service: Mock,
) -> None:
    document_management_service.get_document_path.side_effect = ValueError(
        "Unsupported document type: .csv"
    )

    response = client.get("/documents/manual.csv/download")

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported document type: .csv"}


def test_delete_document_returns_deleted_status(
    client: TestClient,
    document_management_service: Mock,
) -> None:
    response = client.delete("/documents/manual.txt")

    assert response.status_code == 200
    assert response.json() == {"filename": "manual.txt", "status": "deleted"}
    document_management_service.delete_document.assert_called_once_with("manual.txt")


def test_delete_document_returns_not_found(
    client: TestClient,
    document_management_service: Mock,
) -> None:
    document_management_service.delete_document.side_effect = DocumentNotFoundError(
        "Document not found: missing.txt"
    )

    response = client.delete("/documents/missing.txt")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found: missing.txt"}


def test_delete_document_rejects_invalid_filename(
    client: TestClient,
    document_management_service: Mock,
) -> None:
    document_management_service.delete_document.side_effect = ValueError(
        "Unsupported document type: .csv"
    )

    response = client.delete("/documents/support.csv")

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported document type: .csv"}


@pytest.mark.parametrize(
    ("filename", "content", "content_type"),
    [
        ("support.txt", b"Plain text support content.", "text/plain"),
        ("support.md", b"# Markdown support content", "text/markdown"),
    ],
)
def test_upload_document_saves_text_documents(
    client: TestClient,
    upload_dir: Path,
    ingestion_service: Mock,
    filename: str,
    content: bytes,
    content_type: str,
) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": (filename, content, content_type)},
    )

    assert response.status_code == 201
    assert response.json() == {"filename": filename, "status": "uploaded"}
    assert (upload_dir / filename).read_bytes() == content
    ingestion_service.ingest_document.assert_called_once_with(upload_dir / filename)


def test_upload_document_saves_pdf(
    client: TestClient,
    upload_dir: Path,
    ingestion_service: Mock,
) -> None:
    content = (FIXTURES_DIR / "support_document.pdf").read_bytes()

    response = client.post(
        "/documents/upload",
        files={"file": ("support.pdf", content, "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json() == {
        "filename": "support.pdf",
        "status": "uploaded",
    }
    assert (upload_dir / "support.pdf").read_bytes() == content
    ingestion_service.ingest_document.assert_called_once_with(
        upload_dir / "support.pdf"
    )


def test_upload_document_rejects_unsupported_file(
    client: TestClient,
    upload_dir: Path,
    ingestion_service: Mock,
) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("support.csv", b"unsupported", "text/csv")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported document type: .csv"}
    assert not upload_dir.exists()
    ingestion_service.ingest_document.assert_not_called()


def test_upload_document_rejects_oversized_file(
    client: TestClient,
    upload_dir: Path,
    ingestion_service: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "max_upload_size_mb", 1)
    content = b"x" * (1024 * 1024 + 1)

    response = client.post(
        "/documents/upload",
        files={"file": ("large.txt", content, "text/plain")},
    )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "Document exceeds maximum upload size of 1 MB"
    }
    assert not (upload_dir / "large.txt").exists()
    ingestion_service.ingest_document.assert_not_called()


def test_upload_document_does_not_overwrite_existing_file(
    client: TestClient,
    upload_dir: Path,
    ingestion_service: Mock,
) -> None:
    first_content = b"Original support content"
    first_response = client.post(
        "/documents/upload",
        files={"file": ("support.txt", first_content, "text/plain")},
    )
    second_response = client.post(
        "/documents/upload",
        files={"file": ("support.txt", b"Replacement content", "text/plain")},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Document already exists: support.txt"
    }
    assert (upload_dir / "support.txt").read_bytes() == first_content
    ingestion_service.ingest_document.assert_called_once_with(
        upload_dir / "support.txt"
    )


@pytest.mark.parametrize("filename", ["../escape.txt", "folder\\escape.txt"])
def test_upload_document_rejects_path_in_filename(
    client: TestClient,
    upload_dir: Path,
    ingestion_service: Mock,
    filename: str,
) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": (filename, b"unsafe", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Document filename must not include a path"
    }
    assert not upload_dir.exists()
    assert not (upload_dir.parent / "escape.txt").exists()
    ingestion_service.ingest_document.assert_not_called()


def test_upload_document_removes_file_when_document_has_no_text(
    client: TestClient,
    upload_dir: Path,
    ingestion_service: Mock,
) -> None:
    ingestion_service.ingest_document.side_effect = DocumentIngestionError(
        "Document does not contain indexable text"
    )

    response = client.post(
        "/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Document does not contain indexable text"
    }
    assert not (upload_dir / "empty.txt").exists()


def test_upload_document_removes_file_when_embedding_fails(
    client: TestClient,
    upload_dir: Path,
    ingestion_service: Mock,
) -> None:
    ingestion_service.ingest_document.side_effect = EmbeddingServiceError(
        "Failed to generate embeddings"
    )

    response = client.post(
        "/documents/upload",
        files={"file": ("support.txt", b"Support content", "text/plain")},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Failed to generate embeddings"}
    assert not (upload_dir / "support.txt").exists()
