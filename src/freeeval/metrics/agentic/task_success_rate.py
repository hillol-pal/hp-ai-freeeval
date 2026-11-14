"""Percentage of agent tasks successfully completed."""

from __future__ import annotations

from typing import Any

from freeeval.metrics.base import RootMetric
from freeeval.metrics.counts import unit_rate


class TaskSuccessRate(RootMetric):
    """Percentage of agent tasks that completed successfully."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="task_success_rate", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, successful: int, total: int, *args: Any, **kwargs: Any) -> float:
        score = unit_rate(successful, total, label="successful tasks")
        self.reasoning = f"{successful} of {total} tasks succeeded."
        return score
