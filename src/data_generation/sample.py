"""A synthetic evaluation request and the verdicts it should produce."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Category = Literal["prompt", "code", "rag", "agent"]
Verdict = Literal["pass", "fail"]


@dataclass(frozen=True)
class Sample:
    """One request body plus the verdict expected for each scored metric.

    `body` is the JSON a client posts. `expected_results` maps a metric name to
    `pass` or `fail`. A code sample with an empty map has no `expected` output,
    so the code route returns no scores.
    """

    category: Category
    name: str
    body: dict[str, Any]
    expected_results: dict[str, Verdict]
