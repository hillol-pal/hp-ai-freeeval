"""Code evaluation requests.

The code route scores exact match of `output` and `expected`. It does not score
the code-generation metric classes.
"""

from __future__ import annotations

from data_generation.sample import Sample


def samples() -> tuple[Sample, ...]:
    return (
        Sample(
            category="code",
            name="matching_output",
            body={
                "cases": [
                    {
                        "id": "matching-output",
                        "code": "print(2 + 2)",
                        "output": "4",
                        "expected": "4",
                    }
                ]
            },
            expected_results={"exact_match": "pass"},
        ),
        Sample(
            category="code",
            name="different_output",
            body={
                "cases": [
                    {
                        "id": "different-output",
                        "code": "print(2 + 2)",
                        "output": "4",
                        "expected": "5",
                    }
                ]
            },
            expected_results={"exact_match": "fail"},
        ),
        Sample(
            category="code",
            name="no_expected_output",
            body={
                "cases": [
                    {
                        "id": "no-expected-output",
                        "code": "print(2 + 2)",
                        "output": "4",
                    }
                ]
            },
            expected_results={},
        ),
    )
