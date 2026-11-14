"""How closely the generated answer addresses the question."""

from __future__ import annotations

from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.text import content_tokens


class AnswerRelevancy(RootMetric):
    """Share of question content words that also appear in the answer."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="answer_relevancy", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, question: str, answer: str, *args: Any, **kwargs: Any) -> float:
        question_terms = list(dict.fromkeys(content_tokens(question)))
        answer_terms = set(content_tokens(answer))
        if not question_terms:
            self.reasoning = "The question has no content words to compare with the answer."
            return 0.0
        matched = [term for term in question_terms if term in answer_terms]
        score = len(matched) / len(question_terms)
        self.reasoning = (
            f"{len(matched)} of {len(question_terms)} question content words appear in the answer."
        )
        return score
