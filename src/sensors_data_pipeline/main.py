import asyncio
import logging

import click
from dateutil.parser import parse

from sensors_data_pipeline.service_factory import check_db_health, create_service
from sensors_data_pipeline.utils.settings import env_settings

logging.basicConfig(
    level=env_settings.LOG_LEVEL,
    format="%(levelname)s:%(asctime)s: %(name)s: %(message)s",
)

_logger = logging.getLogger(__name__)

sensor_data_service = create_service()


def ingest_sensors_data_from_storage():
    async def runner() -> None:
        try:
            await check_db_health(
                sensor_data_service.database_repository.database_manager
            )

            _logger.info("Running worker...")
            await sensor_data_service.get_and_store_sensors_information()
            await sensor_data_service.get_and_store_sensors_measurements()

        except Exception as e:
            _logger.exception(f"Main process failed: {e}")
            raise
        finally:
            _logger.info("Cleaning up DB resources...")
            await sensor_data_service.database_repository.database_manager.dispose_engine()

    asyncio.run(runner())


@click.command()
@click.option("--sensor-name", required=True)
@click.option("--start-timestamp", required=True)
@click.option("--end-timestamp", required=True)
@click.option("--page-number", type=int)
@click.option("--page-size", type=int)
def retrieve_sensor_readings(
    sensor_name, start_timestamp, end_timestamp, page_number, page_size
):

    start_ts = parse(start_timestamp)
    end_ts = parse(end_timestamp)

    async def runner():
        show_header = True
        async for df in sensor_data_service.get_sensor_readings(
            sensor_name, start_ts, end_ts, page_number, page_size
        ):
            print(df.to_string(index=False, header=show_header))
            show_header = False

    asyncio.run(runner())
