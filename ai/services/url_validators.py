"""
URL validation for AI services — blocks SSRF attacks.
Prevents AI image analysis endpoints from being used to scan internal networks.
"""
import ipaddress
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Allowed schemes for image URLs
ALLOWED_SCHEMES = {'http', 'https'}

# Common cloud metadata endpoints to block
BLOCKED_HOSTS = {
    '169.254.169.254',      # AWS/GCP/Azure metadata
    'metadata.google.internal',
    'metadata.internal',
}


def is_safe_url(url: str) -> bool:
    """
    Validate that a URL is safe to fetch (not an SSRF target).
    
    Blocks:
    - Non-HTTP(S) schemes (file://, ftp://, etc.)
    - Private/internal IP ranges (10.x, 172.16-31.x, 192.168.x, 127.x, ::1)
    - Cloud metadata endpoints (169.254.169.254)
    - Localhost
    
    Returns:
        True if the URL is safe to fetch, False otherwise.
    """
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ALLOWED_SCHEMES:
            logger.warning(f"Blocked URL with scheme: {parsed.scheme}")
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Block known metadata hosts
        if hostname.lower() in BLOCKED_HOSTS:
            logger.warning(f"Blocked metadata endpoint: {hostname}")
            return False
        
        # Block localhost
        if hostname.lower() in ('localhost', '0.0.0.0'):
            logger.warning(f"Blocked localhost URL: {hostname}")
            return False
        
        # Block private/reserved IP ranges
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
                logger.warning(f"Blocked private/reserved IP: {hostname}")
                return False
        except ValueError:
            # Not an IP address (it's a hostname) — that's fine
            pass
        
        return True
        
    except Exception as e:
        logger.warning(f"URL validation error: {e}")
        return False
