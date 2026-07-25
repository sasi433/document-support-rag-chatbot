import pytest

from app.services.vector_store import VectorSearchResult, VectorStore


def test_vector_store_persists_documents(tmp_path) -> None:
    first_store = VectorStore(tmp_path, "test_documents")
    first_store.add_documents(
        ids=["manual-0"],
        documents=["Restart the device to apply the update."],
        embeddings=[[1.0, 0.0]],
        metadatas=[{"source": "manual.txt", "chunk_index": 0}],
    )

    second_store = VectorStore(tmp_path, "test_documents")

    assert second_store.count() == 1
    assert any(tmp_path.iterdir())


def test_vector_store_returns_nearest_document(tmp_path) -> None:
    store = VectorStore(tmp_path, "test_documents")
    store.add_documents(
        ids=["manual-0", "billing-0"],
        documents=["Restart the device.", "Invoices are issued monthly."],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
        metadatas=[
            {"source": "manual.txt", "chunk_index": 0},
            {"source": "billing.txt", "chunk_index": 0},
        ],
    )

    results = store.search([0.9, 0.1], limit=1)

    assert len(results) == 1
    assert isinstance(results[0], VectorSearchResult)
    assert results[0].record_id == "manual-0"
    assert results[0].document == "Restart the device."
    assert results[0].metadata == {"source": "manual.txt", "chunk_index": 0}
    assert results[0].distance >= 0


def test_vector_store_limits_results_to_available_documents(tmp_path) -> None:
    store = VectorStore(tmp_path, "test_documents")
    store.add_documents(
        ids=["manual-0"],
        documents=["Restart the device."],
        embeddings=[[1.0, 0.0]],
        metadatas=[{"source": "manual.txt", "chunk_index": 0}],
    )

    assert len(store.search([1.0, 0.0], limit=10)) == 1


def test_vector_store_returns_no_results_for_empty_collection(tmp_path) -> None:
    store = VectorStore(tmp_path, "test_documents")

    assert store.search([1.0, 0.0]) == []


def test_vector_store_rejects_misaligned_documents(tmp_path) -> None:
    store = VectorStore(tmp_path, "test_documents")

    with pytest.raises(ValueError, match="must align"):
        store.add_documents(
            ids=["manual-0"],
            documents=["First document", "Second document"],
            embeddings=[[1.0, 0.0]],
            metadatas=[{"source": "manual.txt"}],
        )


@pytest.mark.parametrize(
    ("query_embedding", "limit", "message"),
    [
        ([], 5, "Query embedding cannot be empty"),
        ([1.0, 0.0], 0, "Search limit must be greater than zero"),
    ],
)
def test_vector_store_rejects_invalid_search(
    tmp_path,
    query_embedding: list[float],
    limit: int,
    message: str,
) -> None:
    store = VectorStore(tmp_path, "test_documents")

    with pytest.raises(ValueError, match=message):
        store.search(query_embedding, limit)
