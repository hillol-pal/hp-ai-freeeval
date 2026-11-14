import os

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="127.0.0.1", validation_alias="FREEEVAL_HOST")
    port: int = Field(default=8000, ge=1, le=65535, validation_alias="FREEEVAL_PORT")
    log_level: str = Field(default="info", validation_alias="FREEEVAL_LOG_LEVEL")
    environment: str = Field(default="local", validation_alias="FREEEVAL_ENV")
    deepeval_model: str = Field(
        default="gpt-4o-mini", validation_alias="FREEEVAL_DEEPEVAL_MODEL"
    )
    openai_api_key: SecretStr | None = Field(
        default=None, validation_alias="OPENAI_API_KEY"
    )
    phoenix_collector_endpoint: str | None = Field(
        default=None, validation_alias="PHOENIX_COLLECTOR_ENDPOINT"
    )
    phoenix_project_name: str | None = Field(
        default=None, validation_alias="PHOENIX_PROJECT_NAME"
    )
    phoenix_api_key: SecretStr | None = Field(
        default=None, validation_alias="PHOENIX_API_KEY"
    )
    phoenix_enabled: str | None = Field(
        default=None, validation_alias="FREEEVAL_PHOENIX_ENABLED"
    )

    def export_phoenix_environment(self) -> None:
        """Copy Phoenix settings into the process environment when unset.

        configure_phoenix() reads os.environ. A value already in the process
        stays in place. Settings has already applied .env for the rest.
        """
        values: dict[str, str | None] = {
            "PHOENIX_COLLECTOR_ENDPOINT": self.phoenix_collector_endpoint,
            "PHOENIX_PROJECT_NAME": self.phoenix_project_name,
            "FREEEVAL_PHOENIX_ENABLED": self.phoenix_enabled,
            "PHOENIX_API_KEY": (
                None if self.phoenix_api_key is None else self.phoenix_api_key.get_secret_value()
            ),
        }
        for key, value in values.items():
            if value is None or key in os.environ:
                continue
            os.environ[key] = value
