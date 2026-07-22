from pathlib import Path

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".md", ".pdf", ".txt"}


def load_document(file_path: str | Path) -> str:
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {path}")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {path.suffix or 'none'}")

    if extension == ".pdf":
        return _load_pdf(path)

    return path.read_text(encoding="utf-8")


def _load_pdf(path: Path) -> str:
    pages = (page.extract_text() for page in PdfReader(path).pages)
    return "\n\n".join(text.strip() for text in pages if text and text.strip())
