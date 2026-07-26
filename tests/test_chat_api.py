from collections.abc import Iterator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.qa_service import (
    AnswerResult,
    FALLBACK_ANSWER,
    QAService,
    QAServiceError,
    get_qa_service,
)


@pytest.fixture
def qa_service() -> Iterator[Mock]:
    service = Mock(spec=QAService)
    service.answer_question.return_value = AnswerResult(
        answer="Refunds are available within 30 days.",
        sources=["billing.txt"],
    )
    app.dependency_overrides[get_qa_service] = lambda: service

    yield service

    app.dependency_overrides.pop(get_qa_service, None)


@pytest.fixture
def client(qa_service: Mock) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_ask_question_returns_grounded_answer(
    client: TestClient,
    qa_service: Mock,
) -> None:
    response = client.post(
        "/chat/ask",
        json={"question": "What is the refund policy?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Refunds are available within 30 days.",
        "sources": ["billing.txt"],
    }
    qa_service.answer_question.assert_called_once_with(
        "What is the refund policy?"
    )


def test_ask_question_rejects_empty_question(
    client: TestClient,
    qa_service: Mock,
) -> None:
    response = client.post("/chat/ask", json={"question": "  "})

    assert response.status_code == 422
    qa_service.answer_question.assert_not_called()


def test_ask_question_returns_fallback_without_documents(
    client: TestClient,
    qa_service: Mock,
) -> None:
    qa_service.answer_question.return_value = AnswerResult(
        answer=FALLBACK_ANSWER,
        sources=[],
    )

    response = client.post(
        "/chat/ask",
        json={"question": "What is the refund policy?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": FALLBACK_ANSWER,
        "sources": [],
    }


def test_ask_question_returns_bad_gateway_for_provider_error(
    client: TestClient,
    qa_service: Mock,
) -> None:
    qa_service.answer_question.side_effect = QAServiceError(
        "Failed to answer question"
    )

    response = client.post(
        "/chat/ask",
        json={"question": "What is the refund policy?"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Failed to answer question"}
