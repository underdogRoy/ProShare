"""Prompt templates for LLM summarization."""


def summary_prompt(text: str) -> str:
    return (
        "Summarize the following professional article. Output format:\n"
        "TLDR: 2-3 sentences\nTakeaways:\n- 4-6 concise bullets\n\n"
        f"Article:\n{text}"
    )
