"""
Test suite for password hashing and authentication dependencies.
"""

import pytest


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Passwords are hashed correctly."""
        from src.auth.hashing import hash_password
        
        password = "TestPassword123"
        hashed = hash_password(password)
        
        # Hash should be a string but not the plain password
        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > len(password)
    
    def test_hash_same_password_produces_different_hashes(self):
        """Same password hashed twice produces different hashes (salt)."""
        from src.auth.hashing import hash_password
        
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Due to salt, hashes should be different
        assert hash1 != hash2
    
    def test_verify_correct_password(self):
        """Correct password verifies successfully."""
        from src.auth.hashing import hash_password, verify_password
        
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_wrong_password(self):
        """Wrong password fails verification."""
        from src.auth.hashing import hash_password, verify_password
        
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_case_sensitive(self):
        """Password verification is case-sensitive."""
        from src.auth.hashing import hash_password, verify_password
        
        password = "TestPassword123"
        wrong_case = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(wrong_case, hashed) is False
    
    def test_empty_password_handling(self):
        """Empty passwords are handled."""
        from src.auth.hashing import hash_password, verify_password
        
        password = ""
        hashed = hash_password(password)
        
        # Empty password should still hash/verify
        assert verify_password("", hashed) is True
        assert verify_password("anything", hashed) is False


class TestAuthenticationDependency:
    """Test get_current_user dependency."""
    
    def test_get_current_user_with_valid_token(self, client, test_user, auth_headers):
        """Valid token resolves to correct user."""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
    
    def test_get_current_user_without_token(self, client):
        """Missing token fails authentication."""
        response = client.get("/users/me")
        assert response.status_code == 403
    
    def test_get_current_user_with_refresh_token(self, client, test_user):
        """Refresh token is rejected for access."""
        response = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123"
            },
        )
        refresh_token = response.json()["refresh_token"]
        
        # Try to use refresh token for access
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert response.status_code == 401
        assert "Wrong token type" in response.json()["detail"]
    
    def test_get_current_user_inactive_user(self, client, test_db, test_user):
        """Inactive users cannot access protected routes."""
        # Deactivate user
        test_user.is_active = False
        test_db.commit()
        
        # Try to login (should still work for data integrity)
        response = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123"
            },
        )
        
        # If login succeeds, the inactive check happens in the route
        if response.status_code == 200:
            token = response.json()["access_token"]
            response = client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 401
            assert "inactive" in response.json()["detail"]
