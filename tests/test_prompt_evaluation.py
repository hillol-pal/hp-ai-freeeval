from fastapi.testclient import TestClient

PROMPT_URL = "/apis/endpoints/prompts/evaluations"


def _case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "id": "p1",
        "input": {"question": "What is 2+2?"},
        "output": "Yes",
    }
    case.update(overrides)
    return case


def test_valid_prompt_case(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json={"cases": [_case()]})
    body = response.json()
    assert response.status_code == 200
    assert body["use_case"] == "prompt"
    assert body["results"][0]["case_id"] == "p1"


def test_missing_output_is_rejected(client: TestClient) -> None:
    case = _case()
    del case["output"]
    response = client.post(PROMPT_URL, json={"cases": [case]})
    assert response.status_code == 422
    assert "run_id" not in response.text


def test_unknown_field_is_rejected(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json={"cases": [_case(note="nope")]})
    assert response.status_code == 422
    assert "run_id" not in response.text


def test_identical_output_passes(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={"cases": [_case(output="Yes", expected="Yes")]},
    )
    score = response.json()["results"][0]["scores"][0]
    assert score["name"] == "exact_match"
    assert score["passed"] is True
    assert score["value"] is True


def test_different_output_fails(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={"cases": [_case(output="Yes", expected="No")]},
    )
    score = response.json()["results"][0]["scores"][0]
    assert score["passed"] is False
    assert score["value"] is False


def test_input_does_not_change_score(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={"cases": [_case(input={"question": "other"}, output="Yes", expected="Yes")]},
    )
    assert response.json()["results"][0]["scores"][0]["passed"] is True


def test_omitted_expected_has_empty_scores(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json={"cases": [_case()]})
    assert response.status_code == 200
    assert response.json()["results"][0]["scores"] == []


def test_summary_counts_mixed_cases(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={
            "cases": [
                _case(output="Yes", expected="Yes"),
                _case(id="p2"),
            ]
        },
    )
    assert response.json()["summary"] == {
        "case_count": 2,
        "scored_count": 1,
        "passed_count": 1,
    }


def test_each_request_gets_a_new_run_id(client: TestClient) -> None:
    first = client.post(PROMPT_URL, json={"cases": [_case()]})
    second = client.post(PROMPT_URL, json={"cases": [_case()]})
    assert first.json()["run_id"] != second.json()["run_id"]


def test_openapi_documents_prompt_request_and_response(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/apis/endpoints/prompts/evaluations"]["post"]
    request_schema = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert request_schema.endswith("/PromptEvaluationRequest")
    assert response_schema.endswith("/RunRecord")
