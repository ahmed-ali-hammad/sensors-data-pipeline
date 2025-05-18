import pytest
from minio import Minio
from pydantic import ValidationError

from sensors_data_pipeline.utils.minio_client import MinioManager
from sensors_data_pipeline.utils.settings import Settings


@pytest.mark.asyncio
class TestSettings:

    async def test_settings_builds_db_uri_success(self, monkeypatch):
        monkeypatch.setenv("DB_USER", "db_hero")
        monkeypatch.setenv("DB_PASSWORD", "supersecret123")
        monkeypatch.setenv("DB_HOST", "database-central.de")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "test-db")

        monkeypatch.setenv("TIMESCALE_DB_USER", "time_db_hero")
        monkeypatch.setenv("TIMESCALE_DB_PASSWORD", "supersecret456")
        monkeypatch.setenv("TIMESCALE_DB_HOST", "time-database-central.de")
        monkeypatch.setenv("TIMESCALE_DB_PORT", "5432")
        monkeypatch.setenv("TIMESCALE_DB_NAME", "test-timeseries-db")

        env_settings = Settings()

        assert env_settings.ASYNC_DB_URI == (
            "postgresql+asyncpg://db_hero:supersecret123@database-central.de:5432/test-db"
        )

        assert env_settings.ASYNC_TIMESCALE_DB_URI == (
            "postgresql+asyncpg://time_db_hero:supersecret456@time-database-central.de:5432/test-timeseries-db"
        )

    async def test_settings_raises_error_on_missing_value(self, monkeypatch):
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.setenv("DB_PASSWORD", "supersecret123")
        monkeypatch.setenv("DB_HOST", "database-central.de")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "test-db")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "DB_USER" in str(exc_info.value)
        assert "ASYNC_DB_URI" in str(exc_info.value)

    async def test_minio_https_protocol_parsing(self, monkeypatch):
        monkeypatch.setenv("MINIO_ENDPOINT", "minio.example.com")
        monkeypatch.setenv("MINIO_HTTPS_PROTOCOL", "true")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "minio")
        monkeypatch.setenv("MINIO_SECRET_KEY", "secret")

        monkeypatch.setenv("DB_USER", "db_hero")
        monkeypatch.setenv("DB_PASSWORD", "supersecret123")
        monkeypatch.setenv("DB_HOST", "database-central.de")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "test-db")

        monkeypatch.setenv("TIMESCALE_DB_USER", "time_db_hero")
        monkeypatch.setenv("TIMESCALE_DB_PASSWORD", "supersecret456")
        monkeypatch.setenv("TIMESCALE_DB_HOST", "time-database-central.de")
        monkeypatch.setenv("TIMESCALE_DB_PORT", "5432")
        monkeypatch.setenv("TIMESCALE_DB_NAME", "test-timeseries-db")

        env_settings = Settings()
        assert env_settings.MINIO_HTTPS_PROTOCOL is True


class TestMinioManager:
    def test_get_minio_client_success(self, monkeypatch):
        monkeypatch.setenv("MINIO_ENDPOINT", "minio.example.com")
        monkeypatch.setenv("MINIO_HTTPS_PROTOCOL", "true")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "minio")
        monkeypatch.setenv("MINIO_SECRET_KEY", "secret")

        monkeypatch.setenv("DB_USER", "db_hero")
        monkeypatch.setenv("DB_PASSWORD", "supersecret123")
        monkeypatch.setenv("DB_HOST", "database-central.de")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "test-db")

        monkeypatch.setenv("TIMESCALE_DB_USER", "time_db_hero")
        monkeypatch.setenv("TIMESCALE_DB_PASSWORD", "supersecret456")
        monkeypatch.setenv("TIMESCALE_DB_HOST", "time-database-central.de")
        monkeypatch.setenv("TIMESCALE_DB_PORT", "5432")
        monkeypatch.setenv("TIMESCALE_DB_NAME", "test-timeseries-db")

        env_settings = Settings()

        minio_manager = MinioManager(
            minio_endpoint=env_settings.MINIO_ENDPOINT,
            minio_access_key=env_settings.MINIO_ACCESS_KEY,
            minio_secret_key=env_settings.MINIO_SECRET_KEY,
            is_secure=env_settings.MINIO_HTTPS_PROTOCOL,
        )
        minio_client = minio_manager.get_minio_client()

        assert isinstance(minio_client, Minio)

    def test_minio_client_is_singleton(self, monkeypatch):
        monkeypatch.setenv("MINIO_ENDPOINT", "minio.example.com")
        monkeypatch.setenv("MINIO_HTTPS_PROTOCOL", "true")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "minio")
        monkeypatch.setenv("MINIO_SECRET_KEY", "secret")

        monkeypatch.setenv("DB_USER", "db_hero")
        monkeypatch.setenv("DB_PASSWORD", "supersecret123")
        monkeypatch.setenv("DB_HOST", "database-central.de")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "test-db")

        monkeypatch.setenv("TIMESCALE_DB_USER", "time_db_hero")
        monkeypatch.setenv("TIMESCALE_DB_PASSWORD", "supersecret456")
        monkeypatch.setenv("TIMESCALE_DB_HOST", "time-database-central.de")
        monkeypatch.setenv("TIMESCALE_DB_PORT", "5432")
        monkeypatch.setenv("TIMESCALE_DB_NAME", "test-timeseries-db")

        env_settings = Settings()
        minio_manager = MinioManager(
            env_settings.MINIO_ENDPOINT,
            env_settings.MINIO_ACCESS_KEY,
            env_settings.MINIO_SECRET_KEY,
            env_settings.MINIO_HTTPS_PROTOCOL,
        )

        first_client = minio_manager.get_minio_client()
        second_client = minio_manager.get_minio_client()

        assert first_client is second_client
