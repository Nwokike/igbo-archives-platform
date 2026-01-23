"""
Cloudflare Turnstile integration for Django.
Simple server-side validation for comment forms.
"""
import requests
from django.conf import settings


def verify_turnstile(token: str, remote_ip: str = None) -> dict:
    """
    Verify a Turnstile token with Cloudflare's API.
    
    Args:
        token: The cf-turnstile-response from the form
        remote_ip: Optional client IP address
    
    Returns:
        dict with 'success' boolean and any error codes
    """
    if not token:
        return {'success': False, 'error-codes': ['missing-input-response']}
    
    secret_key = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    if not secret_key:
        # If no secret key configured, skip validation (dev mode)
        import logging
        logger = logging.getLogger(__name__)
        if not settings.DEBUG:
            logger.warning("TURNSTILE_SECRET_KEY is not set. Turnstile validation is disabled.")
        return {'success': True}
    
    data = {
        'secret': secret_key,
        'response': token,
    }
    if remote_ip:
        data['remoteip'] = remote_ip
    
    try:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data=data,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {'success': False, 'error-codes': ['internal-error', str(e)]}
