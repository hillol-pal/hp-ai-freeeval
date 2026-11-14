from typing import get_args

from fastapi.testclient import TestClient

from freeeval.api.schemas import RagMetricName
from freeeval.metrics.rag import RAG_METRIC_TYPES

RAG_URL = "/apis/endpoints/rag/evaluations"

PAYLOAD = {
    "query": "capital of France",
    "actual_response": "Paris is the capital of France",
    "retrieved_contexts": ["Paris is the capital of France."],
    "metrics": [
        {"name": "faithfulness", "threshold": 0.5},
        {"name": "answer_relevancy", "threshold": 0.5},
    ],
    "metadata": {"source": "docs"},
}


def test_response_matches_prompt_shape_and_has_a_run_id(client: TestClient) -> None:
    response = client.post(RAG_URL, json=PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"run_id", "framework", "metrics"}
    assert body["run_id"]
    assert body["framework"] == "freeeval"
    metrics = body["metrics"]
    assert [item["name"] for item in metrics] == ["faithfulness", "answer_relevancy"]
    assert [item["result"] for item in metrics] == ["pass", "pass"]
    for item in metrics:
        assert set(item) == {"name", "result", "reasoning", "implementation"}
        assert item["implementation"] == "freeeval"
        assert item["reasoning"]


def test_metadata_is_accepted_and_not_returned(client: TestClient) -> None:
    response = client.post(RAG_URL, json={**PAYLOAD, "metadata": {"trace": "abc"}})
    assert response.status_code == 200
    assert "metadata" not in response.json()
    assert "abc" not in response.text


def test_omitted_metadata_is_accepted(client: TestClient) -> None:
    body = {key: value for key, value in PAYLOAD.items() if key != "metadata"}
    response = client.post(RAG_URL, json=body)
    assert response.status_code == 200
    assert response.json()["metrics"][0]["result"] == "pass"


def test_each_request_receives_its_own_run_id(client: TestClient) -> None:
    first = client.post(RAG_URL, json=PAYLOAD).json()["run_id"]
    second = client.post(RAG_URL, json=PAYLOAD).json()["run_id"]
    assert first != second


def test_each_metric_uses_its_own_threshold(client: TestClient) -> None:
    body = {
        "query": "capital of France",
        "actual_response": "Berlin",
        "retrieved_contexts": ["Paris is the capital of France."],
    }
    low = client.post(
        RAG_URL,
        json={**body, "metrics": [{"name": "answer_relevancy", "threshold": 0.0}]},
    )
    high = client.post(
        RAG_URL,
        json={**body, "metrics": [{"name": "answer_relevancy", "threshold": 0.5}]},
    )
    assert low.json()["metrics"][0]["result"] == "pass"
    assert high.json()["metrics"][0]["result"] == "fail"


def test_unsupported_claim_fails_faithfulness(client: TestClient) -> None:
    response = client.post(
        RAG_URL,
        json={
            **PAYLOAD,
            "actual_response": "Berlin is the capital",
            "metrics": [{"name": "faithfulness", "threshold": 0.5}],
        },
    )
    metric = response.json()["metrics"][0]
    assert metric["result"] == "fail"
    assert "supported" in metric["reasoning"]


def test_missing_fields_return_an_error_list(client: TestClient) -> None:
    response = client.post(RAG_URL, json={})
    body = response.json()
    assert response.status_code == 422
    assert isinstance(body, list)
    assert "run_id" not in response.text
    assert {item["reason_code"] for item in body} == {"MISSING_FIELD"}
    assert {item["error_code"] for item in body} == {"VALIDATION_ERROR"}
    assert {item["message"].split(":", 1)[0] for item in body} == {
        "query",
        "actual_response",
        "retrieved_contexts",
        "metrics",
    }


def test_unknown_field_is_rejected(client: TestClient) -> None:
    response = client.post(RAG_URL, json={**PAYLOAD, "note": "nope"})
    body = response.json()
    assert response.status_code == 422
    assert body[0]["reason_code"] == "UNKNOWN_FIELD"


def test_unknown_metric_is_rejected(client: TestClient) -> None:
    response = client.post(
        RAG_URL,
        json={**PAYLOAD, "metrics": [{"name": "context_precision", "threshold": 0.5}]},
    )
    assert response.status_code == 422
    assert response.json()[0]["reason_code"] == "UNSUPPORTED_METRIC"


def test_duplicate_metrics_are_rejected(client: TestClient) -> None:
    response = client.post(
        RAG_URL,
        json={
            **PAYLOAD,
            "metrics": [
                {"name": "faithfulness", "threshold": 0.2},
                {"name": "faithfulness", "threshold": 0.8},
            ],
        },
    )
    assert response.status_code == 422
    assert response.json()[0]["reason_code"] == "DUPLICATE_METRIC"


def test_metadata_must_be_an_object(client: TestClient) -> None:
    response = client.post(RAG_URL, json={**PAYLOAD, "metadata": ["not", "an", "object"]})
    assert response.status_code == 422
    assert response.json()[0]["reason_code"] == "INVALID_TYPE"


def test_openapi_documents_rag_request_and_run_response(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    operation = schema["paths"][RAG_URL]["post"]
    components = schema["components"]["schemas"]
    request_ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert request_ref.endswith("/RagEvaluationRequest")
    assert response_schema["$ref"].endswith("/RagEvaluationResponse")
    assert set(components["RagEvaluationRequest"]["properties"]) == {
        "query",
        "actual_response",
        "retrieved_contexts",
        "metrics",
        "metadata",
        "framework",
    }
    assert set(components["RagEvaluationResponse"]["properties"]) == {
        "run_id",
        "framework",
        "metrics",
    }
    assert set(get_args(RagMetricName)) == set(RAG_METRIC_TYPES)
