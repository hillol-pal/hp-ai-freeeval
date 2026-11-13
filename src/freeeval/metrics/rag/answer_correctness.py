"""Factual accuracy of the final answer against ground truth."""

from __future__ import annotations

from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.text import token_f1


class AnswerCorrectness(RootMetric):
    """Token F1 of the answer against the ground-truth answer."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="answer_correctness", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, answer: str, expected: str, *args: Any, **kwargs: Any) -> float:
        score = token_f1(answer, expected)
        self.reasoning = f"Token overlap with the ground truth is {score:.2f}."
        return score
