from pathlib import Path

from fastapi import UploadFile

SUPPORTED_DOCUMENT_EXTENSIONS = {".md", ".pdf", ".txt"}
UPLOAD_CHUNK_SIZE = 1024 * 1024


class UploadTooLargeError(ValueError):
    """Raised when an uploaded document exceeds the configured size limit."""


async def save_upload_file(
    upload_file: UploadFile,
    upload_dir: Path,
    max_upload_size_bytes: int,
) -> Path:
    destination: Path | None = None
    file_created = False
    upload_complete = False

    try:
        filename = validate_document_filename(upload_file.filename)
        upload_path = Path(upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)
        destination = upload_path / filename

        with destination.open("xb") as output_file:
            file_created = True
            uploaded_size = 0

            while content := await upload_file.read(UPLOAD_CHUNK_SIZE):
                uploaded_size += len(content)
                if uploaded_size > max_upload_size_bytes:
                    raise UploadTooLargeError(
                        "Document exceeds maximum upload size of "
                        f"{format_file_size(max_upload_size_bytes)}"
                    )
                output_file.write(content)

        upload_complete = True
        return destination
    finally:
        await upload_file.close()

        if file_created and not upload_complete and destination is not None:
            destination.unlink(missing_ok=True)


def format_file_size(size_bytes: int) -> str:
    megabyte = 1024 * 1024
    if size_bytes >= megabyte and size_bytes % megabyte == 0:
        return f"{size_bytes // megabyte} MB"
    return f"{size_bytes} bytes"


def validate_document_filename(filename: str | None) -> str:
    if not filename or not filename.strip():
        raise ValueError("Document filename cannot be empty")

    normalized_filename = filename.replace("\\", "/")
    safe_filename = Path(normalized_filename).name

    if safe_filename != normalized_filename:
        raise ValueError("Document filename must not include a path")

    if Path(safe_filename).suffix.lower() not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {Path(safe_filename).suffix or 'none'}")

    return safe_filename
