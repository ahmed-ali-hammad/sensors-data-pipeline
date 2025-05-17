import uuid
from datetime import datetime

from sqlalchemy import BIGINT, FLOAT
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SensorMeasurement(Base):
    """
    ORM model representing a single measurement recorded by a sensor.
    """

    __tablename__ = "sensor_measurement"

    id: Mapped[int] = mapped_column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    sensor_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    sensor_value: Mapped[float] = mapped_column(FLOAT, nullable=False)
