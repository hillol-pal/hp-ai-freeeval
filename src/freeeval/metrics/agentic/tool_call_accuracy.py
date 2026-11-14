"""Correctness of tool selection and input arguments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from freeeval.metrics.base import RootMetric


class ToolCallAccuracy(RootMetric):
    """Share of tool calls whose name and arguments match the expected call."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="tool_call_accuracy", threshold=threshold)
        self.reasoning = ""

    def evaluate(self, calls: Sequence[Mapping[str, Any]], *args: Any, **kwargs: Any) -> float:
        if not calls:
            self.reasoning = "No tool calls were supplied."
            return 0.0
        correct = 0
        for call in calls:
            name_matches = call.get("actual_name") == call.get("expected_name")
            arguments_match = call.get("actual_arguments") == call.get("expected_arguments")
            if name_matches and arguments_match:
                correct += 1
        score = correct / len(calls)
        self.reasoning = f"{correct} of {len(calls)} tool calls select the right tool and arguments."
        return score
