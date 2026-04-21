"""
Test suite for JWT token generation, encoding, and validation.
"""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError


class TestTokenGeneration:
    """Test access and refresh token creation."""
    
    def test_create_access_token(self):
        """Access token is created with correct payload."""
        from src.auth.jwt import create_access_token
        from src.config import settings
        
        user_id = 1
        token = create_access_token(user_id)
        
        assert isinstance(token, str)
        
        # Decode and verify payload
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_refresh_token(self):
        """Refresh token is created with correct payload."""
        from src.auth.jwt import create_refresh_token
        from src.config import settings
        
        user_id = 1
        token = create_refresh_token(user_id)
        
        assert isinstance(token, str)
        
        # Decode and verify payload
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert "exp" in payload
    
    def test_access_token_expiry(self):
        """Access token expires at correct time."""
        from src.auth.jwt import create_access_token
        from src.config import settings
        
        token = create_access_token(1)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Should expire in approximately 15 minutes (default)
        delta = (exp_time - now).total_seconds()
        assert 14 * 60 <= delta <= 16 * 60  # Allow 1 minute tolerance
    
    def test_refresh_token_expiry(self):
        """Refresh token expires at correct time."""
        from src.auth.jwt import create_refresh_token
        from src.config import settings
        
        token = create_refresh_token(1)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Should expire in approximately 7 days (default)
        delta = (exp_time - now).total_seconds()
        assert 6.9 * 86400 <= delta <= 7.1 * 86400  # Allow some tolerance


class TestTokenDecoding:
    """Test token validation and payload extraction."""
    
    def test_decode_valid_access_token(self):
        """Valid access token is decoded successfully."""
        from src.auth.jwt import create_access_token, decode_token
        
        user_id = 1
        token = create_access_token(user_id)
        
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
    
    def test_decode_invalid_token(self):
        """Invalid token returns None."""
        from src.auth.jwt import decode_token
        
        payload = decode_token("invalid-token-string")
        assert payload is None
    
    def test_decode_expired_token(self):
        """Expired token returns None."""
        from src.auth.jwt import decode_token
        from src.config import settings
        from datetime import datetime, timedelta, timezone
        
        # Create an expired token
        expired_payload = {
            "sub": "1",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        payload = decode_token(expired_token)
        assert payload is None
    
    def test_decode_token_with_wrong_secret(self):
        """Token signed with different secret is rejected."""
        from src.auth.jwt import decode_token
        from src.config import settings
        
        # Create token with wrong secret
        payload = {
            "sub": "1",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
        }
        wrong_token = jwt.encode(
            payload,
            "wrong-secret-key",
            algorithm=settings.ALGORITHM
        )
        
        result = decode_token(wrong_token)
        assert result is None


class TestTokenTypeValidation:
    """Test that token type validation works correctly."""
    
    def test_access_token_has_correct_type(self):
        """Access token includes type=access."""
        from src.auth.jwt import create_access_token
        from src.config import settings
        
        token = create_access_token(1)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["type"] == "access"
    
    def test_refresh_token_has_correct_type(self):
        """Refresh token includes type=refresh."""
        from src.auth.jwt import create_refresh_token
        from src.config import settings
        
        token = create_refresh_token(1)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["type"] == "refresh"
