import inspect
import logging
import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from freeeval.main import main

ENV_VARS = (
    "FREEEVAL_HOST",
    "FREEEVAL_PORT",
    "FREEEVAL_LOG_LEVEL",
    "FREEEVAL_ENV",
)


def test_main_passes_configured_host_and_port(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}
    setup_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_run(*args: object, **kwargs: object) -> None:
        captured["args"] = args
        captured["kwargs"] = kwargs

    def fake_setup(*args: object, **kwargs: object) -> None:
        setup_calls.append((args, kwargs))

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FREEEVAL_HOST", "0.0.0.0")
    monkeypatch.setenv("FREEEVAL_PORT", "9001")
    monkeypatch.setenv("FREEEVAL_LOG_LEVEL", "debug")
    monkeypatch.setenv("FREEEVAL_ENV", "ci")
    monkeypatch.setattr("freeeval.main.setup_logging", fake_setup)
    monkeypatch.setattr("freeeval.main.uvicorn.run", fake_run)
    with caplog.at_level(logging.INFO, logger="freeeval"):
        main()
    assert captured["kwargs"]["host"] == "0.0.0.0"
    assert captured["kwargs"]["port"] == 9001
    assert captured["kwargs"]["log_config"] is None
    assert setup_calls == [((), {"level": "debug"})]
    assert "environment=ci" in caplog.text


def test_main_logs_default_environment(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("freeeval.main.uvicorn.run", lambda *args, **kwargs: None)
    with caplog.at_level(logging.INFO, logger="freeeval"):
        main()
    matches = [
        record
        for record in caplog.records
        if record.name == "freeeval" and record.getMessage() == "environment=local"
    ]
    assert len(matches) == 1


def test_main_copies_phoenix_file_values_before_registration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    for name in (
        "FREEEVAL_PHOENIX_ENABLED",
        "PHOENIX_COLLECTOR_ENDPOINT",
        "PHOENIX_PROJECT_NAME",
        "PHOENIX_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    (tmp_path / ".env").write_text(
        "FREEEVAL_PHOENIX_ENABLED=true\n"
        "PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006\n"
        "PHOENIX_PROJECT_NAME=from-file\n"
        "PHOENIX_API_KEY=file-key\n"
    )
    seen: dict[str, str | None] = {}

    def capture() -> None:
        seen["enabled"] = os.environ.get("FREEEVAL_PHOENIX_ENABLED")
        seen["endpoint"] = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT")
        seen["project"] = os.environ.get("PHOENIX_PROJECT_NAME")
        seen["key"] = os.environ.get("PHOENIX_API_KEY")

    monkeypatch.setattr("freeeval.api.app.configure_phoenix", capture)
    monkeypatch.setattr("freeeval.main.uvicorn.run", lambda *args, **kwargs: None)
    main()
    assert seen == {
        "enabled": "true",
        "endpoint": "http://localhost:6006",
        "project": "from-file",
        "key": "file-key",
    }


def test_main_keeps_phoenix_values_already_in_the_process(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PHOENIX_COLLECTOR_ENDPOINT", raising=False)
    monkeypatch.delenv("PHOENIX_API_KEY", raising=False)
    monkeypatch.setenv("FREEEVAL_PHOENIX_ENABLED", "false")
    monkeypatch.setenv("PHOENIX_PROJECT_NAME", "from-process")
    (tmp_path / ".env").write_text(
        "FREEEVAL_PHOENIX_ENABLED=true\n"
        "PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006\n"
        "PHOENIX_PROJECT_NAME=from-file\n"
    )
    seen: dict[str, str | None] = {}

    def capture() -> None:
        seen["enabled"] = os.environ.get("FREEEVAL_PHOENIX_ENABLED")
        seen["endpoint"] = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT")
        seen["project"] = os.environ.get("PHOENIX_PROJECT_NAME")

    monkeypatch.setattr("freeeval.api.app.configure_phoenix", capture)
    monkeypatch.setattr("freeeval.main.uvicorn.run", lambda *args, **kwargs: None)
    main()
    assert seen == {
        "enabled": "false",
        "endpoint": "http://localhost:6006",
        "project": "from-process",
    }


def test_main_does_not_call_basic_config() -> None:
    assert "basicConfig" not in inspect.getsource(main)


def test_invalid_port_does_not_start_server(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"uvicorn": 0, "setup": 0}

    def fake_run(*args: object, **kwargs: object) -> None:
        calls["uvicorn"] += 1

    def fake_setup(*args: object, **kwargs: object) -> None:
        calls["setup"] += 1

    monkeypatch.setenv("FREEEVAL_PORT", "abc")
    monkeypatch.setattr("freeeval.main.uvicorn.run", fake_run)
    monkeypatch.setattr("freeeval.main.setup_logging", fake_setup)
    with pytest.raises(ValidationError):
        main()
    assert calls["uvicorn"] == 0
    assert calls["setup"] == 0
