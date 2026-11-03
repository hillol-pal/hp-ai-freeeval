from freeeval.api.schemas import CaseResult, Score, Summary


def exact_scores(actual: str, expected: str | None) -> list[Score]:
    if expected is None:
        return []
    passed = actual == expected
    return [Score(name="exact_match", value=passed, passed=passed)]


def summarize(results: list[CaseResult]) -> Summary:
    """Summarize at case level, even when a case has multiple metrics.

    A case is scored when at least one metric has a numeric or boolean value.
    A case passes only when every reported metric has an explicit passing verdict;
    skipped metrics (``passed is None``) therefore prevent a full pass.
    """
    scored_results = [
        result
        for result in results
        if any(score.value is not None for score in result.scores)
    ]
    passed_count = sum(
        1
        for result in scored_results
        if result.scores and all(score.passed is True for score in result.scores)
    )
    return Summary(
        case_count=len(results),
        scored_count=len(scored_results),
        passed_count=passed_count,
    )
