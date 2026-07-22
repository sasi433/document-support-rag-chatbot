from pathlib import Path

import pytest

from app.services.document_loader import load_document


@pytest.mark.parametrize(
    ("extension", "content"),
    [
        (".txt", "Plain text support content."),
        (".md", "# Support Guide\n\nMarkdown support content."),
    ],
)
def test_load_document_reads_text_files(
    tmp_path: Path,
    extension: str,
    content: str,
) -> None:
    document = tmp_path / f"support{extension}"
    document.write_text(content, encoding="utf-8")

    assert load_document(document) == content


def test_load_document_rejects_unsupported_files(tmp_path: Path) -> None:
    document = tmp_path / "support.csv"
    document.write_text("unsupported", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported document type: .csv"):
        load_document(document)


def test_load_document_reports_missing_files(tmp_path: Path) -> None:
    missing_document = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError, match="Document not found"):
        load_document(missing_document)
