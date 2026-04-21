"""
Test utilities and helpers for the test suite.
"""

from typing import Generator
from sqlalchemy.orm import Session


def create_test_user(db: Session, email: str = "test@example.com", password: str = "TestPassword123") -> dict:
    """
    Create a test user in the database.
    
    Args:
        db: Database session
        email: User email (default: test@example.com)
        password: User password (default: TestPassword123)
    
    Returns:
        Dictionary with user details
    """
    from src.models import User
    from src.auth.hashing import hash_password
    
    user = User(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "email": user.email,
        "password": password,  # Unencrypted for reference
    }


def get_auth_headers(client, email: str = "testuser@example.com", password: str = "TestPassword123") -> dict:
    """
    Get authorization headers with a valid token.
    
    Args:
        client: FastAPI TestClient instance
        email: User email for login
        password: User password for login
    
    Returns:
        Dictionary with Authorization header containing bearer token
    """
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    if response.status_code != 200:
        raise ValueError(f"Login failed: {response.json()}")
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
