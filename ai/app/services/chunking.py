"""Chunking logic for long articles."""


def split_into_chunks(content: str, size: int = 1500, overlap: int = 150) -> list[str]:
    words = content.split()
    if len(words) <= 2000:
        return [content]
    chunks: list[str] = []
    index = 0
    while index < len(words):
        end = min(index + size, len(words))
        chunks.append(" ".join(words[index:end]))
        if end == len(words):
            break
        index = end - overlap
    return chunks
