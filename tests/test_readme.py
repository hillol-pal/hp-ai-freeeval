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
    assert "POST /apis/endpoints/prompts/" in README
    for field in ('"prompt"', '"response"', '"metrics"', '"temperature"', '"threshold"'):
        assert field in README


def test_readme_documents_rag_example() -> None:
    assert "POST /apis/endpoints/rag/evaluations" in README
    for field in ('"question"', '"answer"', '"contexts"', '"expected_answer"'):
        assert field in README


def test_readme_documents_agent_example_and_limits() -> None:
    assert "POST /apis/endpoints/agents/evaluations" in README
    for field in ('"task"', '"output"', '"steps"', '"expected_output"'):
        assert field in README
    assert "Runs are not stored." in README
    assert "Contexts, relevant ids, and steps are accepted but not scored." in README
