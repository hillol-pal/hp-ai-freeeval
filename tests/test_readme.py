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
    for field in ('"question"', '"answer"', '"contexts"', '"expected_answer"'):
        assert field in README


def test_readme_lists_metrics_by_category() -> None:
    assert "## Metrics" in README
    for heading in (
        "### Prompt",
        "### Code",
        "### RAG",
        "### Agents",
        "### Agentic",
        "### Ethical",
        "### Summarisation",
    ):
        assert heading in README
    for name in ("answer_relevancy", "conciseness", "specificity", "code_readability"):
        assert f"`{name}`" in README
    assert "None yet." in README


def test_readme_documents_agent_example_and_limits() -> None:
    assert "POST /apis/endpoints/agents/evaluations" in README
    for field in ('"task"', '"output"', '"steps"', '"expected_output"'):
        assert field in README
    assert "Runs are not stored." in README
    assert "Contexts, relevant ids, and steps are accepted but not scored." in README
