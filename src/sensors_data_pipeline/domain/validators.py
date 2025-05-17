from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SensorInfoValidator(BaseModel):
    sensor_name: str
    sensor_uuid: UUID


class SensorMeasurementValidator(BaseModel):
    timestamp: datetime
    sensor_uuid: UUID
    sensor_value: float
