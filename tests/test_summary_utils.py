import os

# Set before any service import so module-level code uses SQLite/memory backends
os.environ.setdefault("SUMMARY_DB_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "memory://local")
os.environ.setdefault("ANTHROPIC_API_KEY", "")

from services.summary.app.main import chunk_text, strip_html, summarize_text  # noqa: E402


# --- strip_html ---

def test_strip_html_removes_block_tags():
    assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"


def test_strip_html_removes_img_tags():
    result = strip_html('<img src="data:image/png;base64,abc"> caption')
    assert "img" not in result
    assert "caption" in result


def test_strip_html_decodes_entities():
    assert strip_html("&amp; &lt; &gt;") == "& < >"


def test_strip_html_collapses_whitespace():
    assert strip_html("<p>  foo   bar  </p>") == "foo bar"


def test_strip_html_empty_input():
    assert strip_html("") == ""


def test_strip_html_plain_text_unchanged():
    assert strip_html("plain text") == "plain text"


def test_strip_html_nested_tags():
    assert strip_html("<div><span><em>deep</em></span></div>") == "deep"


# --- chunk_text ---

def test_chunk_text_short_stays_single_chunk():
    chunks = chunk_text("short text", chunk_size=1000)
    assert len(chunks) == 1
    assert chunks[0] == "short text"


def test_chunk_text_splits_long_text():
    long_text = " ".join(["word"] * 2000)
    chunks = chunk_text(long_text, chunk_size=100)
    assert len(chunks) > 1


def test_chunk_text_reassembled_contains_all_words():
    words = ["word"] * 500
    long_text = " ".join(words)
    chunks = chunk_text(long_text, chunk_size=200)
    reassembled = " ".join(chunks)
    assert reassembled == long_text


def test_chunk_text_empty():
    assert chunk_text("") == []


def test_chunk_text_single_word():
    chunks = chunk_text("hello", chunk_size=1000)
    assert chunks == ["hello"]


# --- summarize_text (fallback mode, no API key) ---

def test_summarize_text_empty_returns_no_content():
    tldr, takeaways = summarize_text("")
    assert tldr == "No content."
    assert takeaways == []


def test_summarize_text_html_only_returns_no_content():
    tldr, takeaways = summarize_text("<p></p>")
    assert tldr == "No content."


def test_summarize_text_fallback_returns_strings():
    content = "<p>Artificial intelligence is transforming the world. Machine learning enables new possibilities. Deep learning powers modern AI systems. Neural networks are the foundation of deep learning. AI research advances rapidly every year.</p>"
    tldr, takeaways = summarize_text(content)
    assert isinstance(tldr, str)
    assert len(tldr) > 0
    assert isinstance(takeaways, list)


def test_summarize_text_fallback_takeaways_are_strings():
    content = "<p>Artificial intelligence is a field of computer science. It involves machine learning and neural networks. Many industries are adopting AI solutions. Research continues to advance the field. Applications span healthcare, finance, and more.</p>"
    _, takeaways = summarize_text(content)
    for item in takeaways:
        assert isinstance(item, str)


def test_summarize_text_tldr_length_reasonable():
    content = "<p>This is a longer article about software engineering best practices. Testing is crucial. Code review helps catch bugs. Documentation ensures maintainability. Continuous integration speeds up delivery. Developers must communicate effectively.</p>"
    tldr, _ = summarize_text(content)
    assert len(tldr) <= 420  # fallback caps at 420 chars
