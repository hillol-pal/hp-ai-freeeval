"""Whether output complies with a required JSON object schema."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from freeeval.metrics.base import RootMetric


def _complies(answer: str, schema: Mapping[str, Any]) -> bool:
    try:
        payload = json.loads(answer)
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, dict):
        return False
    required = schema.get("required", [])
    if not isinstance(required, Sequence) or isinstance(required, (str, bytes)):
        raise ValueError("schema required must be a list of field names")
    return all(isinstance(name, str) and name in payload for name in required)


class FormatComplianceRate(RootMetric):
    """Share of answers that are JSON objects containing the schema's required fields."""

    def __init__(self, threshold: float) -> None:
        super().__init__(name="format_compliance_rate", threshold=threshold)
        self.reasoning = ""

    def evaluate(
        self,
        answers: Sequence[str],
        schema: Mapping[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> float:
        if not answers:
            self.reasoning = "No answers were supplied."
            return 0.0
        compliant = sum(1 for answer in answers if _complies(answer, schema))
        score = compliant / len(answers)
        self.reasoning = f"{compliant} of {len(answers)} answers match the required format."
        return score
