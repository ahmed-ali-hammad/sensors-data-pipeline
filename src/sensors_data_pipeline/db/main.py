import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.sql import text

_logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Singleton class to manage database engine initialization and async session creation
    for both the main and TimescaleDB databases.
    """

    _instance = None

    _async_database_engine: AsyncEngine | None = None
    _async_timescale_database_engine: AsyncEngine | None = None

    _async_database_session_factory: async_sessionmaker | None = None
    _async_timescale_database_session_factory: async_sessionmaker | None = None

    def __new__(cls, database_uri: str, timescale_db_uri: str):
        if not hasattr(cls, "instance"):
            cls.instance = super(DatabaseManager, cls).__new__(cls)

            # Create Databases Engines
            cls._async_database_engine = create_async_engine(
                url=database_uri, echo=False
            )
            cls._async_timescale_database_engine = create_async_engine(
                url=timescale_db_uri, echo=False
            )

            # Create Sessions Factories
            cls._async_database_session_factory = async_sessionmaker(
                bind=cls._async_database_engine, expire_on_commit=False
            )
            cls._async_timescale_database_session_factory = async_sessionmaker(
                bind=cls._async_timescale_database_engine, expire_on_commit=False
            )
        return cls.instance

    @staticmethod
    @asynccontextmanager
    async def get_db_session() -> AsyncIterator[AsyncSession]:
        """
        Context manager to yield a database session.
        """
        if (
            DatabaseManager._async_database_engine is None
            or DatabaseManager._async_database_session_factory is None
        ):
            raise RuntimeError("Database engine or session factory is not initialized.")

        async with DatabaseManager._async_database_session_factory() as session:
            try:
                yield session
            except Exception:
                _logger.exception("Transaction failed. Rolling back..")
                await session.rollback()
                raise

    @staticmethod
    @asynccontextmanager
    async def get_timescale_db_session() -> AsyncIterator[AsyncSession]:
        """
        Context manager to yield a Timescale database session.
        """
        if (
            DatabaseManager._async_timescale_database_engine is None
            or DatabaseManager._async_timescale_database_session_factory is None
        ):
            raise RuntimeError(
                "Timescale Database engine or session factory is not initialized."
            )

        async with DatabaseManager._async_timescale_database_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                _logger.exception("Transaction failed. Rolling back..")
                await session.rollback()
                raise

    @staticmethod
    async def _check_db_connection(
        session_provider: Callable, database_name: str
    ) -> bool:
        """
        Internal helper to check DB connectivity.

        Args:
            session_provider (Callable): A method that returns an async session context manager.
            database_name (str): Name of the DB.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            async with session_provider() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            _logger.exception(f"{database_name} connection failed.")
            return False

    @staticmethod
    async def check_main_db_connection() -> bool:
        """
        Performs a connectivity check for the main database.

        Returns:
            bool: True if the database is reachable, False otherwise.
        """

        return await DatabaseManager._check_db_connection(
            DatabaseManager.get_db_session, "Database"
        )

    @staticmethod
    async def check_timescale_db_connection() -> bool:
        """
        Performs a connectivity check for the Timescale database.

        Returns:
            bool: True if the Timescale DB is reachable, False otherwise.
        """

        return await DatabaseManager._check_db_connection(
            DatabaseManager.get_timescale_db_session, "Timescale Database"
        )

    @classmethod
    async def dispose_engine(cls) -> None:
        """
        Disposes of both DB and TimescaleDB engines.
        """
        if cls._async_database_engine:
            _logger.info("Disposing DB engine.")
            await cls._async_database_engine.dispose()
            cls._async_database_engine = None

        if cls._async_timescale_database_engine:
            _logger.info("Disposing TimescaleDB engine.")
            await cls._async_timescale_database_engine.dispose()
            cls._async_timescale_database_engine = None

        cls._instance = None
