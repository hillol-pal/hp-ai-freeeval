import pytest
from fastapi.testclient import TestClient

from data_generation import catalog, generate, generate_all
from freeeval.api.schemas import (
    AgentEvaluationRequest,
    CodeEvaluationRequest,
    PromptEvaluationRequest,
    RagEvaluationRequest,
)

_URLS = {
    "prompt": "/apis/endpoints/prompts/evaluations",
    "code": "/apis/endpoints/code/evaluations",
    "rag": "/apis/endpoints/rag/evaluations",
    "agent": "/apis/endpoints/agents/evaluations",
}
_MODELS = {
    "prompt": PromptEvaluationRequest,
    "code": CodeEvaluationRequest,
    "rag": RagEvaluationRequest,
    "agent": AgentEvaluationRequest,
}


def test_catalogs_have_unique_names() -> None:
    for category in ("prompt", "code", "rag", "agent"):
        names = [sample.name for sample in catalog(category)]
        assert names
        assert len(names) == len(set(names))


def test_generate_walks_the_catalog_from_the_seed() -> None:
    start = generate("prompt", count=1, seed=1)[0]
    walked = generate("prompt", count=3, seed=1)
    assert start.name == "long_answer"
    assert [sample.name for sample in walked] == [
        "long_answer",
        "relevant_answer",
        "long_answer",
    ]


def test_generate_rejects_bad_count_seed_and_category() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        generate("prompt", count=0)
    with pytest.raises(ValueError, match="seed"):
        generate("prompt", seed=-1)
    with pytest.raises(ValueError, match="Unknown category"):
        catalog("summary")  # type: ignore[arg-type]


def test_generated_bodies_are_copies() -> None:
    first = generate("prompt", count=1)[0]
    first.body["prompt"] = "changed"
    assert generate("prompt", count=1)[0].body["prompt"] == "capital of France"


def test_samples_match_their_labeled_verdicts(client: TestClient) -> None:
    for sample in generate_all():
        _MODELS[sample.category].model_validate(sample.body)
        response = client.post(_URLS[sample.category], json=sample.body)
        assert response.status_code == 200, sample.name
        if sample.category == "code":
            _assert_code(sample.name, response.json(), sample.expected_results)
        else:
            metrics = response.json()["metrics"]
            assert [item["name"] for item in metrics] == list(sample.expected_results)
            assert {
                item["name"]: item["result"] for item in metrics
            } == sample.expected_results


def _assert_code(name: str, body: dict[str, object], expected: dict[str, str]) -> None:
    scores = body["results"][0]["scores"]  # type: ignore[index]
    if not expected:
        assert scores == [], name
        return
    assert scores[0]["name"] == "exact_match"  # type: ignore[index]
    passed = scores[0]["passed"]  # type: ignore[index]
    assert passed is (expected["exact_match"] == "pass"), name
