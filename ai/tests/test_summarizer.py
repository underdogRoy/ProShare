from ai.app.services.summarizer import summarize_article


def test_summarizer_output_contains_required_sections() -> None:
    text = "Sentence one. Sentence two. Sentence three. Sentence four."
    result = summarize_article(text, "extractive")
    assert "TLDR:" in result
    assert "Takeaways:" in result
