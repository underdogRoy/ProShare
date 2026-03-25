"""Summarization pipeline and optional extractive baseline."""
from ai.app.services.chunking import split_into_chunks
from ai.app.services.prompts import summary_prompt


def extractive_summary(text: str) -> str:
    sentences = [x.strip() for x in text.split(".") if x.strip()]
    top = sentences[:6]
    tldr = ". ".join(top[:2]) + "."
    bullets = "\n".join([f"- {s[:180]}" for s in top[:6]])
    return f"TLDR: {tldr}\nTakeaways:\n{bullets}"


def abstractive_summary(text: str) -> str:
    _ = summary_prompt(text)
    return extractive_summary(text)


def summarize_article(content: str, method: str = "abstractive") -> str:
    chunks = split_into_chunks(content)
    if len(chunks) == 1:
        return abstractive_summary(content) if method == "abstractive" else extractive_summary(content)
    part_summaries = [abstractive_summary(chunk) for chunk in chunks]
    merged = "\n".join(part_summaries)
    return abstractive_summary(merged)
