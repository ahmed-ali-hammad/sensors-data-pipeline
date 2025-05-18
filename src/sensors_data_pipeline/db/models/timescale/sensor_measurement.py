import uuid
from datetime import datetime

from sqlalchemy import BIGINT, FLOAT, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SensorMeasurement(Base):
    """
    ORM model representing a single measurement recorded by a sensor.
    """

    __tablename__ = "sensor_measurement"

    __table_args__ = (
        UniqueConstraint("sensor_uuid", "timestamp", name="uq_sensor_timestamp"),
    )

    id: Mapped[int] = mapped_column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )  # timestamps are stored in UTC
    sensor_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    sensor_value: Mapped[float] = mapped_column(FLOAT, nullable=False)
