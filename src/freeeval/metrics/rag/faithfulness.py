"""Whether generated claims are supported by retrieved context."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.text import claim_supported, content_tokens, sentences


class Faithfulness(RootMetric):
    """Share of answer sentences whose content words are covered by the context."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="faithfulness", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, answer: str, contexts: Sequence[str], *args: Any, **kwargs: Any) -> float:
        claims = sentences(answer)
        if not claims:
            self.reasoning = "The answer has no claims to support."
            return 0.0
        context_terms = {term for context in contexts for term in content_tokens(context)}
        supported = sum(1 for claim in claims if claim_supported(claim, context_terms))
        score = supported / len(claims)
        self.reasoning = f"{supported} of {len(claims)} claims are supported by the context."
        return score
