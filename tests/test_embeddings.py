from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai import OpenAIError

from app.services.embeddings import EmbeddingService, EmbeddingServiceError


def make_service(client: Mock) -> EmbeddingService:
    return EmbeddingService(
        api_key=None,
        model="test-embedding-model",
        client=client,
    )


def test_embed_text_returns_vector() -> None:
    client = Mock()
    client.embeddings.create.return_value = SimpleNamespace(
        data=[SimpleNamespace(index=0, embedding=[0.1, 0.2, 0.3])]
    )

    embedding = make_service(client).embed_text("Reset the device")

    assert embedding == [0.1, 0.2, 0.3]
    client.embeddings.create.assert_called_once_with(
        model="test-embedding-model",
        input=["Reset the device"],
    )


def test_embed_texts_returns_vectors_in_input_order() -> None:
    client = Mock()
    client.embeddings.create.return_value = SimpleNamespace(
        data=[
            SimpleNamespace(index=1, embedding=[0.3, 0.4]),
            SimpleNamespace(index=0, embedding=[0.1, 0.2]),
        ]
    )

    embeddings = make_service(client).embed_texts(["First chunk", "Second chunk"])

    assert embeddings == [[0.1, 0.2], [0.3, 0.4]]


@pytest.mark.parametrize("texts", [[], [""], ["Valid text", "  "]])
def test_embed_texts_rejects_empty_input(texts: list[str]) -> None:
    client = Mock()

    with pytest.raises(ValueError):
        make_service(client).embed_texts(texts)

    client.embeddings.create.assert_not_called()


def test_embedding_service_requires_api_key_without_client() -> None:
    with pytest.raises(ValueError, match="OpenAI API key is required"):
        EmbeddingService(api_key=None, model="test-embedding-model")


def test_embedding_service_wraps_provider_errors() -> None:
    client = Mock()
    client.embeddings.create.side_effect = OpenAIError("Provider unavailable")

    with pytest.raises(
        EmbeddingServiceError,
        match="Failed to generate embeddings",
    ):
        make_service(client).embed_text("Reset the device")
