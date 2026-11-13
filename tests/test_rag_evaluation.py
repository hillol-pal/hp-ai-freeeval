import pytest
from fastapi.testclient import TestClient

from freeeval.evaluation.deepeval import MetricEvaluation

RAG_URL = "/apis/endpoints/rag/evaluations"


class _FakeEvaluator:
    def evaluate_rag_case(
        self,
        *,
        question: str,
        answer: str,
        retrieval_context: list[str],
        threshold: float,
    ) -> dict[str, MetricEvaluation | None]:
        faithfulness = None
        if retrieval_context:
            faithfulness = MetricEvaluation(score=1.0, reason="grounded")
        return {
            "faithfulness": faithfulness,
            "answer_relevancy": MetricEvaluation(score=1.0, reason="relevant"),
        }


@pytest.fixture(autouse=True)
def stub_deepeval(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "freeeval.api.routers.rag.get_deepeval_evaluator",
        lambda: _FakeEvaluator(),
    )


def _case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "id": "r1",
        "question": "Capital of France?",
        "answer": "Paris",
        "contexts": [{"id": "c1", "text": "Paris is the capital."}],
    }
    case.update(overrides)
    return case


def test_valid_rag_case(client: TestClient) -> None:
    response = client.post(RAG_URL, json={"cases": [_case()]})
    body = response.json()
    assert response.status_code == 200
    assert body["use_case"] == "rag"
    assert body["results"][0]["case_id"] == "r1"


def test_context_missing_text_is_rejected(client: TestClient) -> None:
    response = client.post(
        RAG_URL,
        json={"cases": [_case(contexts=[{"id": "c1"}])]},
    )
    assert response.status_code == 422
    assert "run_id" not in response.text


def test_identical_answer_passes(client: TestClient) -> None:
    response = client.post(
        RAG_URL,
        json={"cases": [_case(expected_answer="Paris")]},
    )
    score = response.json()["results"][0]["scores"][0]
    assert score["passed"] is True
    assert score["value"] is True


def test_relevant_ids_do_not_change_score(client: TestClient) -> None:
    response = client.post(
        RAG_URL,
        json={"cases": [_case(expected_answer="Paris", relevant_context_ids=["missing"])]},
    )
    assert response.json()["results"][0]["scores"][0]["passed"] is True


def test_omitted_expected_answer_has_no_exact_match(client: TestClient) -> None:
    response = client.post(RAG_URL, json={"cases": [_case()]})
    assert response.status_code == 200
    names = [score["name"] for score in response.json()["results"][0]["scores"]]
    assert names == ["faithfulness", "answer_relevancy"]


def test_summary_counts_mixed_cases(client: TestClient) -> None:
    response = client.post(
        RAG_URL,
        json={
            "cases": [
                _case(expected_answer="Paris"),
                _case(id="r2"),
            ]
        },
    )
    body = response.json()
    assert body["summary"] == {
        "case_count": 2,
        "scored_count": 2,
        "passed_count": 2,
    }
    assert body["results"][0]["scores"][0]["name"] == "exact_match"
    assert "exact_match" not in [score["name"] for score in body["results"][1]["scores"]]
