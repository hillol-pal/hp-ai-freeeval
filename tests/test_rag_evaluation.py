from fastapi.testclient import TestClient

RAG_URL = "/apis/endpoints/rag/evaluations"


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


def test_omitted_expected_answer_has_empty_scores(client: TestClient) -> None:
    response = client.post(RAG_URL, json={"cases": [_case()]})
    assert response.status_code == 200
    assert response.json()["results"][0]["scores"] == []


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
    assert response.json()["summary"] == {
        "case_count": 2,
        "scored_count": 1,
        "passed_count": 1,
    }
