# device.py
"""
Device detection and tracking utilities.

Parses User-Agent and IP address to provide human-readable device information.
"""
import re
from typing import Optional
from fastapi import Request


def get_device_info(request: Request, user_provided_name: Optional[str] = None) -> str:
    """
    Extract device information from request headers and IP.
    
    Priority:
    1. User-provided device name (explicit)
    2. Parsed User-Agent (automatic)
    3. IP address fallback
    
    Args:
        request: FastAPI Request object
        user_provided_name: Optional device name provided by client
    
    Returns:
        Human-readable device description (e.g., "Chrome on Windows", "Safari on iPhone")
    """
    if user_provided_name and user_provided_name.strip():
        return user_provided_name.strip()
    
    # Try to parse User-Agent
    user_agent = request.headers.get("user-agent", "").lower()
    if user_agent:
        device_str = _parse_user_agent(user_agent)
        if device_str:
            # Add IP for additional context
            ip = get_client_ip(request)
            return f"{device_str} ({ip})" if ip else device_str
    
    # Fallback to IP address
    ip = get_client_ip(request)
    return f"Unknown Device ({ip})" if ip else "Unknown Device"


def get_client_ip(request: Request) -> Optional[str]:
    """
    Extract client IP address from request, respecting X-Forwarded-For header.
    
    Args:
        request: FastAPI Request object
    
    Returns:
        Client IP address or None
    """
    # Check X-Forwarded-For header (proxy/load balancer)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # X-Forwarded-For can be comma-separated; take the first IP
        return forwarded_for.split(",")[0].strip()
    
    # Fall back to direct client IP
    return request.client.host if request.client else None


def _parse_user_agent(user_agent: str) -> Optional[str]:
    """
    Parse User-Agent header and return device description.
    
    Args:
        user_agent: User-Agent header (lowercase)
    
    Returns:
        Device description (e.g., "Chrome on Windows") or None if unparseable
    """
    # Detect browser
    browser = _detect_browser(user_agent)
    
    # Detect OS
    os = _detect_os(user_agent)
    
    if browser and os:
        return f"{browser} on {os}"
    elif browser:
        return browser
    elif os:
        return os
    
    return None


def _detect_browser(user_agent: str) -> Optional[str]:
    """Detect browser from User-Agent string."""
    # Order matters - more specific browsers first
    patterns = [
        (r"chrome/(\d+)", "Chrome"),
        (r"firefox/(\d+)", "Firefox"),
        (r"safari/(\d+)", "Safari"),
        (r"edge/(\d+)", "Edge"),
        (r"opera/(\d+)", "Opera"),
        (r"trident/.*rv:(\d+)", "Internet Explorer"),
    ]
    
    for pattern, name in patterns:
        match = re.search(pattern, user_agent)
        if match:
            version = match.group(1)
            return f"{name} {version}"
    
    return None


def _detect_os(user_agent: str) -> Optional[str]:
    """Detect operating system from User-Agent string."""
    patterns = [
        (r"windows nt 10\.0", "Windows 10"),
        (r"windows nt 6\.3", "Windows 8.1"),
        (r"windows nt 6\.2", "Windows 8"),
        (r"windows nt 6\.1", "Windows 7"),
        (r"windows nt", "Windows"),
        (r"iphone", "iPhone"),
        (r"ipad", "iPad"),
        (r"ipod", "iPod"),
        (r"mac os x", "macOS"),
        (r"linux", "Linux"),
        (r"android", "Android"),
    ]
    
    for pattern, name in patterns:
        if re.search(pattern, user_agent):
            return name
    
    return None
