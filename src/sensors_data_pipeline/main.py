import asyncio
import logging
import time

from minio import Minio

from sensors_data_pipeline.db.main import DatabaseManager
from sensors_data_pipeline.db.repository import DatabaseRepository
from sensors_data_pipeline.domain.service import SensorDataService
from sensors_data_pipeline.minio_client import MinioManager
from sensors_data_pipeline.settings import env_settings

# Setup logging configuration
logging.basicConfig(
    level=env_settings.LOG_LEVEL,
    format="%(levelname)s:%(asctime)s: %(name)s: %(message)s",
)

_logger = logging.getLogger(__name__)


async def run_worker(
    minio_client: Minio, database_repository: DatabaseRepository
) -> None:
    _logger.info("Starting the worker process...")

    service = SensorDataService(
        minio_client=minio_client,
        database_repository=database_repository,
    )

    await service.get_and_store_sensors_information()

    await service.get_and_store_sensor_measurements()

    _logger.info("Worker process finished successfully.")


async def main() -> None:
    try:
        _logger.info("Initializing Databases...")
        assert (
            env_settings.ASYNC_DB_URI is not None
            and env_settings.ASYNC_TIMESCALE_DB_URI is not None
        )

        database_manager = DatabaseManager(
            env_settings.ASYNC_DB_URI, env_settings.ASYNC_TIMESCALE_DB_URI
        )

        _logger.info("Running Healthcheck for Databases...")
        if not await database_manager.check_main_db_connection():
            raise RuntimeError("Main DB unreachable")

        if not await database_manager.check_timescale_db_connection():
            raise RuntimeError("Timescale DB unreachable")

        database_repository = DatabaseRepository(database_manager=database_manager)
        minio_manager = MinioManager(
            minio_endpoint=env_settings.MINIO_ENDPOINT,
            minio_access_key=env_settings.MINIO_ACCESS_KEY,
            minio_secret_key=env_settings.MINIO_SECRET_KEY,
            is_secure=env_settings.MINIO_HTTPS_PROTOCOL,
        )
        minio_client = minio_manager.get_minio_client()

        _logger.info("Running worker...")

        start_time = time.time()
        await run_worker(minio_client, database_repository)

        _logger.info(f"Worker completed in {time.time() - start_time:.2f} seconds.")

    except Exception as e:
        _logger.exception(f"Main process failed: {e}")
        raise

    finally:
        _logger.info("Cleaning up DB resources...")
        await DatabaseManager.dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
