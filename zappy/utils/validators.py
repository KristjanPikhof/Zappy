"""Input validation utilities."""

import re
from typing import Optional


def validate_domain(domain: str) -> tuple[bool, Optional[str]]:
    """Validate a domain name.

    Args:
        domain: Domain name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not domain:
        return False, "Domain cannot be empty"

    # Basic domain pattern
    pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"

    if not re.match(pattern, domain):
        return False, "Invalid domain format"

    if len(domain) > 253:
        return False, "Domain name too long"

    return True, None


def validate_port(port: str) -> tuple[bool, Optional[str]]:
    """Validate a port number.

    Args:
        port: Port number as string

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        port_num = int(port)
        if 1 <= port_num <= 65535:
            return True, None
        return False, "Port must be between 1 and 65535"
    except ValueError:
        return False, "Port must be a number"


def validate_ip(ip: str) -> tuple[bool, Optional[str]]:
    """Validate an IP address (IPv4 or IPv6).

    Args:
        ip: IP address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # IPv4 pattern
    ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

    # Simplified IPv6 pattern (covers most common cases)
    ipv6_pattern = r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$"

    if re.match(ipv4_pattern, ip):
        return True, None

    if re.match(ipv6_pattern, ip):
        return True, None

    # Try localhost
    if ip in ("localhost", "127.0.0.1", "::1"):
        return True, None

    return False, "Invalid IP address format"


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """Validate a URL.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL cannot be empty"

    # Basic URL pattern
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"

    if re.match(pattern, url, re.IGNORECASE):
        return True, None

    return False, "Invalid URL format"


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """Validate an email address.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email cannot be empty"

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if re.match(pattern, email):
        return True, None

    return False, "Invalid email format"


def normalize_proxy_url(url: str) -> str:
    """Normalize a proxy URL by adding http:// and localhost if missing.

    Args:
        url: URL, host:port, or just port number

    Returns:
        Normalized URL with protocol

    Examples:
        "5001" -> "http://127.0.0.1:5001"
        "localhost:5001" -> "http://localhost:5001"
        "192.168.1.1:3000" -> "http://192.168.1.1:3000"
        "http://example.com" -> "http://example.com"
    """
    url = url.strip()

    # If already has protocol, return as is
    if re.match(r"^https?://", url, re.IGNORECASE):
        return url

    # If it's just a port number, assume localhost
    if re.match(r"^\d+$", url):
        return f"http://127.0.0.1:{url}"

    # Otherwise add http://
    return f"http://{url}"
