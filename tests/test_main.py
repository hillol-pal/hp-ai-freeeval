import inspect
import logging
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
) -> None:
    captured: dict[str, object] = {}
    setup_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_run(*args: object, **kwargs: object) -> None:
        captured["args"] = args
        captured["kwargs"] = kwargs

    def fake_setup(*args: object, **kwargs: object) -> None:
        setup_calls.append((args, kwargs))

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
