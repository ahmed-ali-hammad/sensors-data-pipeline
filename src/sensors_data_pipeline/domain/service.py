import io
import logging
from typing import Generator, Iterator

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
        chunk_size: int = 100,
    ) -> None:
        self.minio_client = minio_client
        self.database_repository = database_repository
        self.bucket_name = bucket_name
        self.chunk_size = chunk_size

    def _read_sensors_data_csv_file_from_minio(
        self, object_name: str, separator: str = ";"
    ) -> Iterator[pd.DataFrame]:
        response = self.minio_client.get_object(
            bucket_name=self.bucket_name, object_name=object_name
        )
        return pd.read_csv(
            io.BytesIO(response.data), sep=separator, chunksize=self.chunk_size
        )

    def _read_sensors_measurements_csv_file_from_minio(
        self, object_name: str, separator: str = ";"
    ) -> Iterator[pd.DataFrame]:
        response = self.minio_client.get_object(
            bucket_name=self.bucket_name, object_name=object_name
        )
        return pd.read_csv(
            io.BytesIO(response.data),
            sep=separator,
            chunksize=self.chunk_size,
            index_col=0,
        )

    async def _get_sensors_measurement_files_paginated(self) -> Generator[Object]:
        # list_objects returns a generator
        objects = self.minio_client.list_objects(
            self.bucket_name,
            prefix="timeseries/",
            recursive=True,
        )
        return objects

    def _validate_sensors_data(self, chunk: pd.DataFrame) -> list[dict]:
        validator = Pandantic(schema=SensorInfoValidator)
        valid_df = validator.validate(dataframe=chunk, errors="skip")

        # "records" creates a list of dictionaries, one dict per row
        return valid_df.to_dict("records")

    def _validate_sensors_measurements_data(self, chunk: pd.DataFrame) -> list[dict]:
        chunk["timestamp"] = pd.to_datetime(
            chunk["timestamp"], format="%Y-%m-%d %H:%M:%S%z"
        ).dt.tz_convert(None)

        validator = Pandantic(schema=SensorMeasurementValidator)
        valid_df = validator.validate(dataframe=chunk, errors="skip")

        # records creates a list of dictionaries, one dict per row
        return valid_df.to_dict("records")

    async def get_and_store_sensors_information(self) -> None:
        _logger.info("Fetching and storing sensors metadata...")
        sensors_data_csv_chunks = self._read_sensors_data_csv_file_from_minio(
            object_name="mapping/mapping.csv"
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

    async def get_and_store_sensor_measurements(self):
        _logger.info("Fetching and storing sensors measurements...")

        sensors_measurement_files_generator = (
            await self._get_sensors_measurement_files_paginated()
        )

        for index, object in enumerate(sensors_measurement_files_generator):
            _logger.info(
                f"Processing file: '{object.object_name}' for sensors measurements. Index: {index + 1}"
            )
            sensors_measurements_csv_chunks = (
                self._read_sensors_measurements_csv_file_from_minio(
                    object_name=object.object_name
                )
            )

            for chunk in sensors_measurements_csv_chunks:
                sensors_measurements = self._validate_sensors_measurements_data(chunk)

                if sensors_measurements:
                    await self.database_repository.store_sensors_measurements(
                        sensors_measurements=sensors_measurements
                    )

        _logger.info("Sensors measurements processed successfully.")
