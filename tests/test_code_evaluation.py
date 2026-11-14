from fastapi.testclient import TestClient

CODE_URL = "/apis/endpoints/code/evaluations"


def _case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "id": "c1",
        "code": "print(2 + 2)",
        "output": "4",
    }
    case.update(overrides)
    return case


def test_valid_code_case(client: TestClient) -> None:
    response = client.post(CODE_URL, json={"cases": [_case()]})
    body = response.json()
    assert response.status_code == 200
    assert body["use_case"] == "code"
    assert body["results"][0]["case_id"] == "c1"


def test_missing_output_is_rejected(client: TestClient) -> None:
    case = _case()
    del case["output"]
    response = client.post(CODE_URL, json={"cases": [case]})
    assert response.status_code == 422
    assert "run_id" not in response.text


def test_unknown_field_is_rejected(client: TestClient) -> None:
    response = client.post(CODE_URL, json={"cases": [_case(note="nope")]})
    assert response.status_code == 422
    assert "run_id" not in response.text


def test_identical_output_passes(client: TestClient) -> None:
    response = client.post(
        CODE_URL,
        json={"cases": [_case(output="4", expected="4")]},
    )
    score = response.json()["results"][0]["scores"][0]
    assert score["name"] == "exact_match"
    assert score["passed"] is True
    assert score["value"] is True


def test_different_output_fails(client: TestClient) -> None:
    response = client.post(
        CODE_URL,
        json={"cases": [_case(output="4", expected="5")]},
    )
    score = response.json()["results"][0]["scores"][0]
    assert score["passed"] is False
    assert score["value"] is False


def test_code_does_not_change_score(client: TestClient) -> None:
    response = client.post(
        CODE_URL,
        json={"cases": [_case(code="print('four')", output="4", expected="4")]},
    )
    assert response.json()["results"][0]["scores"][0]["passed"] is True


def test_omitted_expected_has_empty_scores(client: TestClient) -> None:
    response = client.post(CODE_URL, json={"cases": [_case()]})
    assert response.status_code == 200
    assert response.json()["results"][0]["scores"] == []


def test_summary_counts_mixed_cases(client: TestClient) -> None:
    response = client.post(
        CODE_URL,
        json={
            "cases": [
                _case(output="4", expected="4"),
                _case(id="c2"),
            ]
        },
    )
    assert response.json()["summary"] == {
        "case_count": 2,
        "scored_count": 1,
        "passed_count": 1,
    }


def test_each_request_gets_a_new_run_id(client: TestClient) -> None:
    first = client.post(CODE_URL, json={"cases": [_case()]})
    second = client.post(CODE_URL, json={"cases": [_case()]})
    assert first.json()["run_id"] != second.json()["run_id"]
