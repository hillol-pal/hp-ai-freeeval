from freeeval.api.schemas import CaseResult
from freeeval.api.scoring import exact_scores, summarize


def test_equal_strings_pass() -> None:
    scores = exact_scores("Yes", "Yes")
    assert len(scores) == 1
    assert scores[0].name == "exact_match"
    assert scores[0].value is True
    assert scores[0].passed is True


def test_unequal_strings_fail() -> None:
    scores = exact_scores("Yes", "yes")
    assert scores[0].value is False
    assert scores[0].passed is False


def test_whitespace_difference_fails() -> None:
    scores = exact_scores("Yes ", "Yes")
    assert scores[0].passed is False
    assert scores[0].value is False


def test_omitted_expected_produces_no_score() -> None:
    assert exact_scores("Yes", None) == []


def test_summary_counts_one_scored_pass_among_two() -> None:
    results = [
        CaseResult(case_id="a", scores=exact_scores("Yes", "Yes")),
        CaseResult(case_id="b", scores=exact_scores("Yes", None)),
    ]
    summary = summarize(results)
    assert summary.case_count == 2
    assert summary.scored_count == 1
    assert summary.passed_count == 1
