import pytest
from pydantic import ValidationError

from freeeval.api.schemas import (
    AgentCase,
    AgentEvaluationRequest,
    AgentStep,
    CodeCase,
    CodeEvaluationRequest,
    Context,
    PromptEvaluationRequest,
    RagCase,
    RagEvaluationRequest,
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
        cases=[
            RagCase(
                id="r1",
                question="Capital of France?",
                answer="Paris",
                contexts=[Context(id="c1", text="Paris is the capital.")],
                expected_answer="Paris",
                relevant_context_ids=["c1"],
            )
        ]
    )
    agent = AgentEvaluationRequest(
        cases=[
            AgentCase(
                id="a1",
                task="Find the capital",
                output="Paris",
                steps=[AgentStep(kind="tool", name="search")],
                expected_output="Paris",
            )
        ]
    )
    assert prompt.prompt == "What is 2+2?"
    assert prompt.metrics[0].name == "answer_relevancy"
    assert prompt.metrics[0].threshold == 0.7
    assert code.cases[0].code == "print(2 + 2)"
    assert rag.cases[0].contexts[0].id == "c1"
    assert agent.cases[0].steps[0].kind == "tool"


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
        RagEvaluationRequest(
            cases=[
                RagCase(id="r1", question="q", answer="a", contexts=[]),
                RagCase(id="r1", question="q", answer="b", contexts=[]),
            ]
        )


def test_rejects_unknown_agent_step_kind() -> None:
    with pytest.raises(ValidationError):
        AgentStep.model_validate({"kind": "browse", "name": "search"})
