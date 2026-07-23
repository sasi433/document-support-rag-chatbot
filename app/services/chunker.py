from dataclasses import dataclass

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    source: str
    chunk_index: int


def chunk_document(
    text: str,
    source: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero")

    if overlap < 0:
        raise ValueError("Chunk overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("Chunk overlap must be smaller than chunk size")

    source_name = source.strip()
    if not source_name:
        raise ValueError("Source cannot be empty")

    content = text.strip()
    if not content:
        return []

    chunks: list[DocumentChunk] = []
    step = chunk_size - overlap

    for start in range(0, len(content), step):
        chunk_text = content[start : start + chunk_size]
        chunks.append(
            DocumentChunk(
                text=chunk_text,
                source=source_name,
                chunk_index=len(chunks),
            )
        )

        if start + chunk_size >= len(content):
            break

    return chunks
