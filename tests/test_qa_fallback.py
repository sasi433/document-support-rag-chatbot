from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.embeddings import EmbeddingService
from app.services.qa_service import FALLBACK_ANSWER, QAService
from app.services.vector_store import VectorStore


def make_service(tmp_path: Path) -> tuple[QAService, Mock, VectorStore, Mock]:
    embedding_service = Mock(spec=EmbeddingService)
    vector_store = VectorStore(tmp_path / "chroma", "fallback_tests")
    client = Mock()
    service = QAService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        api_key=None,
        model="test-chat-model",
        client=client,
    )
    return service, embedding_service, vector_store, client


def test_no_indexed_documents_returns_fallback(tmp_path: Path) -> None:
    service, embedding_service, _, client = make_service(tmp_path)

    result = service.answer_question("What is the refund policy?")

    assert result.answer == FALLBACK_ANSWER
    assert result.sources == []
    embedding_service.embed_text.assert_not_called()
    client.responses.create.assert_not_called()


def test_unsupported_question_returns_fallback_without_sources(
    tmp_path: Path,
) -> None:
    service, embedding_service, vector_store, client = make_service(tmp_path)
    vector_store.add_documents(
        ids=["company.txt:0"],
        documents=["Standard support is available from 08:00 to 18:00 CET."],
        embeddings=[[1.0, 0.0]],
        metadatas=[{"source": "company.txt", "chunk_index": 0}],
    )
    embedding_service.embed_text.return_value = [1.0, 0.0]
    client.responses.create.return_value = SimpleNamespace(
        output_text=FALLBACK_ANSWER
    )

    result = service.answer_question(
        "What is the CEO's personal phone number?"
    )

    assert result.answer == FALLBACK_ANSWER
    assert result.sources == []

    request = client.responses.create.call_args.kwargs
    assert "What is the CEO's personal phone number?" in request["input"]
    assert "Standard support is available" in request["input"]


def test_supported_question_returns_answer_and_source(tmp_path: Path) -> None:
    service, embedding_service, vector_store, client = make_service(tmp_path)
    vector_store.add_documents(
        ids=["company_faq.md:0"],
        documents=["Refund requests must be submitted within 14 calendar days."],
        embeddings=[[1.0, 0.0]],
        metadatas=[{"source": "company_faq.md", "chunk_index": 0}],
    )
    embedding_service.embed_text.return_value = [1.0, 0.0]
    client.responses.create.return_value = SimpleNamespace(
        output_text="Refund requests must be submitted within 14 calendar days."
    )

    result = service.answer_question("What is the refund policy?")

    assert result.answer == (
        "Refund requests must be submitted within 14 calendar days."
    )
    assert result.sources == ["company_faq.md"]
