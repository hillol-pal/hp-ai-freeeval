import json

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from freeeval.evaluation.errors import EvaluationExecutionError
from freeeval.tracing import configure_phoenix, set_tracer_provider

PROMPT_URL = "/apis/endpoints/prompts/evaluations"
CODE_URL = "/apis/endpoints/code/evaluations"


@pytest.fixture
def phoenix_spans() -> InMemorySpanExporter:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    set_tracer_provider(provider)
    yield exporter
    set_tracer_provider(None)
    exporter.clear()


def test_prompt_evaluation_emits_a_trace(
    client: TestClient, phoenix_spans: InMemorySpanExporter
) -> None:
    response = client.post(
        PROMPT_URL,
        json={
            "prompt": "capital of France",
            "answer": "Paris is the capital of France",
            "metrics": [{"name": "answer_relevancy", "threshold": 0.5}],
        },
    )
    body = response.json()
    assert response.status_code == 200
    spans = {span.name: span for span in phoenix_spans.get_finished_spans()}
    parent = spans["freeeval.prompt"]
    metric = spans["freeeval.metric.answer_relevancy"]
    assert parent.attributes["freeeval.run_id"] == body["run_id"]
    assert parent.attributes["openinference.span.kind"] == "CHAIN"
    assert json.loads(parent.attributes["input.value"])["prompt"] == "capital of France"
    assert json.loads(parent.attributes["output.value"])["run_id"] == body["run_id"]
    assert metric.parent.span_id == parent.context.span_id
    assert metric.attributes["openinference.span.kind"] == "EVALUATOR"
    assert metric.attributes["freeeval.metric.result"] == body["metrics"][0]["result"]
    assert metric.attributes["freeeval.metric.implementation"] == "freeeval"


def test_code_evaluation_emits_a_trace(
    client: TestClient, phoenix_spans: InMemorySpanExporter
) -> None:
    response = client.post(
        CODE_URL,
        json={"cases": [{"id": "c1", "code": "print(1)", "output": "1", "expected": "1"}]},
    )
    body = response.json()
    spans = {span.name: span for span in phoenix_spans.get_finished_spans()}
    assert spans["freeeval.code"].attributes["freeeval.run_id"] == body["run_id"]
    assert spans["freeeval.metric.exact_match"].attributes["freeeval.metric.result"] == "pass"
    assert spans["freeeval.metric.exact_match"].attributes["freeeval.metric.case_id"] == "c1"


def test_judge_failure_marks_the_trace(
    client: TestClient,
    phoenix_spans: InMemorySpanExporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail() -> None:
        raise EvaluationExecutionError("DeepEval failed while measuring the metric.")

    monkeypatch.setattr("freeeval.evaluation.factory.get_deepeval_evaluator", fail)
    response = client.post(
        PROMPT_URL,
        json={
            "framework": "deepeval",
            "prompt": "capital of France",
            "answer": "Paris is the capital of France",
            "metrics": [{"name": "answer_relevancy", "threshold": 0.5}],
        },
    )
    assert response.status_code == 502
    spans = phoenix_spans.get_finished_spans()
    assert {span.name for span in spans} >= {"freeeval.prompt", "freeeval.metric.answer_relevancy"}
    assert all(span.status.status_code == StatusCode.ERROR for span in spans)
    assert "run_id" not in response.text


def test_configure_phoenix_stays_off_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FREEEVAL_PHOENIX_ENABLED", raising=False)
    monkeypatch.delenv("PHOENIX_COLLECTOR_ENDPOINT", raising=False)
    monkeypatch.delenv("PHOENIX_API_KEY", raising=False)
    import freeeval.tracing as tracing

    tracing._configured = False
    configure_phoenix()
    assert tracing._configured is False


def test_configure_phoenix_registers_the_collector(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
    monkeypatch.setenv("PHOENIX_PROJECT_NAME", "freeeval-test")
    calls: dict[str, object] = {}

    def register(**kwargs: object) -> None:
        calls.update(kwargs)

    import phoenix.otel as otel

    monkeypatch.setattr(otel, "register", register)
    import freeeval.tracing as tracing

    tracing._configured = False
    configure_phoenix()
    assert calls["project_name"] == "freeeval-test"
    assert calls["auto_instrument"] is True
    tracing._configured = False
