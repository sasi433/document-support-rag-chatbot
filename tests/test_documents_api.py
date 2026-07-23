from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    temporary_upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(get_settings(), "upload_dir", temporary_upload_dir)
    return temporary_upload_dir


@pytest.fixture
def client(upload_dir: Path) -> Iterator[TestClient]:
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


def test_upload_document_saves_pdf(
    client: TestClient,
    upload_dir: Path,
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


def test_upload_document_rejects_unsupported_file(
    client: TestClient,
    upload_dir: Path,
) -> None:
    response = client.post(
        "/documents/upload",
        files={"file": ("support.csv", b"unsupported", "text/csv")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported document type: .csv"}
    assert not upload_dir.exists()


def test_upload_document_does_not_overwrite_existing_file(
    client: TestClient,
    upload_dir: Path,
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


@pytest.mark.parametrize("filename", ["../escape.txt", "folder\\escape.txt"])
def test_upload_document_rejects_path_in_filename(
    client: TestClient,
    upload_dir: Path,
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
