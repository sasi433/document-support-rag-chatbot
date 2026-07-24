from openai import OpenAI, OpenAIError


class EmbeddingServiceError(RuntimeError):
    """Raised when the embedding provider cannot generate vectors."""


class EmbeddingService:
    def __init__(
        self,
        api_key: str | None,
        model: str,
        client: OpenAI | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("Embedding model cannot be empty")

        if client is None:
            if not api_key:
                raise ValueError("OpenAI API key is required")
            client = OpenAI(api_key=api_key)

        self._client = client
        self._model = model

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            raise ValueError("At least one text is required")

        if any(not text.strip() for text in texts):
            raise ValueError("Embedding text cannot be empty")

        try:
            response = self._client.embeddings.create(
                model=self._model,
                input=texts,
            )
        except OpenAIError as exc:
            raise EmbeddingServiceError("Failed to generate embeddings") from exc

        ordered_embeddings = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered_embeddings]
