from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.schemas.document import (
    DocumentCapabilitiesResponse,
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentSummary,
    DocumentUploadResponse,
)
from app.services.document_management import (
    DocumentManagementService,
    DocumentNotFoundError,
    get_document_management_service,
)
from app.services.embeddings import EmbeddingServiceError
from app.services.ingestion_service import (
    DocumentIngestionError,
    IngestionService,
    get_ingestion_service,
)
from app.utils.file_utils import (
    SUPPORTED_DOCUMENT_EXTENSIONS,
    UploadTooLargeError,
    save_upload_file,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/capabilities", response_model=DocumentCapabilitiesResponse)
def get_document_capabilities() -> DocumentCapabilitiesResponse:
    settings = get_settings()
    return DocumentCapabilitiesResponse(
        supported_extensions=sorted(SUPPORTED_DOCUMENT_EXTENSIONS),
        max_upload_size_bytes=settings.max_upload_size_bytes,
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    document_service: DocumentManagementService = Depends(
        get_document_management_service
    ),
) -> DocumentListResponse:
    documents = document_service.list_documents()
    return DocumentListResponse(
        documents=[
            DocumentSummary(
                filename=document.filename,
                chunk_count=document.chunk_count,
            )
            for document in documents
        ]
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> DocumentUploadResponse:
    settings = get_settings()

    try:
        saved_path = await save_upload_file(
            file,
            settings.upload_dir,
            settings.max_upload_size_bytes,
        )
    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileExistsError as exc:
        filename = Path(file.filename or "document").name
        raise HTTPException(
            status_code=409,
            detail=f"Document already exists: {filename}",
        ) from exc

    try:
        ingestion_service.ingest_document(saved_path)
    except DocumentIngestionError as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EmbeddingServiceError as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception:
        saved_path.unlink(missing_ok=True)
        raise

    return DocumentUploadResponse(filename=saved_path.name, status="uploaded")


@router.delete("/{filename}", response_model=DocumentDeleteResponse)
def delete_document(
    filename: str,
    document_service: DocumentManagementService = Depends(
        get_document_management_service
    ),
) -> DocumentDeleteResponse:
    try:
        document_service.delete_document(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return DocumentDeleteResponse(filename=filename, status="deleted")
