from ai.app.services.chunking import split_into_chunks


def test_chunking_short_text_single_chunk() -> None:
    content = "word " * 300
    chunks = split_into_chunks(content)
    assert len(chunks) == 1


def test_chunking_long_text_multiple_chunks() -> None:
    content = "word " * 3500
    chunks = split_into_chunks(content)
    assert len(chunks) >= 2
