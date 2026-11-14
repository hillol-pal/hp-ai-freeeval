"""Share of answer words that are content words rather than stopwords."""

from __future__ import annotations

from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.prompt.text import content_tokens, tokens


class Specificity(RootMetric):
    """Share of answer words that are content words rather than stopwords."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="specificity", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, prompt: str, answer: str, *args: Any, **kwargs: Any) -> float:
        answer_words = tokens(answer)
        if not answer_words:
            self.reasoning = "The answer has no words."
            return 0.0
        content_words = content_tokens(answer)
        score = len(content_words) / len(answer_words)
        self.reasoning = (
            f"{len(content_words)} of {len(answer_words)} answer words are content words."
        )
        return score
