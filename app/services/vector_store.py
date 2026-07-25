from dataclasses import dataclass
from pathlib import Path

import chromadb

MetadataValue = str | int | float | bool
Metadata = dict[str, MetadataValue]


@dataclass(frozen=True)
class VectorSearchResult:
    record_id: str
    document: str
    metadata: Metadata
    distance: float


class VectorStore:
    def __init__(self, persist_dir: str | Path, collection_name: str) -> None:
        if not collection_name.strip():
            raise ValueError("Collection name cannot be empty")

        path = Path(persist_dir)
        path.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(path))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=None,
        )

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[Metadata],
    ) -> None:
        if not ids:
            raise ValueError("At least one document is required")

        if len({len(ids), len(documents), len(embeddings), len(metadatas)}) != 1:
            raise ValueError("IDs, documents, embeddings, and metadata must align")

        if any(not record_id.strip() for record_id in ids):
            raise ValueError("Document IDs cannot be empty")

        if any(not document.strip() for document in documents):
            raise ValueError("Documents cannot be empty")

        if any(not embedding for embedding in embeddings):
            raise ValueError("Embeddings cannot be empty")

        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[VectorSearchResult]:
        if not query_embedding:
            raise ValueError("Query embedding cannot be empty")

        if limit <= 0:
            raise ValueError("Search limit must be greater than zero")

        record_count = self._collection.count()
        if record_count == 0:
            return []

        response = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(limit, record_count),
            include=["documents", "metadatas", "distances"],
        )

        ids = response["ids"][0]
        documents = response["documents"][0] if response["documents"] else []
        metadatas = response["metadatas"][0] if response["metadatas"] else []
        distances = response["distances"][0] if response["distances"] else []

        return [
            VectorSearchResult(
                record_id=record_id,
                document=document,
                metadata=metadata,
                distance=distance,
            )
            for record_id, document, metadata, distance in zip(
                ids,
                documents,
                metadatas,
                distances,
            )
        ]

    def count(self) -> int:
        return self._collection.count()
