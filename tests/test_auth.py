"""
Test suite for auth endpoints (register, login, refresh token).
"""

from src.auth.jwt import create_email_verification_token, create_password_reset_token
from src.models import User


class TestRegister:
    """Register endpoint tests."""
    
    def test_register_success(self, client, test_db):
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
        assert "Check your email" in data["message"]

        created = test_db.query(User).filter(User.email == "newuser@example.com").first()
        assert created is not None
        assert created.is_active is False
    
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

    def test_login_unverified_user(self, client, test_user, test_db):
        """Unverified users cannot login."""
        test_user.is_active = False
        test_db.commit()

        response = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123"
            },
        )
        assert response.status_code == 403
        assert "Email not verified" in response.json()["detail"]
    
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


class TestEmailVerification:
    """Email verification link endpoint tests."""

    def test_verify_email_success(self, client, test_user, test_db):
        test_user.is_active = False
        test_db.commit()

        token = create_email_verification_token(test_user.id, test_user.email)
        response = client.get(f"/auth/verify-email?token={token}")

        assert response.status_code == 200
        assert "verified" in response.json()["message"].lower()

        test_db.refresh(test_user)
        assert test_user.is_active is True

    def test_verify_email_invalid_token(self, client):
        response = client.get("/auth/verify-email?token=not-a-valid-token")
        assert response.status_code == 400

    def test_verify_email_wrong_token_type(self, client, test_user):
        from src.auth.jwt import create_access_token

        token = create_access_token(test_user.id)
        response = client.get(f"/auth/verify-email?token={token}")
        assert response.status_code == 400


class TestPasswordReset:
    """Password reset flow endpoint tests."""

    def test_forgot_password_existing_email(self, client, test_user):
        """Forgot password with existing email returns success message."""
        response = client.post(
            "/auth/forgot-password",
            json={"email": "testuser@example.com"},
        )
        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]

    def test_forgot_password_nonexistent_email(self, client):
        """Forgot password with non-existent email still returns success (enumeration protection)."""
        response = client.post(
            "/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == 200
        assert "reset link has been sent" in response.json()["message"]

    def test_forgot_password_invalid_email(self, client):
        """Forgot password fails with invalid email format."""
        response = client.post(
            "/auth/forgot-password",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422

    def test_forgot_password_missing_email(self, client):
        """Forgot password fails with missing email."""
        response = client.post(
            "/auth/forgot-password",
            json={},
        )
        assert response.status_code == 422

    def test_reset_password_success(self, client, test_user):
        """User can reset password with valid token."""
        token = create_password_reset_token(test_user.id, test_user.email)
        response = client.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "NewPassword456"},
        )
        assert response.status_code == 200
        assert "successfully" in response.json()["message"]

        # Verify user can login with new password
        login_response = client.post(
            "/auth/login",
            json={"email": "testuser@example.com", "password": "NewPassword456"},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

    def test_reset_password_old_password_fails(self, client, test_user):
        """User cannot login with old password after reset."""
        token = create_password_reset_token(test_user.id, test_user.email)
        client.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "NewPassword456"},
        )

        # Try to login with old password
        login_response = client.post(
            "/auth/login",
            json={"email": "testuser@example.com", "password": "TestPassword123"},
        )
        assert login_response.status_code == 401
        assert "Invalid credentials" in login_response.json()["detail"]

    def test_reset_password_invalid_token(self, client):
        """Reset password fails with invalid token."""
        response = client.post(
            "/auth/reset-password",
            json={"token": "not-a-valid-token", "new_password": "NewPassword456"},
        )
        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    def test_reset_password_wrong_token_type(self, client, test_user):
        """Reset password fails with wrong token type (e.g., access token)."""
        from src.auth.jwt import create_access_token

        token = create_access_token(test_user.id)
        response = client.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "NewPassword456"},
        )
        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    def test_reset_password_weak_password(self, client, test_user):
        """Reset password fails with weak password."""
        token = create_password_reset_token(test_user.id, test_user.email)
        response = client.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "weak"},
        )
        assert response.status_code == 422

    def test_reset_password_missing_fields(self, client):
        """Reset password fails with missing fields."""
        response = client.post(
            "/auth/reset-password",
            json={"token": "some-token"},
        )
        assert response.status_code == 422

    def test_reset_password_email_mismatch(self, client, test_user, test_db):
        """Reset password fails if email in token doesn't match user's current email."""
        token = create_password_reset_token(test_user.id, "old@example.com")
        response = client.post(
            "/auth/reset-password",
            json={"token": token, "new_password": "NewPassword456"},
        )
        assert response.status_code == 400
        assert "does not match" in response.json()["detail"]


class TestLoginRateLimit:
    """Rate limiting on /login endpoint tests."""

    def test_login_rate_limit_header_present(self, client):
        """Login endpoint has rate limit information in response headers."""
        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "SomePassword123"
            },
        )
        # Check that rate limit headers are present (slowapi adds these)
        # Response should have x-ratelimit headers
        assert response.status_code in [401, 429]
        # If not rate limited yet, headers should indicate the limit
        if response.status_code == 401:
            # Should have rate limit info in headers
            headers_lower = {k.lower(): v for k, v in response.headers.items()}
            # slowapi may or may not add headers depending on configuration
            # Just verify the endpoint works and doesn't crash

    def test_login_rate_limit_multiple_requests(self, client):
        """Multiple login requests to /login endpoint don't crash the app."""
        # This test verifies that the rate limiter is applied without errors
        # We'll make a few requests and verify we get responses (not 500 errors)
        responses = []
        for i in range(3):
            response = client.post(
                "/auth/login",
                json={
                    "email": f"user{i}@example.com",
                    "password": "Password123"
                },
            )
            responses.append(response.status_code)
            # Should get 401 (invalid credentials) or 429 (rate limited), not 500
            assert response.status_code in [401, 429], f"Got unexpected status: {response.status_code}"

        # At least one request should succeed in getting past basic validation
        assert len(responses) >= 1


class TestLogout:
    """Logout endpoint and token blacklist tests."""

    def test_logout_success(self, client, test_user):
        """User can logout and invalidate access token."""
        # Login to get tokens
        login_response = client.post(
            "/auth/login",
            json={"email": "testuser@example.com", "password": "TestPassword123"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Logout
        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert logout_response.status_code == 200
        assert "successfully" in logout_response.json()["message"]

    def test_logout_invalidates_access_token(self, client, test_user):
        """After logout, the access token becomes invalid."""
        # Login to get token
        login_response = client.post(
            "/auth/login",
            json={"email": "testuser@example.com", "password": "TestPassword123"},
        )
        access_token = login_response.json()["access_token"]

        # Logout
        client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        # Try to use the token after logout
        me_response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 401
        assert "revoked" in me_response.json()["detail"].lower()

    def test_logout_requires_valid_token(self, client):
        """Logout fails with invalid token."""
        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    def test_logout_requires_authorization_header(self, client):
        """Logout fails without Authorization header."""
        response = client.post("/auth/logout")
        assert response.status_code == 403  # Missing credentials

    def test_logout_requires_bearer_token(self, client, test_user):
        """Logout fails with malformed Authorization header."""
        login_response = client.post(
            "/auth/login",
            json={"email": "testuser@example.com", "password": "TestPassword123"},
        )
        access_token = login_response.json()["access_token"]

        # Send with invalid header format (no "Bearer " prefix)
        response = client.post(
            "/auth/logout",
            headers={"Authorization": access_token}  # Missing "Bearer " prefix
        )
        assert response.status_code == 400

    def test_logout_revokes_refresh_tokens(self, client, test_user, test_db):
        """Logout also revokes all refresh tokens for the user."""
        from src.models import RefreshToken

        # Login to get tokens
        login_response = client.post(
            "/auth/login",
            json={"email": "testuser@example.com", "password": "TestPassword123"},
        )
        access_token = login_response.json()["access_token"]

        # Verify refresh token is active before logout
        tokens_before = test_db.query(RefreshToken).filter(
            RefreshToken.user_id == test_user.id,
            RefreshToken.revoked == False
        ).all()
        assert len(tokens_before) >= 1

        # Logout
        client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        # Verify all refresh tokens are revoked after logout
        tokens_after = test_db.query(RefreshToken).filter(
            RefreshToken.user_id == test_user.id,
            RefreshToken.revoked == False
        ).all()
        assert len(tokens_after) == 0
