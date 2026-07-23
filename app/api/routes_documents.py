from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.schemas.document import DocumentUploadResponse
from app.utils.file_utils import save_upload_file

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
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

    return DocumentUploadResponse(filename=saved_path.name, status="uploaded")
