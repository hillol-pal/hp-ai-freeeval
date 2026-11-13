import pytest
from pydantic import ValidationError

from freeeval.api.schemas import (
    AgentEvaluationRequest,
    CodeCase,
    CodeEvaluationRequest,
    PromptEvaluationRequest,
    RagEvaluationRequest,
    TraceEvent,
)


def test_accepts_one_valid_payload_per_use_case() -> None:
    prompt = PromptEvaluationRequest(
        prompt="What is 2+2?",
        answer="4",
        metrics=[{"name": "answer_relevancy", "threshold": 0.7}],
    )
    code = CodeEvaluationRequest(
        cases=[
            CodeCase(id="c1", code="print(2 + 2)", output="4", expected="4"),
        ]
    )
    rag = RagEvaluationRequest(
        query="Capital of France?",
        actual_response="Paris",
        retrieved_contexts=["Paris is the capital."],
        metrics=[{"name": "faithfulness", "threshold": 0.5}],
        metadata={"source": "unit"},
    )
    agent = AgentEvaluationRequest(
        input="Find the capital",
        actual_output="Paris",
        execution_trace=[TraceEvent(kind="tool", name="search")],
        metrics=[{"name": "task_success_rate", "threshold": 0.5}],
        metadata={"source": "unit"},
    )
    assert prompt.prompt == "What is 2+2?"
    assert prompt.metrics[0].name == "answer_relevancy"
    assert prompt.metrics[0].threshold == 0.7
    assert code.cases[0].code == "print(2 + 2)"
    assert rag.query == "Capital of France?"
    assert rag.retrieved_contexts == ["Paris is the capital."]
    assert rag.metadata == {"source": "unit"}
    assert agent.input == "Find the capital"
    assert agent.execution_trace[0].kind == "tool"
    assert agent.metadata == {"source": "unit"}


def test_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        PromptEvaluationRequest.model_validate(
            {
                "prompt": "q",
                "answer": "a",
                "metrics": [{"name": "answer_relevancy", "threshold": 0.5}],
                "note": "extra",
            }
        )


def test_rejects_empty_prompt() -> None:
    with pytest.raises(ValidationError):
        PromptEvaluationRequest(
            prompt="",
            answer="4",
            metrics=[{"name": "answer_relevancy", "threshold": 0.5}],
        )


def test_rejects_duplicate_case_id() -> None:
    with pytest.raises(ValidationError):
        CodeEvaluationRequest(
            cases=[
                CodeCase(id="c1", code="print(1)", output="1"),
                CodeCase(id="c1", code="print(2)", output="2"),
            ]
        )


def test_rejects_duplicate_rag_metrics() -> None:
    with pytest.raises(ValidationError):
        RagEvaluationRequest(
            query="q",
            actual_response="a",
            retrieved_contexts=[],
            metrics=[
                {"name": "faithfulness", "threshold": 0.2},
                {"name": "faithfulness", "threshold": 0.8},
            ],
        )


def test_rejects_unknown_agent_step_kind() -> None:
    with pytest.raises(ValidationError):
        TraceEvent.model_validate({"kind": "browse", "name": "search"})
