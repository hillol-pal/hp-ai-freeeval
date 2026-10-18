from pathlib import Path

import pytest
from pydantic import ValidationError

from freeeval.config import Settings

ROOT = Path(__file__).resolve().parents[1]
ENV_VARS = (
    "FREEEVAL_HOST",
    "FREEEVAL_PORT",
    "FREEEVAL_LOG_LEVEL",
    "FREEEVAL_ENV",
)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_defaults_when_unset(clean_env: None) -> None:
    settings = Settings()
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.log_level == "info"
    assert settings.environment == "local"


def test_each_variable_overrides_default(clean_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FREEEVAL_HOST", "0.0.0.0")
    monkeypatch.setenv("FREEEVAL_PORT", "9001")
    monkeypatch.setenv("FREEEVAL_LOG_LEVEL", "debug")
    monkeypatch.setenv("FREEEVAL_ENV", "ci")
    settings = Settings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 9001
    assert settings.log_level == "debug"
    assert settings.environment == "ci"


@pytest.mark.parametrize("port", ["abc", "0"])
def test_invalid_port_is_rejected(clean_env: None, monkeypatch: pytest.MonkeyPatch, port: str) -> None:
    monkeypatch.setenv("FREEEVAL_PORT", port)
    with pytest.raises(ValidationError):
        Settings()


def test_env_example_lists_defaults() -> None:
    values: dict[str, str] = {}
    for line in (ROOT / ".env.example").read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, value = stripped.split("=", 1)
        values[key] = value
    assert values == {
        "FREEEVAL_HOST": "127.0.0.1",
        "FREEEVAL_PORT": "8000",
        "FREEEVAL_LOG_LEVEL": "info",
        "FREEEVAL_ENV": "local",
    }
