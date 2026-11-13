"""Prompt evaluation requests."""

from __future__ import annotations

from data_generation.sample import Sample


def samples() -> tuple[Sample, ...]:
    return (
        Sample(
            category="prompt",
            name="relevant_answer",
            body={
                "prompt": "capital of France",
                "answer": "Paris is the capital of France",
                "metrics": [
                    {"name": "answer_relevancy", "threshold": 0.5},
                    {"name": "specificity", "threshold": 0.5},
                ],
            },
            expected_results={"answer_relevancy": "pass", "specificity": "pass"},
        ),
        Sample(
            category="prompt",
            name="long_answer",
            body={
                "prompt": "hello",
                "answer": "hello there friend extra",
                "metrics": [
                    {"name": "conciseness", "threshold": 0.9},
                    {"name": "answer_relevancy", "threshold": 0.5},
                ],
            },
            expected_results={"conciseness": "fail", "answer_relevancy": "pass"},
        ),
    )
