from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai import OpenAIError

from app.services.embeddings import EmbeddingService, EmbeddingServiceError
from app.services.qa_service import (
    FALLBACK_ANSWER,
    QAService,
    QAServiceError,
)
from app.services.vector_store import VectorSearchResult, VectorStore


def make_service(
    embedding_service: Mock,
    vector_store: Mock,
    client: Mock,
) -> QAService:
    return QAService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        api_key=None,
        model="test-chat-model",
        client=client,
    )


def test_answer_question_uses_retrieved_context() -> None:
    embedding_service = Mock(spec=EmbeddingService)
    embedding_service.embed_text.return_value = [0.1, 0.2]

    vector_store = Mock(spec=VectorStore)
    vector_store.count.return_value = 2
    vector_store.search.return_value = [
        VectorSearchResult(
            record_id="billing.txt:0",
            document="Refunds are available within 30 days.",
            metadata={"source": "billing.txt", "chunk_index": 0},
            distance=0.1,
        ),
        VectorSearchResult(
            record_id="billing.txt:1",
            document="Contact support with the invoice number.",
            metadata={"source": "billing.txt", "chunk_index": 1},
            distance=0.2,
        ),
    ]

    client = Mock()
    client.responses.create.return_value = SimpleNamespace(
        output_text="Refunds are available within 30 days."
    )

    result = make_service(embedding_service, vector_store, client).answer_question(
        "What is the refund policy?"
    )

    assert result.answer == "Refunds are available within 30 days."
    assert result.sources == ["billing.txt"]
    embedding_service.embed_text.assert_called_once_with(
        "What is the refund policy?"
    )
    vector_store.search.assert_called_once_with([0.1, 0.2], limit=3)

    request = client.responses.create.call_args.kwargs
    assert request["model"] == "test-chat-model"
    assert "What is the refund policy?" in request["input"]
    assert "Refunds are available within 30 days." in request["input"]
    assert "Contact support with the invoice number." in request["input"]
    assert "only the provided document context" in request["instructions"]
    assert FALLBACK_ANSWER in request["instructions"]


def test_answer_question_returns_fallback_without_document_context() -> None:
    embedding_service = Mock(spec=EmbeddingService)
    vector_store = Mock(spec=VectorStore)
    vector_store.count.return_value = 0
    client = Mock()

    result = make_service(embedding_service, vector_store, client).answer_question(
        "What is the refund policy?"
    )

    assert result.answer == FALLBACK_ANSWER
    assert result.sources == []
    embedding_service.embed_text.assert_not_called()
    vector_store.search.assert_not_called()
    client.responses.create.assert_not_called()


def test_answer_question_returns_fallback_without_sources() -> None:
    embedding_service = Mock(spec=EmbeddingService)
    embedding_service.embed_text.return_value = [0.1, 0.2]
    vector_store = Mock(spec=VectorStore)
    vector_store.count.return_value = 1
    vector_store.search.return_value = [
        VectorSearchResult(
            record_id="company.txt:0",
            document="The office opens at 9 AM.",
            metadata={"source": "company.txt", "chunk_index": 0},
            distance=0.5,
        )
    ]
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(
        output_text="I DON'T KNOW BASED ON THE PROVIDED DOCUMENTS"
    )

    result = make_service(embedding_service, vector_store, client).answer_question(
        "What is the CEO's personal phone number?"
    )

    assert result.answer == FALLBACK_ANSWER
    assert result.sources == []


def test_answer_question_wraps_embedding_errors() -> None:
    embedding_service = Mock(spec=EmbeddingService)
    embedding_service.embed_text.side_effect = EmbeddingServiceError(
        "Failed to generate embeddings"
    )

    vector_store = Mock(spec=VectorStore)
    vector_store.count.return_value = 1

    with pytest.raises(QAServiceError, match="Failed to answer question"):
        make_service(embedding_service, vector_store, Mock()).answer_question(
            "What is the refund policy?"
        )


def test_answer_question_wraps_answer_provider_errors() -> None:
    embedding_service = Mock(spec=EmbeddingService)
    embedding_service.embed_text.return_value = [0.1, 0.2]
    vector_store = Mock(spec=VectorStore)
    vector_store.count.return_value = 1
    vector_store.search.return_value = [
        VectorSearchResult(
            record_id="billing.txt:0",
            document="Refunds are available within 30 days.",
            metadata={"source": "billing.txt", "chunk_index": 0},
            distance=0.1,
        )
    ]
    client = Mock()
    client.responses.create.side_effect = OpenAIError("Provider unavailable")

    with pytest.raises(QAServiceError, match="Failed to answer question"):
        make_service(embedding_service, vector_store, client).answer_question(
            "What is the refund policy?"
        )


def test_answer_question_rejects_empty_provider_output() -> None:
    embedding_service = Mock(spec=EmbeddingService)
    embedding_service.embed_text.return_value = [0.1, 0.2]
    vector_store = Mock(spec=VectorStore)
    vector_store.count.return_value = 1
    vector_store.search.return_value = [
        VectorSearchResult(
            record_id="billing.txt:0",
            document="Refunds are available within 30 days.",
            metadata={"source": "billing.txt", "chunk_index": 0},
            distance=0.1,
        )
    ]
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(output_text="  ")

    with pytest.raises(QAServiceError, match="returned empty text"):
        make_service(embedding_service, vector_store, client).answer_question(
            "What is the refund policy?"
        )


def test_answer_question_rejects_empty_question() -> None:
    with pytest.raises(ValueError, match="Question cannot be empty"):
        make_service(Mock(), Mock(), Mock()).answer_question("  ")
