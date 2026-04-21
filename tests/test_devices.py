"""
Test suite for device detection and multi-device session management.
"""
import time
from datetime import datetime, timedelta, timezone
from src.models import RefreshToken


class TestDeviceDetection:
    """Device detection on login tests."""

    def test_login_response_includes_device_info(self, client, test_user):
        """Login response includes device_id and device_name."""
        response = client.post(
            "/auth/login",
            json={"email": "testuser@example.com", "password": "TestPassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for device fields in response
        assert "device_id" in data
        assert "device_name" in data
        assert isinstance(data["device_id"], int)
        assert isinstance(data["device_name"], str)
        assert len(data["device_name"]) > 0

    def test_login_with_custom_device_name(self, client, test_user):
        """Custom device_name in login request is used."""
        response = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "My Personal Laptop"
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["device_name"] == "My Personal Laptop"

    def test_login_device_name_stored_in_database(self, client, test_user, test_db):
        """Device name from login is stored in RefreshToken.device_info."""
        device_name = "Home Computer"
        response = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": device_name
            },
        )
        assert response.status_code == 200
        device_id = response.json()["device_id"]

        # Verify in database
        token_record = test_db.query(RefreshToken).filter(
            RefreshToken.id == device_id
        ).first()
        assert token_record is not None
        assert token_record.device_info == device_name


class TestMultiDeviceSessions:
    """Multi-device session management tests."""

    def test_multiple_logins_create_separate_sessions(self, client, test_user, test_db):
        """Multiple logins from same user create separate session records."""
        # First login
        login1 = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "Device 1"
            },
        )
        assert login1.status_code == 200
        device_id_1 = login1.json()["device_id"]

        # Small delay to ensure unique token generation
        time.sleep(0.01)

        # Second login
        login2 = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "Device 2"
            },
        )
        assert login2.status_code == 200
        device_id_2 = login2.json()["device_id"]

        # Verify both sessions exist in database
        assert device_id_1 != device_id_2
        session1 = test_db.query(RefreshToken).filter(
            RefreshToken.id == device_id_1
        ).first()
        session2 = test_db.query(RefreshToken).filter(
            RefreshToken.id == device_id_2
        ).first()
        assert session1 is not None
        assert session2 is not None
        assert session1.device_info == "Device 1"
        assert session2.device_info == "Device 2"

    def test_user_can_view_all_sessions(self, client, test_user):
        """User can list all active sessions from all devices."""
        # Login from two different devices
        login1 = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "Phone"
            },
        )
        token1 = login1.json()["access_token"]

        time.sleep(0.01)

        login2 = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "Tablet"
            },
        )
        token2 = login2.json()["access_token"]

        # Get sessions using first device's token
        sessions_response = client.get(
            "/users/me/sessions",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()
        assert len(sessions) >= 2

        # Verify both devices are listed
        device_names = [session["device_name"] for session in sessions]
        assert "Phone" in device_names
        assert "Tablet" in device_names

    def test_user_can_revoke_single_device(self, client, test_user):
        """User can revoke session from one device without affecting others."""
        # Login from two devices
        login1 = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "Device A"
            },
        )
        token1 = login1.json()["access_token"]
        device_id_1 = login1.json()["device_id"]

        time.sleep(0.01)

        login2 = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "Device B"
            },
        )
        token2 = login2.json()["access_token"]

        # Revoke Device A session
        revoke_response = client.delete(
            f"/users/me/sessions/{device_id_1}",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert revoke_response.status_code == 204

        # Device A token should now be rejected
        me_response_a = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert me_response_a.status_code == 401

        # Device B token should still work
        me_response_b = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert me_response_b.status_code == 200

    def test_user_can_revoke_all_sessions(self, client, test_user):
        """User can logout from all devices at once."""
        # Login from two devices
        login1 = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "Phone"
            },
        )
        token1 = login1.json()["access_token"]

        time.sleep(0.01)

        login2 = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "Laptop"
            },
        )
        token2 = login2.json()["access_token"]

        # Revoke all sessions
        revoke_all_response = client.delete(
            "/users/me/sessions",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert revoke_all_response.status_code == 204

        # Both tokens should now be rejected
        me_response_1 = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert me_response_1.status_code == 401

        me_response_2 = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert me_response_2.status_code == 401

    def test_session_includes_created_timestamp(self, client, test_user):
        """Session response includes creation timestamp."""
        login_response = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "Test Device"
            },
        )
        token = login_response.json()["access_token"]

        sessions_response = client.get(
            "/users/me/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()
        
        # Find the session we just created
        test_session = next(s for s in sessions if s["device_name"] == "Test Device")
        assert "created_at" in test_session
        assert test_session["created_at"] is not None

    def test_session_includes_expiry_timestamp(self, client, test_user):
        """Session response includes expiration timestamp."""
        login_response = client.post(
            "/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "TestPassword123",
                "device_name": "Test Device"
            },
        )
        token = login_response.json()["access_token"]

        sessions_response = client.get(
            "/users/me/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()
        
        # Find the session we just created
        test_session = next(s for s in sessions if s["device_name"] == "Test Device")
        assert "expires_at" in test_session
        assert test_session["expires_at"] is not None
