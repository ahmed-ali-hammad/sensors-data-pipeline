import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from sensors_data_pipeline.db.repository import DatabaseRepository
from sensors_data_pipeline.domain.service import SensorDataService


@pytest_asyncio.fixture
async def mock_db_session(mocker):
    session = mocker.MagicMock(spec=AsyncSession)
    yield session


@pytest_asyncio.fixture
async def sensor_data_service_test_instance(test_db_session):
    """
    Provide an instance of the BaseService for testing purposes.
    """
    database_repository = DatabaseRepository(test_db_session)
    sensor_data_service = SensorDataService(database_repository)

    return sensor_data_service
