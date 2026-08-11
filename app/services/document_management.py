from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings
from app.services.vector_store import VectorStore
from app.utils.file_utils import validate_document_filename


class DocumentNotFoundError(FileNotFoundError):
    """Raised when a document has no uploaded file or indexed chunks."""


@dataclass(frozen=True)
class IndexedDocument:
    filename: str
    chunk_count: int
    size_bytes: int | None = None
    modified_at: datetime | None = None
    download_available: bool = False


class DocumentManagementService:
    def __init__(self, upload_dir: str | Path, vector_store: VectorStore) -> None:
        self._upload_dir = Path(upload_dir)
        self._vector_store = vector_store

    def list_documents(self) -> list[IndexedDocument]:
        documents = []
        for source, chunk_count in sorted(self._vector_store.source_counts().items()):
            try:
                document_path = self.get_document_path(source)
                file_stat = document_path.stat()
            except (DocumentNotFoundError, OSError, ValueError):
                documents.append(
                    IndexedDocument(filename=source, chunk_count=chunk_count)
                )
                continue

            documents.append(
                IndexedDocument(
                    filename=source,
                    chunk_count=chunk_count,
                    size_bytes=file_stat.st_size,
                    modified_at=datetime.fromtimestamp(file_stat.st_mtime, tz=UTC),
                    download_available=True,
                )
            )

        return documents

    def get_document_path(self, filename: str) -> Path:
        safe_filename = validate_document_filename(filename)
        upload_root = self._upload_dir.resolve()
        upload_path = (upload_root / safe_filename).resolve()
        if upload_path.parent != upload_root:
            raise ValueError("Document path must stay inside the upload directory")
        if not upload_path.is_file():
            raise DocumentNotFoundError(f"Document not found: {safe_filename}")
        return upload_path

    def delete_document(self, filename: str) -> None:
        safe_filename = validate_document_filename(filename)
        upload_path = self._upload_dir / safe_filename
        file_exists = upload_path.is_file()
        deleted_chunks = self._vector_store.delete_source(safe_filename)

        if not file_exists and deleted_chunks == 0:
            raise DocumentNotFoundError(f"Document not found: {safe_filename}")

        if file_exists:
            upload_path.unlink()


@lru_cache
def get_document_management_service() -> DocumentManagementService:
    settings = get_settings()
    vector_store = VectorStore(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
    )
    return DocumentManagementService(settings.upload_dir, vector_store)
