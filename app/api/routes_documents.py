from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.schemas.document import DocumentUploadResponse
from app.services.embeddings import EmbeddingServiceError
from app.services.ingestion_service import (
    DocumentIngestionError,
    IngestionService,
    get_ingestion_service,
)
from app.utils.file_utils import save_upload_file

router = APIRouter(prefix="/documents", tags=["documents"])


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
        saved_path = await save_upload_file(file, settings.upload_dir)
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
