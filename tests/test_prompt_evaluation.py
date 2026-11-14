from typing import get_args

from fastapi.testclient import TestClient

from freeeval.api.schemas import PromptMetricName
from freeeval.metrics.prompt import PROMPT_METRIC_TYPES

PROMPT_URL = "/apis/endpoints/prompts/evaluations"

PAYLOAD = {
    "prompt": "capital of France",
    "answer": "Paris is the capital of France",
    "metrics": [
        {"name": "answer_relevancy", "threshold": 0.5},
        {"name": "specificity", "threshold": 0.5},
    ],
}


def test_response_has_run_id_and_metric_verdicts(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json=PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"run_id", "framework", "metrics"}
    assert body["run_id"]
    assert body["framework"] == "freeeval"
    metrics = body["metrics"]
    assert [item["name"] for item in metrics] == ["answer_relevancy", "specificity"]
    assert [item["result"] for item in metrics] == ["pass", "pass"]
    for item in metrics:
        assert set(item) == {"name", "result", "reasoning", "implementation"}
        assert item["implementation"] == "freeeval"
        assert item["reasoning"]


def test_each_request_receives_its_own_run_id(client: TestClient) -> None:
    first = client.post(PROMPT_URL, json=PAYLOAD).json()["run_id"]
    second = client.post(PROMPT_URL, json=PAYLOAD).json()["run_id"]
    assert first != second


def test_each_metric_uses_its_own_threshold(client: TestClient) -> None:
    body = {
        "prompt": "hello",
        "answer": "hello there friend extra",
    }
    low = client.post(
        PROMPT_URL,
        json={**body, "metrics": [{"name": "conciseness", "threshold": 0.2}]},
    )
    high = client.post(
        PROMPT_URL,
        json={**body, "metrics": [{"name": "conciseness", "threshold": 0.9}]},
    )
    assert low.json()["metrics"][0]["result"] == "pass"
    assert high.json()["metrics"][0]["result"] == "fail"


def test_score_equal_to_threshold_passes(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={
            "prompt": "hello",
            "answer": "hello there",
            "metrics": [{"name": "conciseness", "threshold": 0.5}],
        },
    )
    assert response.json()["metrics"][0]["result"] == "pass"
    assert "2 words" in response.json()["metrics"][0]["reasoning"]


def test_missing_fields_return_an_error_list(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json={})
    body = response.json()
    assert response.status_code == 422
    assert isinstance(body, list)
    assert {item["reason_code"] for item in body} == {"MISSING_FIELD"}
    assert {item["error_code"] for item in body} == {"VALIDATION_ERROR"}
    assert {item["message"].split(":", 1)[0] for item in body} == {
        "prompt",
        "answer",
        "metrics",
    }


def test_missing_metric_threshold_is_rejected(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={
            "prompt": "capital of France",
            "answer": "Paris",
            "metrics": [{"name": "answer_relevancy"}],
        },
    )
    body = response.json()
    assert response.status_code == 422
    assert body[0]["reason_code"] == "MISSING_FIELD"
    assert "threshold" in body[0]["message"]


def test_unknown_field_is_rejected(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json={**PAYLOAD, "note": "nope"})
    body = response.json()
    assert response.status_code == 422
    assert body[0]["reason_code"] == "UNKNOWN_FIELD"
    assert body[0]["error_code"] == "VALIDATION_ERROR"


def test_empty_prompt_is_rejected(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json={**PAYLOAD, "prompt": ""})
    assert response.status_code == 422
    assert response.json()[0]["reason_code"] == "EMPTY"


def test_empty_metrics_list_is_rejected(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json={**PAYLOAD, "metrics": []})
    assert response.status_code == 422
    assert response.json()[0]["reason_code"] == "EMPTY"


def test_unknown_metric_is_rejected(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={**PAYLOAD, "metrics": [{"name": "bleu", "threshold": 0.5}]},
    )
    body = response.json()
    assert response.status_code == 422
    assert body[0]["error_code"] == "VALIDATION_ERROR"
    assert body[0]["reason_code"] == "UNSUPPORTED_METRIC"


def test_duplicate_metrics_are_rejected(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={
            **PAYLOAD,
            "metrics": [
                {"name": "specificity", "threshold": 0.2},
                {"name": "specificity", "threshold": 0.8},
            ],
        },
    )
    assert response.status_code == 422
    assert response.json()[0]["reason_code"] == "DUPLICATE_METRIC"


def test_threshold_out_of_range_is_rejected(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={**PAYLOAD, "metrics": [{"name": "specificity", "threshold": 1.5}]},
    )
    assert response.status_code == 422
    assert response.json()[0]["reason_code"] == "OUT_OF_RANGE"


def test_openapi_documents_metric_list_request_and_run_response(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()
    operation = schema["paths"][PROMPT_URL]["post"]
    components = schema["components"]["schemas"]
    request_ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert request_ref.endswith("/PromptEvaluationRequest")
    assert response_schema["$ref"].endswith("/PromptEvaluationResponse")
    response_properties = components["PromptEvaluationResponse"]["properties"]
    assert set(response_properties) == {"run_id", "framework", "metrics"}
    assert response_properties["metrics"]["items"]["$ref"].endswith("/PromptMetricResult")
    request_properties = components["PromptEvaluationRequest"]["properties"]
    assert set(request_properties) == {"prompt", "answer", "metrics", "framework"}
    metric_properties = components["PromptMetricSpec"]["properties"]
    assert set(metric_properties) == {"name", "threshold"}
    assert set(components["PromptMetricResult"]["properties"]) == {
        "name",
        "result",
        "reasoning",
        "implementation",
    }
    assert set(components["PromptMetricResult"]["properties"]["result"]["enum"]) == {
        "pass",
        "fail",
    }
    assert set(get_args(PromptMetricName)) == set(PROMPT_METRIC_TYPES)
