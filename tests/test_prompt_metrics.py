import pytest

from freeeval.metrics.prompt import (
    PROMPT_METRIC_TYPES,
    AnswerRelevancy,
    Conciseness,
    PromptEvaluation,
    Specificity,
)


def test_answer_relevancy_counts_shared_content_words() -> None:
    metric = AnswerRelevancy(threshold=0.5)
    score = metric.evaluate("capital of France", "Paris is the capital of France")
    assert score == 1.0
    assert metric.reasoning == "2 of 2 prompt content words appear in the answer."


def test_answer_relevancy_is_zero_when_nothing_overlaps() -> None:
    metric = AnswerRelevancy(threshold=0.5)
    score = metric.evaluate("capital of France", "Berlin")
    assert score == 0.0
    assert "0 of 2" in metric.reasoning


def test_conciseness_passes_a_shorter_answer_and_scales_a_longer_one() -> None:
    short = Conciseness(threshold=1)
    assert short.evaluate("hello world", "hello") == 1.0
    long = Conciseness(threshold=0.5)
    assert long.evaluate("hello", "hello there friend extra") == 0.25
    assert "4 words" in long.reasoning
    assert "1 word" in long.reasoning


def test_specificity_ignores_stopwords() -> None:
    metric = Specificity(threshold=0.5)
    assert metric.evaluate("unused", "the the Paris") == pytest.approx(1 / 3)
    assert metric.reasoning == "1 of 3 answer words are content words."


def test_threshold_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        AnswerRelevancy(1.5)


def test_prompt_evaluation_uses_each_metric_threshold() -> None:
    evaluation = PromptEvaluation(
        [AnswerRelevancy(0.5), Conciseness(0.9), Specificity(0.5)]
    )
    verdicts = evaluation.evaluate("capital of France", "Paris is the capital of France")
    assert [verdict.name for verdict in verdicts] == [
        "answer_relevancy",
        "conciseness",
        "specificity",
    ]
    assert [verdict.result for verdict in verdicts] == ["pass", "fail", "pass"]
    assert all(verdict.reasoning for verdict in verdicts)


def test_registry_matches_the_prompt_metric_classes() -> None:
    assert set(PROMPT_METRIC_TYPES) == {
        "answer_relevancy",
        "conciseness",
        "specificity",
    }
    assert PROMPT_METRIC_TYPES["answer_relevancy"] is AnswerRelevancy
    assert PROMPT_METRIC_TYPES["conciseness"] is Conciseness
    assert PROMPT_METRIC_TYPES["specificity"] is Specificity
