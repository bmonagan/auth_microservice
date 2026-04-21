"""
Test suite for auth endpoints (register, login, refresh token).
"""

import pytest


class TestRegister:
    """Register endpoint tests."""
    
    def test_register_success(self, client):
        """User can register with valid email and strong password."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123"
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert data["message"] == "User created"
    
    def test_register_weak_password_too_short(self, client):
        """Register fails if password is under 8 characters."""
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "Short1"
            },
        )
        assert response.status_code == 422  # Validation error
        
    def test_register_weak_password_no_uppercase(self, client):
        """Register fails if password lacks uppercase letter."""
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "lowercase123"
            },
        )
        assert response.status_code == 422
    
    def test_register_weak_password_no_number(self, client):
        """Register fails if password lacks digit."""
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "NoNumbers"
            },
        )
        assert response.status_code == 422
    
    def test_register_invalid_email(self, client):
        """Register fails with invalid email format."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "ValidPassword1"
            },
        )
        assert response.status_code == 422
    
    def test_register_duplicate_email(self, client, test_user):
        """Register fails if email already exists."""
        response = client.post(
            "/auth/register",
            json={
                "email": "testuser@example.com",
                "password": "DifferentPassword123"
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]


class TestLogin:
    """Login endpoint tests."""
    
    def test_login_success(self, client, test_user):
        """User can login with correct credentials."""
        response = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123"
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        """Login fails with wrong password."""
        response = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "WrongPassword123"
            },
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Login fails for non-existent user."""
        response = client.post(
            "/auth/login",
            json={
                "email": "doesnotexist@example.com",
                "password": "SomePassword123"
            },
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_missing_email(self, client):
        """Login fails with missing email."""
        response = client.post(
            "/auth/login",
            json={"password": "TestPassword123"},
        )
        assert response.status_code == 422
    
    def test_login_missing_password(self, client):
        """Login fails with missing password."""
        response = client.post(
            "/auth/login",
            json={"email": "testuser@example.com"},
        )
        assert response.status_code == 422


class TestTokenStorage:
    """Verify refresh tokens are persisted after login."""
    
    def test_refresh_token_persisted(self, client, test_db, test_user):
        """Refresh token is stored in database after login."""
        response = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123"
            },
        )
        assert response.status_code == 200
        
        # Verify token exists in DB
        from src.models import RefreshToken
        tokens = test_db.query(RefreshToken).filter(
            RefreshToken.user_id == test_user.id
        ).all()
        assert len(tokens) == 1
        assert not tokens[0].revoked
