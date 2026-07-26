from fastapi import APIRouter, Depends, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.qa_service import (
    NoDocumentContextError,
    QAService,
    QAServiceError,
    get_qa_service,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    qa_service: QAService = Depends(get_qa_service),
) -> ChatResponse:
    try:
        result = qa_service.answer_question(request.question)
    except NoDocumentContextError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QAServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(answer=result.answer, sources=result.sources)
