"""Relevance and ranking quality of retrieved documents."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from freeeval.metrics.base import RootMetric


class ContextPrecision(RootMetric):
    """Mean precision at each relevant document, in retrieval order."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="context_precision", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, relevant: Sequence[bool], *args: Any, **kwargs: Any) -> float:
        if not relevant or not any(relevant):
            self.reasoning = "No retrieved document is relevant."
            return 0.0
        precision_sum = 0.0
        relevant_count = 0
        for rank, is_relevant in enumerate(relevant, start=1):
            if is_relevant:
                relevant_count += 1
                precision_sum += relevant_count / rank
        score = precision_sum / relevant_count
        self.reasoning = (
            f"{relevant_count} of {len(relevant)} retrieved documents are relevant; "
            f"context precision is {score:.2f}."
        )
        return score
