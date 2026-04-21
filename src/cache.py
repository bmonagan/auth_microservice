# cache.py
import logging
from typing import Optional, Set
import redis
from src.config import settings

logger = logging.getLogger(__name__)

# Global Redis client (lazy-loaded)
_redis_client: Optional[redis.Redis] = None

# In-memory fallback for testing/development when Redis is unavailable
_memory_blacklist: Set[str] = set()


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client singleton. Returns None if Redis is unavailable."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory blacklist.")
            _redis_client = False  # Mark as tried but failed
    return _redis_client if _redis_client is not False else None


def blacklist_token(token: str, ttl_seconds: int) -> bool:
    """
    Add a token to the blacklist with TTL matching token expiry.
    
    Args:
        token: JWT token to blacklist
        ttl_seconds: Time to live in seconds (should match token expiry)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis_client()
        if client:
            key = f"blacklist:{token}"
            client.setex(key, ttl_seconds, "true")
        else:
            # Fallback to in-memory blacklist
            _memory_blacklist.add(token)
        logger.info("Token blacklisted successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to blacklist token: {e}")
        # Still add to memory blacklist as fallback
        _memory_blacklist.add(token)
        return True  # Return True since we have fallback


def is_token_blacklisted(token: str) -> bool:
    """
    Check if a token is blacklisted.
    
    Args:
        token: JWT token to check
    
    Returns:
        True if token is blacklisted, False otherwise
    """
    try:
        client = get_redis_client()
        if client:
            key = f"blacklist:{token}"
            result = client.exists(key)
            return bool(result)
        else:
            # Check memory blacklist
            return token in _memory_blacklist
    except Exception as e:
        logger.error(f"Failed to check token blacklist: {e}")
        # Also check memory as fallback
        return token in _memory_blacklist


def clear_memory_blacklist() -> None:
    """Clear the in-memory blacklist (useful for testing)."""
    global _memory_blacklist
    _memory_blacklist.clear()
