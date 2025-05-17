from sqlalchemy.dialects.postgresql import insert

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

        Args:
            sensors_measurements (list): A list of dictionaries, each representing a sensor measurement.
        """
        async with self.database_manager.get_timescale_db_session() as session:
            statement = insert(SensorMeasurement).values(sensors_measurements)
            await session.execute(statement)
            await session.commit()
