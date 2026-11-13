from typing import get_args

from fastapi.testclient import TestClient

from freeeval.api.schemas import AgentMetricName
from freeeval.metrics.agentic import AGENT_METRIC_TYPES

AGENT_URL = "/apis/endpoints/agents/evaluations"

PAYLOAD = {
    "input": "Find the capital of France",
    "actual_output": "Paris",
    "execution_trace": [
        {
            "kind": "tool",
            "name": "search",
            "arguments": {"q": "capital of France"},
            "expected_name": "search",
            "expected_arguments": {"q": "capital of France"},
        }
    ],
    "metrics": [
        {"name": "task_success_rate", "threshold": 0.5},
        {"name": "tool_call_accuracy", "threshold": 0.5},
    ],
    "metadata": {"source": "docs"},
}


def test_response_matches_the_other_routes_and_has_a_run_id(client: TestClient) -> None:
    response = client.post(AGENT_URL, json=PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"run_id", "metrics"}
    assert body["run_id"]
    metrics = body["metrics"]
    assert [item["name"] for item in metrics] == ["task_success_rate", "tool_call_accuracy"]
    assert [item["result"] for item in metrics] == ["pass", "pass"]
    for item in metrics:
        assert set(item) == {"name", "result", "reasoning"}
        assert item["reasoning"]


def test_empty_trace_can_still_succeed(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={
            **PAYLOAD,
            "execution_trace": [],
            "metrics": [{"name": "task_success_rate", "threshold": 0.5}],
        },
    )
    assert response.status_code == 200
    assert response.json()["metrics"][0]["result"] == "pass"


def test_trace_error_fails_task_success(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={
            **PAYLOAD,
            "execution_trace": [
                {"kind": "tool", "name": "search", "error": "timeout"},
            ],
            "metrics": [{"name": "task_success_rate", "threshold": 0.5}],
        },
    )
    metric = response.json()["metrics"][0]
    assert metric["result"] == "fail"
    assert "trace error" in metric["reasoning"]


def test_wrong_tool_fails_accuracy(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={
            **PAYLOAD,
            "execution_trace": [
                {
                    "kind": "tool",
                    "name": "browse",
                    "arguments": {},
                    "expected_name": "search",
                    "expected_arguments": {},
                }
            ],
            "metrics": [{"name": "tool_call_accuracy", "threshold": 0.5}],
        },
    )
    metric = response.json()["metrics"][0]
    assert metric["result"] == "fail"
    assert "tool calls" in metric["reasoning"]


def test_metadata_is_accepted_and_not_returned(client: TestClient) -> None:
    response = client.post(AGENT_URL, json={**PAYLOAD, "metadata": {"trace": "abc"}})
    assert response.status_code == 200
    assert "metadata" not in response.json()
    assert "abc" not in response.text


def test_each_request_receives_its_own_run_id(client: TestClient) -> None:
    first = client.post(AGENT_URL, json=PAYLOAD).json()["run_id"]
    second = client.post(AGENT_URL, json=PAYLOAD).json()["run_id"]
    assert first != second


def test_missing_fields_return_an_error_list(client: TestClient) -> None:
    response = client.post(AGENT_URL, json={})
    body = response.json()
    assert response.status_code == 422
    assert isinstance(body, list)
    assert "run_id" not in response.text
    assert {item["reason_code"] for item in body} == {"MISSING_FIELD"}
    assert {item["message"].split(":", 1)[0] for item in body} == {
        "input",
        "actual_output",
        "execution_trace",
        "metrics",
    }


def test_unknown_trace_kind_is_rejected(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={
            **PAYLOAD,
            "execution_trace": [{"kind": "browse", "name": "search"}],
        },
    )
    assert response.status_code == 422
    assert isinstance(response.json(), list)
    assert "run_id" not in response.text


def test_unknown_metric_is_rejected(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={**PAYLOAD, "metrics": [{"name": "task_reliability", "threshold": 0.5}]},
    )
    assert response.status_code == 422
    assert response.json()[0]["reason_code"] == "UNSUPPORTED_METRIC"


def test_duplicate_metrics_are_rejected(client: TestClient) -> None:
    response = client.post(
        AGENT_URL,
        json={
            **PAYLOAD,
            "metrics": [
                {"name": "task_success_rate", "threshold": 0.2},
                {"name": "task_success_rate", "threshold": 0.8},
            ],
        },
    )
    assert response.status_code == 422
    assert response.json()[0]["reason_code"] == "DUPLICATE_METRIC"


def test_openapi_documents_agent_request_and_run_response(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    operation = schema["paths"][AGENT_URL]["post"]
    components = schema["components"]["schemas"]
    request_ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert request_ref.endswith("/AgentEvaluationRequest")
    assert response_schema["$ref"].endswith("/AgentEvaluationResponse")
    assert set(components["AgentEvaluationRequest"]["properties"]) == {
        "input",
        "actual_output",
        "execution_trace",
        "metrics",
        "metadata",
    }
    assert set(components["AgentEvaluationResponse"]["properties"]) == {"run_id", "metrics"}
    assert set(get_args(AgentMetricName)) == set(AGENT_METRIC_TYPES)
