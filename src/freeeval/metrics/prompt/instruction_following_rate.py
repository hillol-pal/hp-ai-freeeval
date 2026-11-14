"""Whether a response complies with prompt instructions and constraints."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from freeeval.metrics.base import RootMetric


class InstructionFollowingRate(RootMetric):
    """Share of required instructions that appear in the response."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="instruction_following_rate", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, answer: str, constraints: Sequence[str], *args: Any, **kwargs: Any) -> float:
        if not constraints:
            self.reasoning = "No instructions were supplied."
            return 0.0
        followed = sum(1 for constraint in constraints if constraint.casefold() in answer.casefold())
        score = followed / len(constraints)
        self.reasoning = f"{followed} of {len(constraints)} instructions are followed."
        return score
