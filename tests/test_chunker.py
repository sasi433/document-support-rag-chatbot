import pytest

from app.services.chunker import DocumentChunk, chunk_document


def test_chunk_document_returns_one_chunk_for_short_text() -> None:
    chunks = chunk_document("Short support document.", "support.txt")

    assert chunks == [
        DocumentChunk(
            text="Short support document.",
            source="support.txt",
            chunk_index=0,
        )
    ]


def test_chunk_document_creates_overlapping_chunks() -> None:
    chunks = chunk_document(
        text="abcdefghij",
        source="support.txt",
        chunk_size=4,
        overlap=1,
    )

    assert [chunk.text for chunk in chunks] == ["abcd", "defg", "ghij"]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert all(chunk.source == "support.txt" for chunk in chunks)
    assert chunks[0].text[-1:] == chunks[1].text[:1]
    assert chunks[1].text[-1:] == chunks[2].text[:1]


@pytest.mark.parametrize("text", ["", "  \n\t  "])
def test_chunk_document_returns_no_chunks_for_empty_text(text: str) -> None:
    assert chunk_document(text, "support.txt") == []


@pytest.mark.parametrize(
    ("chunk_size", "overlap", "message"),
    [
        (0, 0, "Chunk size must be greater than zero"),
        (10, -1, "Chunk overlap cannot be negative"),
        (10, 10, "Chunk overlap must be smaller than chunk size"),
        (10, 11, "Chunk overlap must be smaller than chunk size"),
    ],
)
def test_chunk_document_rejects_invalid_sizes(
    chunk_size: int,
    overlap: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        chunk_document(
            text="Support content",
            source="support.txt",
            chunk_size=chunk_size,
            overlap=overlap,
        )


def test_chunk_document_rejects_empty_source() -> None:
    with pytest.raises(ValueError, match="Source cannot be empty"):
        chunk_document("Support content", "  ")
