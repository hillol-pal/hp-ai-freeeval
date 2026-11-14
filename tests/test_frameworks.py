import pytest
from fastapi.testclient import TestClient

from freeeval.evaluation.deepeval import MetricEvaluation
from freeeval.evaluation.errors import EvaluationConfigurationError, EvaluationExecutionError
from freeeval.evaluation.ragas import RagasEvaluator
from freeeval.metrics.agentic.evaluation import TraceStep

PROMPT_URL = "/apis/endpoints/prompts/evaluations"
RAG_URL = "/apis/endpoints/rag/evaluations"
AGENT_URL = "/apis/endpoints/agents/evaluations"


class _Judge:
    def __init__(self, score: float = 0.9, reason: str = "judge accepted the answer") -> None:
        self.calls: list[str] = []
        self.score = score
        self.reason = reason

    def score_answer_relevancy(self, **kwargs: object) -> MetricEvaluation:
        self.calls.append("answer_relevancy")
        return MetricEvaluation(score=self.score, reason=self.reason)

    def score_faithfulness(self, **kwargs: object) -> MetricEvaluation:
        self.calls.append("faithfulness")
        return MetricEvaluation(score=self.score, reason=self.reason)

    def score_task_completion(self, **kwargs: object) -> MetricEvaluation:
        self.calls.append("task_success_rate")
        return MetricEvaluation(score=self.score, reason=self.reason)

    def score_tool_correctness(self, **kwargs: object) -> MetricEvaluation:
        self.calls.append("tool_call_accuracy")
        return MetricEvaluation(score=self.score, reason=self.reason)

    def score_tool_call_accuracy(self, **kwargs: object) -> MetricEvaluation:
        self.calls.append("tool_call_accuracy")
        return MetricEvaluation(score=self.score, reason=self.reason)

    def score_task_success(self, **kwargs: object) -> MetricEvaluation:
        self.calls.append("task_success_rate")
        return MetricEvaluation(score=self.score, reason=self.reason)


def test_freeeval_framework_does_not_call_a_judge(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail() -> None:
        raise AssertionError("judge factory should not be called")

    monkeypatch.setattr("freeeval.evaluation.factory.get_deepeval_evaluator", fail)
    monkeypatch.setattr("freeeval.evaluation.factory.get_ragas_evaluator", fail)
    response = client.post(
        PROMPT_URL,
        json={
            "prompt": "capital of France",
            "answer": "Paris is the capital of France",
            "metrics": [{"name": "answer_relevancy", "threshold": 0.5}],
        },
    )
    assert response.status_code == 200
    assert response.json()["metrics"][0]["implementation"] == "freeeval"


def test_deepeval_uses_the_sdk_and_freeeval_for_the_rest(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    judge = _Judge()
    monkeypatch.setattr("freeeval.evaluation.factory.get_deepeval_evaluator", lambda: judge)
    response = client.post(
        PROMPT_URL,
        json={
            "framework": "deepeval",
            "prompt": "hello",
            "answer": "hello there friend extra",
            "metrics": [
                {"name": "answer_relevancy", "threshold": 0.5},
                {"name": "conciseness", "threshold": 0.9},
            ],
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["framework"] == "deepeval"
    assert judge.calls == ["answer_relevancy"]
    assert body["metrics"][0]["implementation"] == "deepeval"
    assert body["metrics"][0]["result"] == "pass"
    assert body["metrics"][0]["reasoning"].startswith("DeepEval AnswerRelevancyMetric:")
    assert body["metrics"][1]["implementation"] == "freeeval"
    assert body["metrics"][1]["result"] == "fail"
    assert body["metrics"][1]["reasoning"].startswith("FreeEval conciseness:")


def test_ragas_fallback_prefixes_freeeval_reasoning(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    judge = _Judge(score=0.1, reason="not faithful")
    monkeypatch.setattr("freeeval.evaluation.factory.get_ragas_evaluator", lambda: judge)
    response = client.post(
        RAG_URL,
        json={
            "framework": "ragas",
            "query": "capital of France",
            "actual_response": "Paris is the capital of France",
            "retrieved_contexts": ["Paris is the capital of France."],
            "metrics": [
                {"name": "faithfulness", "threshold": 0.5},
                {"name": "answer_relevancy", "threshold": 0.5},
            ],
        },
    )
    metrics = response.json()["metrics"]
    assert response.status_code == 200
    assert judge.calls == ["faithfulness", "answer_relevancy"]
    assert metrics[0]["result"] == "fail"
    assert metrics[0]["implementation"] == "ragas"
    assert metrics[0]["reasoning"].startswith("Ragas Faithfulness:")
    assert metrics[1]["implementation"] == "ragas"


def test_deepeval_agent_metrics_ignore_the_trace_error_rule(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    judge = _Judge(score=1.0, reason="the task was completed")
    monkeypatch.setattr("freeeval.evaluation.factory.get_deepeval_evaluator", lambda: judge)
    response = client.post(
        AGENT_URL,
        json={
            "framework": "deepeval",
            "input": "Find the capital of France",
            "actual_output": "Paris",
            "execution_trace": [{"kind": "tool", "name": "search", "error": "timeout"}],
            "metrics": [{"name": "task_success_rate", "threshold": 0.5}],
        },
    )
    metric = response.json()["metrics"][0]
    assert response.status_code == 200
    assert metric["result"] == "pass"
    assert metric["implementation"] == "deepeval"
    assert "TaskCompletionMetric" in metric["reasoning"]


def test_missing_judge_configuration_is_a_list_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail() -> None:
        raise EvaluationConfigurationError("DeepEval scoring requires OPENAI_API_KEY.")

    monkeypatch.setattr("freeeval.evaluation.factory.get_deepeval_evaluator", fail)
    response = client.post(
        RAG_URL,
        json={
            "framework": "deepeval",
            "query": "capital of France",
            "actual_response": "Paris",
            "retrieved_contexts": ["Paris is the capital."],
            "metrics": [{"name": "faithfulness", "threshold": 0.5}],
        },
    )
    body = response.json()
    assert response.status_code == 503
    assert isinstance(body, list)
    assert "run_id" not in response.text
    assert body[0]["error_code"] == "EVALUATION_UNAVAILABLE"
    assert body[0]["reason_code"] == "JUDGE_NOT_CONFIGURED"


def test_judge_failure_does_not_fall_back_to_freeeval(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
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
    assert response.json()[0]["reason_code"] == "JUDGE_FAILED"
    assert "run_id" not in response.text


def test_unknown_framework_is_rejected(client: TestClient) -> None:
    response = client.post(
        PROMPT_URL,
        json={
            "framework": "bleu",
            "prompt": "hello",
            "answer": "hello",
            "metrics": [{"name": "conciseness", "threshold": 0.5}],
        },
    )
    assert response.status_code == 422
    assert response.json()[0]["reason_code"] == "INVALID_VALUE"


def test_deepeval_sdk_imports() -> None:
    from freeeval.evaluation.deepeval import DeepEvalEvaluator

    evaluator = DeepEvalEvaluator(model_name="gpt-4o-mini", api_key=None)
    sdk = evaluator._load_sdk()
    assert sdk.AnswerRelevancyMetric.__name__ == "AnswerRelevancyMetric"
    assert sdk.FaithfulnessMetric.__name__ == "FaithfulnessMetric"
    assert sdk.ToolCorrectnessMetric.__name__ == "ToolCorrectnessMetric"
    assert sdk.TaskCompletionMetric.__name__ == "TaskCompletionMetric"
    assert sdk.ToolCall.__name__ == "ToolCall"


def test_ragas_sdk_imports() -> None:
    evaluator = RagasEvaluator(model_name="gpt-4o-mini", api_key=None)
    sdk = evaluator._load_sdk()
    assert sdk.Faithfulness.__name__ == "Faithfulness"
    assert sdk.AnswerRelevancy.__name__ == "AnswerRelevancy"
    assert sdk.ToolCallAccuracy.__name__ == "ToolCallAccuracy"
    assert sdk.AgentGoalAccuracyWithoutReference.__name__ == "AgentGoalAccuracyWithoutReference"


def test_ragas_tool_accuracy_passes_expected_calls() -> None:
    seen: dict[str, object] = {}

    class _Result:
        value = 1.0
        reason = "tools matched"

    class _ToolCall:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs

    class _Message:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs

    class _ToolMetric:
        def score(self, **kwargs: object) -> _Result:
            seen.update(kwargs)
            return _Result()

    class _SDK:
        ToolCall = _ToolCall
        HumanMessage = _Message
        AIMessage = _Message
        ToolCallAccuracy = _ToolMetric

    evaluator = RagasEvaluator(model_name="gpt-4o-mini", api_key=None, sdk=_SDK)
    scored = evaluator.score_tool_call_accuracy(
        task="Find Paris",
        output="Paris",
        trace=[
            TraceStep(
                kind="tool",
                name="search",
                arguments={"q": "Paris"},
                expected_name="search",
                expected_arguments={"q": "Paris"},
            )
        ],
        threshold=0.5,
    )
    assert scored.score == 1.0
    reference = seen["reference_tool_calls"]
    assert reference[0].kwargs == {"name": "search", "args": {"q": "Paris"}}  # type: ignore[index]
