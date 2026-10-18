from pydantic import Field
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
