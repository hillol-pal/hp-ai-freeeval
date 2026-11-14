"""Frequency of fabricated or unsupported factual claims."""

from __future__ import annotations

from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.counts import unit_rate


class HallucinationRate(RootMetric):
    """Share of claims that are unsupported.

    The returned score is the share of supported claims, so a higher score
    means fewer hallucinations. The reasoning states the hallucination rate.
    """

    def __init__(self, threshold: float) -> None:
        super().__init__(name="hallucination_rate", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, unsupported: int, total: int, *args: Any, **kwargs: Any) -> float:
        rate = unit_rate(unsupported, total, label="unsupported claims")
        score = 1.0 - rate
        self.reasoning = f"{unsupported} of {total} claims are unsupported (rate {rate:.2f})."
        return score
