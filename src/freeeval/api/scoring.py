from freeeval.api.schemas import CaseResult, Score, Summary


def exact_scores(actual: str, expected: str | None) -> list[Score]:
    if expected is None:
        return []
    passed = actual == expected
    return [Score(name="exact_match", value=passed, passed=passed)]


def summarize(results: list[CaseResult]) -> Summary:
    scored_count = sum(1 for result in results if result.scores)
    passed_count = sum(1 for result in results for score in result.scores if score.passed)
    return Summary(
        case_count=len(results),
        scored_count=scored_count,
        passed_count=passed_count,
    )
