from sensors_data_pipeline.db.main import DatabaseManager
from sensors_data_pipeline.db.repository import DatabaseRepository
from sensors_data_pipeline.domain.service import SensorDataService
from sensors_data_pipeline.utils.minio_client import MinioManager
from sensors_data_pipeline.utils.settings import env_settings


def create_service() -> SensorDataService:
    assert (
        env_settings.ASYNC_DB_URI is not None
        and env_settings.ASYNC_TIMESCALE_DB_URI is not None
    )
    db_manager = DatabaseManager(
        env_settings.ASYNC_DB_URI,
        env_settings.ASYNC_TIMESCALE_DB_URI,
    )

    db_repo = DatabaseRepository(database_manager=db_manager)

    minio_manager = MinioManager(
        minio_endpoint=env_settings.MINIO_ENDPOINT,
        minio_access_key=env_settings.MINIO_ACCESS_KEY,
        minio_secret_key=env_settings.MINIO_SECRET_KEY,
        is_secure=env_settings.MINIO_HTTPS_PROTOCOL,
    )
    minio_client = minio_manager.get_minio_client()

    return SensorDataService(
        minio_client=minio_client,
        database_repository=db_repo,
    )


async def check_db_health(db_manager: DatabaseManager):
    if not await db_manager.check_main_db_connection():
        raise RuntimeError("Main DB unreachable")
    if not await db_manager.check_timescale_db_connection():
        raise RuntimeError("Timescale DB unreachable")
