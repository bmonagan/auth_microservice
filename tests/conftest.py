"""
Pytest configuration and shared fixtures for the test suite.

Fixtures provide isolated test database, test client, and test user setup/teardown.
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Set test database URL before importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-change-in-production"

from src.database import Base, get_db
from src.main import app
from src.limiter import limiter
from src.cache import clear_memory_blacklist
from src.models import User
from src.auth.hashing import hash_password


@pytest.fixture(scope="session", autouse=True)
def disable_rate_limiter_for_tests():
    """Disable rate limiter globally for all tests to avoid blocking requests."""
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture(scope="function", autouse=True)
def clear_blacklist():
    """Clear the token blacklist before each test."""
    clear_memory_blacklist()
    yield
    clear_memory_blacklist()


@pytest.fixture(scope="function")
def test_db():
    """
    Create an in-memory SQLite database for each test.
    
    Automatically creates all tables and cleans up after the test.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal()
    
    # Cleanup
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """
    Return a TestClient instance bound to the FastAPI app with test database.
    """
    return TestClient(app)


@pytest.fixture
def test_user(test_db):
    """
    Create and return a test user in the database.
    
    Email: testuser@example.com
    Password: TestPassword123
    """
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("TestPassword123"),
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """
    Return Authorization headers with a valid access token for the test user.
    """
    response = client.post(
        "/auth/login",
        json={"email": "testuser@example.com", "password": "TestPassword123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
