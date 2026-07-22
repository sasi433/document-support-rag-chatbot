from pathlib import Path

SUPPORTED_TEXT_EXTENSIONS = {".md", ".txt"}


def load_document(file_path: str | Path) -> str:
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {path}")

    if path.suffix.lower() not in SUPPORTED_TEXT_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {path.suffix or 'none'}")

    return path.read_text(encoding="utf-8")
