import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SensorInfo(Base):
    """
    ORM model representing metadata for a sensor.
    """

    __tablename__ = "sensor_info"

    sensor_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    sensor_name: Mapped[str] = mapped_column(String(100))
