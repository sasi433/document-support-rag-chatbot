from dataclasses import dataclass
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


class DocumentManagementService:
    def __init__(self, upload_dir: str | Path, vector_store: VectorStore) -> None:
        self._upload_dir = Path(upload_dir)
        self._vector_store = vector_store

    def list_documents(self) -> list[IndexedDocument]:
        return [
            IndexedDocument(filename=source, chunk_count=chunk_count)
            for source, chunk_count in sorted(self._vector_store.source_counts().items())
        ]

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
