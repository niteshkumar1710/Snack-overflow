from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

import app.models  # Ensure all models are registered with Base.metadata
from app.database.base import Base
from app.main import app as fastapi_app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Provides a TestClient instance for API tests."""
    with TestClient(fastapi_app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provides an isolated in-memory database session with strict foreign key and check constraint enforcement.

    Used for verifying model definitions, relational cascades, and database constraints.
    """
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable SQLite foreign key constraint enforcement
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables defined in SQLAlchemy Base.metadata
    Base.metadata.create_all(bind=test_engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)
