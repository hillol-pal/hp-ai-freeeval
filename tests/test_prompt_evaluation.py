from fastapi.testclient import TestClient

PROMPT_URL = "/apis/endpoints/prompts/"

PAYLOAD = {
    "prompt": "What is 2+2?",
    "response": "4",
    "metrics": [
        {"name": "answer_relevancy", "provider": "deepeval"},
        {"name": "faithfulness", "provider": "ragas"},
    ],
    "temperature": 0,
    "threshold": 0.7,
}


def test_returns_one_verdict_per_metric(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json=PAYLOAD)
    body = response.json()
    assert response.status_code == 200
    assert body["verdicts"] == [
        {
            "metric": "answer_relevancy",
            "provider": "deepeval",
            "threshold": 0.7,
            "score": None,
            "passed": None,
            "status": "pending",
        },
        {
            "metric": "faithfulness",
            "provider": "ragas",
            "threshold": 0.7,
            "score": None,
            "passed": None,
            "status": "pending",
        },
    ]


def test_missing_prompt_is_rejected(client: TestClient) -> None:
    payload = {key: value for key, value in PAYLOAD.items() if key != "prompt"}
    response = client.post(PROMPT_URL, json=payload)
    assert response.status_code == 422
    assert "verdicts" not in response.json()


def test_unknown_field_is_rejected(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json={**PAYLOAD, "note": "nope"})
    assert response.status_code == 422
    assert "verdicts" not in response.json()


def test_metrics_must_be_a_non_empty_list(client: TestClient) -> None:
    response = client.post(PROMPT_URL, json={**PAYLOAD, "metrics": []})
    assert response.status_code == 422


def test_unknown_provider_is_rejected(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={**PAYLOAD, "metrics": [{"name": "bleu", "provider": "builtin"}]},
    )
    assert response.status_code == 422


def test_openapi_documents_prompt_request_and_response(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/apis/endpoints/prompts/"]["post"]
    components = schema["components"]["schemas"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/PromptRequest"
    )
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/PromptResponse"
    )
    assert components["PromptRequest"]["properties"]["metrics"]["type"] == "array"
    for name in ("prompt", "response", "metrics", "temperature", "threshold"):
        assert name in components["PromptRequest"]["properties"]
    assert components["PromptResponse"]["properties"]["verdicts"]["type"] == "array"
    assert set(components["PromptMetric"]["properties"]["provider"]["enum"]) == {
        "deepeval",
        "ragas",
    }
