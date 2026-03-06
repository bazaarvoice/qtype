"""Tools module for {{ cookiecutter.project_name }}.

This module provides custom tools that can be used in QType flows.
Run the following to regenerate the QType tool definitions:

    qtype convert module {{ cookiecutter.__module }}.tools \\
        -o {{ cookiecutter.__slug }}.tools.qtype.yaml
"""

from pydantic import BaseModel


class TextAnalysisResult(BaseModel):
    """Result of analyzing a block of text."""

    word_count: int
    char_count: int
    sentence_count: int
    avg_word_length: float


def greet(name: str) -> str:
    """Greet a person by name.

    Args:
        name: The person's name to greet.

    Returns:
        A personalized greeting message.
    """
    return f"Hello, {name}! Welcome to {{ cookiecutter.project_name }}."


def analyze_text(text: str) -> TextAnalysisResult:
    """Analyze text and return statistics.

    Args:
        text: The text to analyze.

    Returns:
        TextAnalysisResult containing word count, character count,
        sentence count, and average word length.
    """
    words = text.split()
    sentences = [
        s.strip()
        for s in text.replace("!", ".").replace("?", ".").split(".")
        if s.strip()
    ]
    avg_word_length = (
        sum(len(w) for w in words) / len(words) if words else 0.0
    )
    return TextAnalysisResult(
        word_count=len(words),
        char_count=len(text),
        sentence_count=len(sentences),
        avg_word_length=round(avg_word_length, 2),
    )
