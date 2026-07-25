from collections.abc import Iterator
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
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
def client(upload_dir: Path, ingestion_service: Mock) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


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
