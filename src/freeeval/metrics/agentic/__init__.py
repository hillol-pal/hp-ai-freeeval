"""AI agent metrics and the evaluation that runs a list of them."""

from freeeval.metrics.agentic.evaluation import (
    AGENT_METRIC_TYPES,
    AgentEvaluation,
    TraceStep,
    build_agent_metric,
)
from freeeval.metrics.agentic.task_reliability import TaskReliability
from freeeval.metrics.agentic.task_success_rate import TaskSuccessRate
from freeeval.metrics.agentic.tool_call_accuracy import ToolCallAccuracy

AGENT_METRICS: dict[str, type] = {
    "task_success_rate": TaskSuccessRate,
    "tool_call_accuracy": ToolCallAccuracy,
    "task_reliability": TaskReliability,
}

__all__ = [
    "AGENT_METRIC_TYPES",
    "AGENT_METRICS",
    "AgentEvaluation",
    "TaskReliability",
    "TaskSuccessRate",
    "ToolCallAccuracy",
    "TraceStep",
    "build_agent_metric",
]
