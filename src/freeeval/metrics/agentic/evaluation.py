"""Run one agent execution through a caller-supplied list of metrics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

from freeeval.metrics.agentic.task_success_rate import TaskSuccessRate
from freeeval.metrics.agentic.tool_call_accuracy import ToolCallAccuracy
from freeeval.metrics.base import RootMetric

AGENT_METRIC_TYPES: dict[str, type[RootMetric]] = {
    "task_success_rate": TaskSuccessRate,
    "tool_call_accuracy": ToolCallAccuracy,
}

Verdict = Literal["pass", "fail"]


@dataclass(frozen=True)
class TraceStep:
    """One recorded step. Tool accuracy reads name, arguments, and the expected call."""

    kind: str
    name: str
    arguments: dict[str, Any] | None = None
    expected_name: str | None = None
    expected_arguments: dict[str, Any] | None = None
    error: str | None = None


@dataclass(frozen=True)
class MetricVerdict:
    name: str
    result: Verdict
    reasoning: str


class AgentEvaluation:
    """Evaluate one input, output, and execution trace with each metric."""

    def __init__(self, metrics: list[RootMetric]) -> None:
        self.metrics = metrics

    def evaluate(
        self,
        task_input: str,
        actual_output: str,
        execution_trace: Sequence[TraceStep],
    ) -> list[MetricVerdict]:
        verdicts: list[MetricVerdict] = []
        for metric in self.metrics:
            score = float(_score(metric, task_input, actual_output, execution_trace))
            reasoning = getattr(metric, "reasoning", "") or (
                f"Score {score:.2f} compared with threshold {metric.threshold:.2f}."
            )
            verdicts.append(
                MetricVerdict(
                    name=metric.name,
                    result="pass" if score >= metric.threshold else "fail",
                    reasoning=reasoning,
                )
            )
        return verdicts


def build_agent_metric(name: str, threshold: float) -> RootMetric:
    return AGENT_METRIC_TYPES[name](threshold)


def _score(
    metric: RootMetric,
    task_input: str,
    actual_output: str,
    execution_trace: Sequence[TraceStep],
) -> float:
    if isinstance(metric, TaskSuccessRate):
        succeeded = bool(actual_output.strip()) and not any(step.error for step in execution_trace)
        score = metric.evaluate(1 if succeeded else 0, 1)
        outcome = "finished without a trace error" if succeeded else "recorded a trace error"
        metric.reasoning = f"{metric.reasoning} The task {task_input!r} {outcome}."
        return score
    if isinstance(metric, ToolCallAccuracy):
        return metric.evaluate(_tool_calls(execution_trace))
    raise ValueError(f"Unsupported agent metric: {metric.name}")


def _tool_calls(execution_trace: Sequence[TraceStep]) -> list[dict[str, Any]]:
    return [
        {
            "actual_name": step.name,
            "actual_arguments": step.arguments,
            "expected_name": step.expected_name,
            "expected_arguments": step.expected_arguments,
        }
        for step in execution_trace
        if step.kind == "tool"
    ]
