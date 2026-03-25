import hashlib
import re
from collections import Counter


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def source_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def summarize(content: str) -> tuple[str, list[str]]:
    sentences = _split_sentences(content)
    if not sentences:
        return "No content available.", []

    tldr = " ".join(sentences[:2])[:400]

    words = [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", content)]
    top_terms = [word for word, _ in Counter(words).most_common(5)]

    takeaways = []
    for idx, sentence in enumerate(sentences[:5], start=1):
        takeaway = sentence[:140]
        if takeaway:
            takeaways.append(f"{idx}. {takeaway}")

    if top_terms:
        takeaways.append("Keywords: " + ", ".join(top_terms))
    return tldr, takeaways
