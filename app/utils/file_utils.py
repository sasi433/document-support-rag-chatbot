from pathlib import Path

from fastapi import UploadFile

SUPPORTED_DOCUMENT_EXTENSIONS = {".md", ".pdf", ".txt"}
UPLOAD_CHUNK_SIZE = 1024 * 1024


async def save_upload_file(upload_file: UploadFile, upload_dir: Path) -> Path:
    destination: Path | None = None
    file_created = False
    upload_complete = False

    try:
        filename = _validate_filename(upload_file.filename)
        upload_path = Path(upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)
        destination = upload_path / filename

        with destination.open("xb") as output_file:
            file_created = True

            while content := await upload_file.read(UPLOAD_CHUNK_SIZE):
                output_file.write(content)

        upload_complete = True
        return destination
    finally:
        await upload_file.close()

        if file_created and not upload_complete and destination is not None:
            destination.unlink(missing_ok=True)


def _validate_filename(filename: str | None) -> str:
    if not filename or not filename.strip():
        raise ValueError("Document filename cannot be empty")

    normalized_filename = filename.replace("\\", "/")
    safe_filename = Path(normalized_filename).name

    if safe_filename != normalized_filename:
        raise ValueError("Document filename must not include a path")

    if Path(safe_filename).suffix.lower() not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {Path(safe_filename).suffix or 'none'}")

    return safe_filename
