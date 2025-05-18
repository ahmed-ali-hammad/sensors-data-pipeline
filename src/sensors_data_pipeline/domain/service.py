import io
import logging
import time
from datetime import datetime
from typing import AsyncGenerator, Generator, Iterator

import pandas as pd
from minio import Minio
from minio.datatypes import Object
from pandantic import Pandantic  # type: ignore[import-untyped]

from sensors_data_pipeline.db.repository import DatabaseRepository
from sensors_data_pipeline.domain.validators import (
    SensorInfoValidator,
    SensorMeasurementValidator,
)

_logger = logging.getLogger(__name__)


class SensorDataService:
    def __init__(
        self,
        minio_client: Minio,
        database_repository: DatabaseRepository,
        bucket_name: str = "code-challenge-data",
        chunk_size: int = 5000,
    ) -> None:
        self.minio_client = minio_client
        self.database_repository = database_repository
        self.bucket_name = bucket_name
        self.chunk_size = chunk_size

    def _read_csv_file_from_minio(
        self,
        object_name: str,
        required_columns: list,
        separator: str = ";",
    ) -> Iterator[pd.DataFrame]:
        """
        Reads a CSV file from MinIO and returns an iterator of DataFrame chunks.

        Args:
            object_name (str): Name of the object in the MinIO bucket.
            separator (str): CSV separator. Defaults to ';'.

        Returns:
            Iterator[pd.DataFrame]: Iterator over DataFrame chunks.
        """
        response = self.minio_client.get_object(
            bucket_name=self.bucket_name, object_name=object_name
        )
        return pd.read_csv(
            io.BytesIO(response.data),
            sep=separator,
            chunksize=self.chunk_size,
            usecols=required_columns,
        )

    async def _get_sensors_measurement_files_paginated(self) -> Generator[Object]:
        """
        Retrieves sensor measurement files from MinIO.

        Returns:
            Generator[Object]: A generator yielding MinIO objects under the 'timeseries/' prefix.
        """
        objects = self.minio_client.list_objects(
            self.bucket_name,
            prefix="timeseries/",
            recursive=True,
        )
        return objects

    def _validate_sensors_data(self, chunk: pd.DataFrame) -> list[dict]:
        """
        Validates a DataFrame chunk using the SensorInfoValidator.

        Args:
            chunk (pd.DataFrame): A chunk of sensor data.

        Returns:
            list[dict]: A list of validated rows as dictionaries.
        """
        validator = Pandantic(schema=SensorInfoValidator)
        valid_df = validator.validate(dataframe=chunk, errors="skip")

        # "records" creates a list of dictionaries, one dict per row
        return valid_df.to_dict("records")

    def _preprocess_sensors_measurements_timestamps(
        self, chunk: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Parses and localizes timestamps in the sensor measurements.

        This method expects the 'timestamp' column to contain both timezone-aware and naive values.
        It converts the column to datetime and localizes naive timestamps to 'Europe/Berlin'.

        Args:
            chunk (pd.DataFrame): A DataFrame containing a 'timestamp' column.

        Returns:
            pd.DataFrame: The updated DataFrame with processed timestamps.
        """
        chunk["timestamp"] = pd.to_datetime(
            chunk["timestamp"], format="ISO8601", utc=False
        )

        def localize_if_naive(timestamp):
            return (
                timestamp.tz_localize("Europe/Berlin", ambiguous=True)
                if timestamp.tzinfo is None
                else timestamp
            )

        chunk["timestamp"] = chunk["timestamp"].apply(localize_if_naive)
        return chunk

    def _validate_sensors_measurements_data(self, chunk: pd.DataFrame) -> list[dict]:
        """
        Preprocesses and validates a chunk of sensor measurement data.

        Applies timestamp parsing and timezone handling, then validates the
        cleaned data using the SensorMeasurementValidator schema.

        Args:
            chunk (pd.DataFrame): Raw sensor measurements data.

        Returns:
            list[dict]: List of valid records as dictionaries.
        """
        chunk = self._preprocess_sensors_measurements_timestamps(chunk)

        validator = Pandantic(schema=SensorMeasurementValidator)
        valid_df = validator.validate(dataframe=chunk, errors="skip")

        # records creates a list of dictionaries, one dict per row
        return valid_df.to_dict("records")

    async def get_and_store_sensors_information(self) -> None:
        """
        Reads, validates, and stores sensor metadata from MinIO to the database.

        Processes the mapping CSV in chunks, validates each chunk,
        and stores valid records asynchronously.
        """
        _logger.info("Fetching and storing sensors metadata...")
        sensors_data_csv_chunks = self._read_csv_file_from_minio(
            object_name="mapping/mapping.csv",
            required_columns=["sensor_uuid", "sensor_name"],
        )

        for index, chunk in enumerate(sensors_data_csv_chunks):
            _logger.info(
                f"Processing sensors data — batch {index + 1} with {self.chunk_size} rows."
            )
            sensors_records = self._validate_sensors_data(chunk)

            if sensors_records:
                await self.database_repository.store_sensors_data(
                    sensor_records=sensors_records
                )

        _logger.info("Sensors metadata processed successfully.")

    async def get_and_store_sensors_measurements(self) -> None:
        """
        Reads sensors measurement CSV files from MinIO, validates their contents,
        and stores the valid records into the database.
        """
        _logger.info("Fetching and storing sensors measurements...")

        sensors_measurement_files_generator = (
            await self._get_sensors_measurement_files_paginated()
        )

        start_time = time.time()
        for index, object in enumerate(sensors_measurement_files_generator):
            _logger.info(
                f"count: {index + 1} - processing sensors measurements file: '{object.object_name}'"
            )

            if object.object_name is None:
                _logger.warning(
                    f"Skipping object at index {index + 1} with `None` name"
                )
                continue

            sensors_measurements_csv_chunks = self._read_csv_file_from_minio(
                object_name=object.object_name,
                required_columns=["timestamp", "sensor_uuid", "sensor_value"],
            )

            for chunk in sensors_measurements_csv_chunks:
                sensors_measurements = self._validate_sensors_measurements_data(chunk)

                if sensors_measurements:
                    await self.database_repository.store_sensors_measurements(
                        sensors_measurements=sensors_measurements
                    )

            _logger.info(f"Elapsed time: {time.time() - start_time:.2f} seconds")
        _logger.info("Sensors measurements processed successfully.")

    async def get_sensor_readings(
        self,
        sensor_name: str,
        start_timestamp: datetime,
        end_timestamp: datetime,
        page_number: int | None = None,
        page_size: int | None = None,
    ) -> AsyncGenerator[pd.DataFrame, None]:
        """
        Yields sensor readings batches as pandas DataFrames for a given sensor name
        within a specified time range. Supports optional pagination.

        Args:
            sensor_name (str): The name of the sensor to retrieve readings for.
            start_timestamp (datetime): Start of the time range.
            end_timestamp (datetime): End of the time range.
            page_number (int | None): Optional page number for pagination.
            page_size (int | None): Optional number of records per page.

        Yields:
            pd.DataFrame: A DataFrame containing rows of sensor values and their corresponding timestamps.

        Notes:
            - If the sensor is not found, the method logs the event and exits.
            - Data is retrieved in batches of up to 500 rows (or smaller if limited by page size).
        """

        sensor = await self.database_repository.get_sensor_by_sensor_name(
            sensor_name=sensor_name
        )

        if sensor is None:
            _logger.info(f"Sensor {sensor_name} is not found.")
            return

        total_yielded = 0
        default_batch_size = 500
        offset = (page_number - 1) * page_size if page_number and page_size else 0

        while True:
            if page_size is not None:
                remaining = page_size - total_yielded
                if remaining <= 0:
                    break
                current_batch_size = min(default_batch_size, remaining)
            else:
                current_batch_size = default_batch_size
            sensor_measurements = await self.database_repository.get_sensor_measurements_by_sensor_uuid_and_time_range(
                sensor_uuid=sensor.sensor_uuid,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                offset=offset,
                batch_size=current_batch_size,
            )

            if not sensor_measurements:
                if not total_yielded:
                    # In case no readings were returned
                    _logger.info(
                        "No sensor readings found for the given time range. "
                        "If you provided pagination parameters, consider adjusting the page number or page size."
                    )
                break

            yield pd.DataFrame(
                sensor_measurements, columns=["sensor_value", "timestamp"]
            )

            num_rows = len(sensor_measurements)
            offset += num_rows
            total_yielded += num_rows
