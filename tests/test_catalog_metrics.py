import pytest

from freeeval.metrics.agentic import (
    TaskReliability,
    TaskSuccessRate,
    ToolCallAccuracy,
)
from freeeval.metrics.code import (
    Extensibility,
    Maintainability,
    Readability,
    Robustness,
    SecuredCode,
)
from freeeval.metrics.prompt import (
    AnswerCorrectness as PromptAnswerCorrectness,
    FormatComplianceRate,
    HallucinationRate,
    InstructionFollowingRate,
)
from freeeval.metrics.rag import (
    AnswerCorrectness as RagAnswerCorrectness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)


_CLEAN = "def add_numbers(left, right):\n    return left + right\n"
_GUARDED = "def load_path(path):\n    if not path:\n        raise ValueError('missing')\n    return path\n"


def test_code_generation_metrics_score_clear_code_higher() -> None:
    assert Maintainability(0.5).evaluate(_CLEAN) == pytest.approx(1.0)
    assert Readability(0.5).evaluate(_CLEAN) == pytest.approx(1.0)
    assert Extensibility(0.5).evaluate(_CLEAN) == pytest.approx(1.0)
    assert Robustness(0.5).evaluate(_GUARDED) == pytest.approx(1.0)
    assert Robustness(0.5).evaluate(_CLEAN) == pytest.approx(0.0)
    secured = SecuredCode(0.5)
    assert secured.evaluate(_CLEAN) == pytest.approx(1.0)
    unsafe = secured.evaluate("result = eval(payload)\n")
    assert unsafe < 1.0
    assert "eval" in secured.reasoning


def test_prompt_metrics() -> None:
    assert PromptAnswerCorrectness(0.5).evaluate("Paris", "Paris") == pytest.approx(1.0)
    assert PromptAnswerCorrectness(0.5).evaluate("Berlin", "Paris") == pytest.approx(0.0)
    followed = InstructionFollowingRate(0.5)
    assert followed.evaluate("Reply in JSON only", ["json", "yaml"]) == pytest.approx(0.5)
    compliant = FormatComplianceRate(0.5)
    schema = {"required": ["city"]}
    assert compliant.evaluate(['{"city": "Paris"}', "not json"], schema) == pytest.approx(0.5)
    hallucinations = HallucinationRate(0.5)
    assert hallucinations.evaluate(unsupported=1, total=4) == pytest.approx(0.75)
    assert "rate 0.25" in hallucinations.reasoning


def test_rag_metrics() -> None:
    contexts = ["Paris is the capital of France."]
    assert Faithfulness(0.5).evaluate("Paris is the capital.", contexts) == pytest.approx(1.0)
    assert ContextPrecision(0.5).evaluate([False, True]) == pytest.approx(0.5)
    assert ContextRecall(0.5).evaluate("Paris is the capital.", contexts) == pytest.approx(1.0)
    assert AnswerRelevancy(0.5).evaluate(
        "capital of France", "Paris is the capital of France"
    ) == pytest.approx(1.0)
    assert RagAnswerCorrectness(0.5).evaluate("Paris", "Paris") == pytest.approx(1.0)


def test_agent_metrics() -> None:
    assert TaskSuccessRate(0.5).evaluate(2, 2) == pytest.approx(1.0)
    calls = [
        {
            "expected_name": "search",
            "actual_name": "search",
            "expected_arguments": {"q": "Paris"},
            "actual_arguments": {"q": "Paris"},
        },
        {
            "expected_name": "search",
            "actual_name": "browse",
            "expected_arguments": {},
            "actual_arguments": {},
        },
    ]
    assert ToolCallAccuracy(0.5).evaluate(calls) == pytest.approx(0.5)
    assert TaskReliability(0.5, k=2).evaluate(successful=2, total=5) == pytest.approx(0.1)
