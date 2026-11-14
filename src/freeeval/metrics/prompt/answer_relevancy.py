"""Share of prompt content words that also appear in the answer."""

from __future__ import annotations

from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.prompt.text import content_tokens


class AnswerRelevancy(RootMetric):
    """Share of prompt content words that also appear in the answer."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="answer_relevancy", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, prompt: str, answer: str, *args: Any, **kwargs: Any) -> float:
        prompt_terms = list(dict.fromkeys(content_tokens(prompt)))
        answer_terms = set(content_tokens(answer))
        if not prompt_terms:
            self.reasoning = "The prompt has no content words to compare with the answer."
            return 0.0
        matched = [term for term in prompt_terms if term in answer_terms]
        score = len(matched) / len(prompt_terms)
        self.reasoning = (
            f"{len(matched)} of {len(prompt_terms)} prompt content words "
            "appear in the answer."
        )
        return score
