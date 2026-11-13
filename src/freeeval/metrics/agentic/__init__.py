"""AI agent metrics."""

from freeeval.metrics.agentic.task_reliability import TaskReliability
from freeeval.metrics.agentic.task_success_rate import TaskSuccessRate
from freeeval.metrics.agentic.tool_call_accuracy import ToolCallAccuracy

AGENT_METRICS: dict[str, type] = {
    "task_success_rate": TaskSuccessRate,
    "tool_call_accuracy": ToolCallAccuracy,
    "task_reliability": TaskReliability,
}

__all__ = [
    "AGENT_METRICS",
    "TaskReliability",
    "TaskSuccessRate",
    "ToolCallAccuracy",
]
