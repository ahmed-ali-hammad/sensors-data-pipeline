from datetime import datetime
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Row

from sensors_data_pipeline.db.main import DatabaseManager
from sensors_data_pipeline.db.models.main.sensor_info import SensorInfo
from sensors_data_pipeline.db.models.timescale.sensor_measurement import (
    SensorMeasurement,
)


class DatabaseRepository:
    """
    Repository class for handling database operations.
    """

    def __init__(self, database_manager: DatabaseManager) -> None:
        """
        Initializes a DatabaseRepository with a given database manager.

        Args:
            database_manager (DatabaseManager): An instance responsible for providing database sessions.
        """
        self.database_manager = database_manager

    async def store_sensors_data(self, sensor_records: list) -> None:
        """
        Inserts sensors metadata records into the database.

        If a sensor with the same UUID already exists, the record is skipped (no overwrite).

        Args:
            sensor_records (list): A list of dictionaries containing sensors metadata to be saved.
        """
        async with self.database_manager.get_db_session() as session:
            statement = (
                insert(SensorInfo)
                .values(sensor_records)
                .on_conflict_do_nothing(index_elements=[SensorInfo.sensor_uuid])
            )
            await session.execute(statement)
            await session.commit()

    async def store_sensors_measurements(self, sensors_measurements: list) -> None:
        """
        Inserts a list of sensors measurements into the database.

        This method uses a TimescaleDB session to perform a bulk insert.

        If a measurement with the same sensor_uuid and timestamp exists, the record is skipped (no overwrite).

        Args:
            sensors_measurements (list): A list of dictionaries, each representing a sensor measurement.
        """
        async with self.database_manager.get_timescale_db_session() as session:
            statement = (
                insert(SensorMeasurement)
                .values(sensors_measurements)
                .on_conflict_do_nothing(
                    index_elements=[
                        SensorMeasurement.sensor_uuid,
                        SensorMeasurement.timestamp,
                    ]
                )
            )
            await session.execute(statement)
            await session.commit()

    async def get_sensor_by_sensor_name(self, sensor_name: str) -> SensorInfo | None:
        """
        Retrieve a sensor record from the database by its sensor name.

        Args:
            sensor_name (str): The unique name of the sensor to look up.

        Returns:
            SensorInfo | None: The matching SensorInfo object if found, otherwise None.
        """
        async with self.database_manager.get_db_session() as session:
            statement = select(SensorInfo).where(SensorInfo.sensor_name == sensor_name)
            result = await session.execute(statement)

            return result.scalar_one_or_none()

    async def get_sensor_measurements_by_sensor_uuid_and_time_range(
        self,
        sensor_uuid: UUID,
        start_timestamp: datetime,
        end_timestamp: datetime,
        offset: int,
        batch_size: int = 1000,
    ) -> Sequence[Row[tuple[float, datetime]]]:
        """
        Fetches a paginated list of sensor measurements for a given sensor UUID
        within a specified time range.

        Args:
            sensor_uuid (UUID): The UUID of the sensor to retrieve measurements for.
            start_timestamp (datetime): Start of the time range.
            end_timestamp (datetime): End of the time range.
            offset (int): Number of records to skip (used for pagination).
            batch_size (int, optional): Maximum number of records to return. Defaults to 1000.

        Returns:
            Sequence[Row[tuple[float, datetime]]]: A sequence of SQLAlchemy Row objects,
            each containing a sensor value and its corresponding timestamp.
        """
        async with self.database_manager.get_timescale_db_session() as session:
            statement = (
                select(SensorMeasurement.sensor_value, SensorMeasurement.timestamp)
                .where(
                    (SensorMeasurement.sensor_uuid == sensor_uuid)
                    & (SensorMeasurement.timestamp >= start_timestamp)
                    & (SensorMeasurement.timestamp <= end_timestamp)
                )
                .order_by(SensorMeasurement.timestamp)
                .limit(batch_size)
                .offset(offset)
            )

            result = await session.execute(statement)
            return result.all()
