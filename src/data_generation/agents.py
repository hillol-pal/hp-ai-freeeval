"""Agent evaluation requests."""

from __future__ import annotations

from data_generation.sample import Sample

_MATCHING_TOOL = {
    "kind": "tool",
    "name": "search",
    "arguments": {"q": "capital of France"},
    "expected_name": "search",
    "expected_arguments": {"q": "capital of France"},
}


def samples() -> tuple[Sample, ...]:
    return (
        Sample(
            category="agent",
            name="successful_search",
            body={
                "input": "Find the capital of France",
                "actual_output": "Paris",
                "execution_trace": [_MATCHING_TOOL],
                "metrics": [
                    {"name": "task_success_rate", "threshold": 0.5},
                    {"name": "tool_call_accuracy", "threshold": 0.5},
                ],
                "metadata": {"source": "data_generation", "sample": "successful_search"},
            },
            expected_results={"task_success_rate": "pass", "tool_call_accuracy": "pass"},
        ),
        Sample(
            category="agent",
            name="tool_error",
            body={
                "input": "Find the capital of France",
                "actual_output": "Paris",
                "execution_trace": [{**_MATCHING_TOOL, "error": "timeout"}],
                "metrics": [
                    {"name": "task_success_rate", "threshold": 0.5},
                    {"name": "tool_call_accuracy", "threshold": 0.5},
                ],
                "metadata": {"source": "data_generation", "sample": "tool_error"},
            },
            expected_results={"task_success_rate": "fail", "tool_call_accuracy": "pass"},
        ),
        Sample(
            category="agent",
            name="wrong_tool",
            body={
                "input": "Find the capital of France",
                "actual_output": "Paris",
                "execution_trace": [
                    {
                        "kind": "tool",
                        "name": "browse",
                        "arguments": {},
                        "expected_name": "search",
                        "expected_arguments": {},
                    }
                ],
                "metrics": [{"name": "tool_call_accuracy", "threshold": 0.5}],
                "metadata": {"source": "data_generation", "sample": "wrong_tool"},
            },
            expected_results={"tool_call_accuracy": "fail"},
        ),
    )
