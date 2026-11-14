from pathlib import Path

README = (Path(__file__).resolve().parents[1] / "README.md").read_text()


def test_readme_documents_startup() -> None:
    for name in (
        "FREEEVAL_HOST",
        "FREEEVAL_PORT",
        "FREEEVAL_LOG_LEVEL",
        "FREEEVAL_ENV",
        "python -m freeeval",
        "GET /health",
    ):
        assert name in README


def test_readme_documents_prompt_example() -> None:
    assert "POST /apis/endpoints/prompts/evaluations" in README
    for field in ('"prompt"', '"answer"', '"metrics"', '"threshold"'):
        assert field in README


def test_readme_documents_code_example() -> None:
    assert "POST /apis/endpoints/code/evaluations" in README
    for field in ('"code"', '"output"', '"expected"'):
        assert field in README


def test_readme_documents_rag_example() -> None:
    assert "POST /apis/endpoints/rag/evaluations" in README
    for field in (
        '"query"',
        '"actual_response"',
        '"retrieved_contexts"',
        '"metrics"',
        '"metadata"',
    ):
        assert field in README


def test_readme_lists_metrics_by_category() -> None:
    assert "## Metrics" in README
    for category in ("Code Generation", "Prompt / LLM", "RAG", "AI Agents"):
        assert category in README
    for name in (
        "maintainability",
        "readability",
        "robustness",
        "secured_code",
        "extensibility",
        "answer_correctness",
        "instruction_following_rate",
        "answer_relevancy",
        "format_compliance_rate",
        "hallucination_rate",
        "faithfulness",
        "context_precision",
        "context_recall",
        "task_success_rate",
        "tool_call_accuracy",
        "task_reliability",
    ):
        assert f"`{name}`" in README


def test_readme_documents_agent_example_and_limits() -> None:
    assert "POST /apis/endpoints/agents/evaluations" in README
    for field in (
        '"input"',
        '"actual_output"',
        '"execution_trace"',
        '"metrics"',
        '"metadata"',
    ):
        assert field in README
    assert "Runs are not stored." in README
    assert "agent `metadata` are accepted and are not scored." in README
