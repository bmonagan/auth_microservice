# cache.py
import logging
from typing import Optional
import redis
from src.config import settings

logger = logging.getLogger(__name__)

# Global Redis client (lazy-loaded)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    return _redis_client


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
        key = f"blacklist:{token}"
        client.setex(key, ttl_seconds, "true")
        logger.info("Token blacklisted successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to blacklist token: {e}")
        return False


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
        key = f"blacklist:{token}"
        result = client.exists(key)
        return bool(result)
    except Exception as e:
        logger.error(f"Failed to check token blacklist: {e}")
        # Fail open — if Redis is down, allow the token
        # In production, consider fail-closed (deny) for security
        return False
