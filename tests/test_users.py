"""
Test suite for protected user endpoints.
"""

import pytest


class TestGetCurrentUser:
    """GET /users/me endpoint tests."""
    
    def test_get_me_authenticated(self, client, auth_headers, test_user):
        """Authenticated user can retrieve their profile."""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["is_active"] is True
    
    def test_get_me_without_token(self, client):
        """Unauthenticated access to /users/me fails."""
        response = client.get("/users/me")
        assert response.status_code == 403  # FastAPI OAuth2 returns 403
    
    def test_get_me_with_invalid_token(self, client):
        """Invalid token is rejected."""
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid-token-here"}
        )
        assert response.status_code == 401
    
    def test_get_me_with_malformed_header(self, client):
        """Malformed authorization header is rejected."""
        response = client.get(
            "/users/me",
            headers={"Authorization": "InvalidFormat token-here"}
        )
        assert response.status_code == 403


class TestUpdateProfile:
    """PATCH /users/me endpoint tests."""
    
    def test_update_email_success(self, client, auth_headers, test_user, test_db):
        """User can update their email."""
        response = client.patch(
            "/users/me",
            headers=auth_headers,
            json={"email": "newemail@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"
        
        # Verify in database
        test_db.refresh(test_user)
        assert test_user.email == "newemail@example.com"
    
    def test_update_email_duplicate_fails(self, client, auth_headers, test_db, test_user):
        """Cannot update to an email already in use."""
        # Create another user
        from src.models import User
        from src.auth.hashing import hash_password
        
        other_user = User(
            email="other@example.com",
            hashed_password=hash_password("OtherPassword123"),
            is_active=True,
        )
        test_db.add(other_user)
        test_db.commit()
        
        # Try to update to existing email
        response = client.patch(
            "/users/me",
            headers=auth_headers,
            json={"email": "other@example.com"},
        )
        assert response.status_code == 400
        assert "already in use" in response.json()["detail"]
    
    def test_update_email_without_auth(self, client):
        """Unauthenticated update fails."""
        response = client.patch(
            "/users/me",
            json={"email": "newemail@example.com"},
        )
        assert response.status_code == 403


class TestChangePassword:
    """POST /users/me/change-password endpoint tests."""
    
    def test_change_password_success(self, client, auth_headers, test_user):
        """User can change their password."""
        response = client.post(
            "/users/me/change-password",
            headers=auth_headers,
            json={
                "old_password": "TestPassword123",
                "new_password": "NewPassword456",
            },
        )
        assert response.status_code == 204
    
    def test_change_password_wrong_old_password(self, client, auth_headers):
        """Cannot change password with wrong old password."""
        response = client.post(
            "/users/me/change-password",
            headers=auth_headers,
            json={
                "old_password": "WrongPassword123",
                "new_password": "NewPassword456",
            },
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"]
    
    def test_change_password_same_as_old(self, client, auth_headers):
        """Cannot set new password to same as old password."""
        response = client.post(
            "/users/me/change-password",
            headers=auth_headers,
            json={
                "old_password": "TestPassword123",
                "new_password": "TestPassword123",
            },
        )
        assert response.status_code == 400
        assert "must differ" in response.json()["detail"]
    
    def test_change_password_without_auth(self, client):
        """Unauthenticated password change fails."""
        response = client.post(
            "/users/me/change-password",
            json={
                "old_password": "TestPassword123",
                "new_password": "NewPassword456",
            },
        )
        assert response.status_code == 403


class TestDeleteAccount:
    """DELETE /users/me endpoint tests."""
    
    def test_delete_account_success(self, client, auth_headers, test_user, test_db):
        """User can delete their account with correct password."""
        response = client.delete(
            "/users/me",
            headers=auth_headers,
            json={"password": "TestPassword123"},
        )
        assert response.status_code == 204
        
        # Verify user is deleted
        from src.models import User
        deleted_user = test_db.query(User).filter(User.id == test_user.id).first()
        assert deleted_user is None
    
    def test_delete_account_wrong_password(self, client, auth_headers):
        """Cannot delete account with wrong password."""
        response = client.delete(
            "/users/me",
            headers=auth_headers,
            json={"password": "WrongPassword123"},
        )
        assert response.status_code == 400
        assert "Incorrect password" in response.json()["detail"]
    
    def test_delete_account_without_auth(self, client):
        """Unauthenticated delete fails."""
        response = client.delete(
            "/users/me",
            json={"password": "TestPassword123"},
        )
        assert response.status_code == 403


class TestGetSessions:
    """GET /users/me/sessions endpoint tests."""
    
    def test_get_sessions_authenticated(self, client, auth_headers, test_user):
        """User can retrieve their active sessions."""
        response = client.get("/users/me/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
    
    def test_get_sessions_without_auth(self, client):
        """Unauthenticated access fails."""
        response = client.get("/users/me/sessions")
        assert response.status_code == 403


class TestRevokeSession:
    """DELETE /users/me/sessions/{session_id} endpoint tests."""
    
    def test_revoke_own_session(self, client, auth_headers, test_db, test_user):
        """User can revoke their own session."""
        # Get sessions
        response = client.get("/users/me/sessions", headers=auth_headers)
        assert response.status_code == 200
        sessions = response.json()["sessions"]
        
        if sessions:
            session_id = sessions[0]["id"]
            response = client.delete(
                f"/users/me/sessions/{session_id}",
                headers=auth_headers,
            )
            assert response.status_code == 204
            
            # Verify revoked in DB
            from src.models import RefreshToken
            token = test_db.query(RefreshToken).filter(
                RefreshToken.id == session_id
            ).first()
            assert token.revoked is True
    
    def test_revoke_nonexistent_session(self, client, auth_headers):
        """Revoking non-existent session fails."""
        response = client.delete(
            "/users/me/sessions/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestRevokeAllSessions:
    """DELETE /users/me/sessions endpoint tests."""
    
    def test_revoke_all_sessions(self, client, auth_headers, test_db, test_user):
        """User can revoke all sessions at once."""
        response = client.delete(
            "/users/me/sessions",
            headers=auth_headers,
        )
        assert response.status_code == 204
        
        # Verify all sessions revoked
        from src.models import RefreshToken
        active_tokens = test_db.query(RefreshToken).filter(
            RefreshToken.user_id == test_user.id,
            RefreshToken.revoked == False,
        ).all()
        assert len(active_tokens) == 0
