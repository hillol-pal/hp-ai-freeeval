"""Whether retrieval captures the information needed for the answer."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.text import claim_supported, content_tokens, sentences


class ContextRecall(RootMetric):
    """Share of ground-truth statements covered by the retrieved context."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="context_recall", threshold=threshold)
        self.reasoning = ""

    def evaluate(
        self,
        ground_truth: str,
        contexts: Sequence[str],
        *args: Any,
        **kwargs: Any,
    ) -> float:
        statements = sentences(ground_truth)
        if not statements:
            self.reasoning = "The ground truth has no statements to recall."
            return 0.0
        context_terms = {term for context in contexts for term in content_tokens(context)}
        recalled = sum(1 for statement in statements if claim_supported(statement, context_terms))
        score = recalled / len(statements)
        self.reasoning = f"{recalled} of {len(statements)} ground-truth statements are in the context."
        return score
