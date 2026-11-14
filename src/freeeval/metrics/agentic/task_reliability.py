"""Consistency of successful outcomes across repeated executions."""

from __future__ import annotations

import math
from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.counts import unit_rate


class TaskReliability(RootMetric):
    """pass^k: probability that k draws from the trials are all successful."""

    def __init__(self, threshold: float, k: int = 1) -> None:
        if k < 1:
            raise ValueError("k must be at least 1")
        super().__init__(name="task_reliability", threshold=threshold)
        self.k = k
        self.reasoning = ""

    def evaluate(
        self,
        successful: int,
        total: int,
        *args: Any,
        k: int | None = None,
        **kwargs: Any,
    ) -> float:
        repeats = self.k if k is None else k
        if repeats < 1:
            raise ValueError("k must be at least 1")
        unit_rate(successful, total, label="successful trials")
        if repeats > total or successful < repeats:
            score = 0.0
        else:
            score = math.comb(successful, repeats) / math.comb(total, repeats)
        self.reasoning = (
            f"{successful} of {total} repeated trials succeeded; "
            f"pass^{repeats} is {score:.2f}."
        )
        return score
