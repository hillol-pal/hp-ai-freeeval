"""RAG evaluation requests."""

from __future__ import annotations

from data_generation.sample import Sample


def samples() -> tuple[Sample, ...]:
    return (
        Sample(
            category="rag",
            name="grounded_answer",
            body={
                "query": "capital of France",
                "actual_response": "Paris is the capital of France",
                "retrieved_contexts": ["Paris is the capital of France."],
                "metrics": [
                    {"name": "faithfulness", "threshold": 0.5},
                    {"name": "answer_relevancy", "threshold": 0.5},
                ],
                "metadata": {"source": "data_generation", "sample": "grounded_answer"},
            },
            expected_results={"faithfulness": "pass", "answer_relevancy": "pass"},
        ),
        Sample(
            category="rag",
            name="unsupported_answer",
            body={
                "query": "capital of France",
                "actual_response": "Berlin is a city",
                "retrieved_contexts": ["Paris is the capital of France."],
                "metrics": [
                    {"name": "faithfulness", "threshold": 0.5},
                    {"name": "answer_relevancy", "threshold": 0.5},
                ],
                "metadata": {"source": "data_generation", "sample": "unsupported_answer"},
            },
            expected_results={"faithfulness": "fail", "answer_relevancy": "fail"},
        ),
    )
