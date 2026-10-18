from fastapi.testclient import TestClient

AGENT_URL = "/apis/endpoints/agents/evaluations"


def _case(**overrides: object) -> dict[str, object]:
    case: dict[str, object] = {
        "id": "a1",
        "task": "Find the capital",
        "output": "done",
        "steps": [{"kind": "tool", "name": "search"}],
    }
    case.update(overrides)
    return case


def test_valid_agent_case_with_tool_step(client: TestClient) -> None:
    response = client.post(AGENT_URL, json={"cases": [_case()]})
    body = response.json()
    assert response.status_code == 200
    assert body["use_case"] == "agent"
    assert body["results"][0]["case_id"] == "a1"


def test_empty_steps_are_accepted(client: TestClient) -> None:
    response = client.post(AGENT_URL, json={"cases": [_case(steps=[])]})
    assert response.status_code == 200


def test_optional_step_fields_are_accepted(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={
            "cases": [
                _case(
                    steps=[
                        {
                            "kind": "tool",
                            "name": "search",
                            "input": {"q": "capital"},
                            "output": {"text": "Paris"},
                            "error": "",
                        }
                    ]
                )
            ]
        },
    )
    assert response.status_code == 200


def test_unknown_step_kind_is_rejected(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={"cases": [_case(steps=[{"kind": "browse", "name": "search"}])]},
    )
    assert response.status_code == 422
    assert "run_id" not in response.text


def test_identical_output_passes(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={"cases": [_case(expected_output="done")]},
    )
    score = response.json()["results"][0]["scores"][0]
    assert score["passed"] is True
    assert score["value"] is True


def test_step_error_does_not_change_score(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={
            "cases": [
                _case(
                    expected_output="done",
                    steps=[{"kind": "tool", "name": "search", "error": "timeout"}],
                )
            ]
        },
    )
    assert response.json()["results"][0]["scores"][0]["passed"] is True


def test_omitted_expected_output_has_empty_scores(client: TestClient) -> None:
    response = client.post(AGENT_URL, json={"cases": [_case()]})
    assert response.status_code == 200
    assert response.json()["results"][0]["scores"] == []


def test_summary_counts_mixed_cases(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={
            "cases": [
                _case(expected_output="done"),
                _case(id="a2"),
            ]
        },
    )
    assert response.json()["summary"] == {
        "case_count": 2,
        "scored_count": 1,
        "passed_count": 1,
    }
