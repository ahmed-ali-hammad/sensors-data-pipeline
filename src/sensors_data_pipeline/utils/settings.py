from functools import lru_cache

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration class.

    This class uses Pydantic's `BaseSettings` to manage and validate
    environment variables.
    """

    LOG_LEVEL: str = "INFO"
    MINIO_ENDPOINT: str
    MINIO_HTTPS_PROTOCOL: bool
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str

    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    ASYNC_DB_URI: str | None = None

    TIMESCALE_DB_HOST: str
    TIMESCALE_DB_PORT: int
    TIMESCALE_DB_NAME: str
    TIMESCALE_DB_USER: str
    TIMESCALE_DB_PASSWORD: str
    ASYNC_TIMESCALE_DB_URI: str | None = None

    @field_validator("ASYNC_DB_URI", mode="before")
    def build_async_db_uri(cls, v, info: ValidationInfo):
        values = info.data
        try:
            return f"postgresql+asyncpg://{values['DB_USER']}:{values['DB_PASSWORD']}@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}"
        except KeyError as e:
            raise ValueError(f"Missing database configuration value: {e}")

    @field_validator("ASYNC_TIMESCALE_DB_URI", mode="before")
    def build_async_timescale_db_uri(cls, v, info: ValidationInfo):
        values = info.data
        try:
            return f"postgresql+asyncpg://{values['TIMESCALE_DB_USER']}:{values['TIMESCALE_DB_PASSWORD']}@{values['TIMESCALE_DB_HOST']}:{values['TIMESCALE_DB_PORT']}/{values['TIMESCALE_DB_NAME']}"
        except KeyError as e:
            raise ValueError(f"Missing database configuration value: {e}")


@lru_cache()
def get_env_settings() -> Settings:
    return Settings()
