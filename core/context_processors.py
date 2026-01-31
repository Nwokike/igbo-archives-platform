"""
Context processors for template variables.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def pwa_settings(request):
    """Expose PWA, push notification, and Turnstile settings to templates."""
    
    webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
    turnstile_site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
    
    # Warn if Turnstile is not configured in production
    if not turnstile_site_key and not settings.DEBUG:
        logger.warning("TURNSTILE_SITE_KEY is not set. Turnstile widget will not appear.")
    
    return {
        'VAPID_PUBLIC_KEY': webpush_settings.get('VAPID_PUBLIC_KEY', ''),
        'turnstile_site_key': turnstile_site_key,
    }


def monetization_settings(request):
    """Expose monetization settings to templates."""
    return {
        'ENABLE_ADSENSE': getattr(settings, 'ENABLE_ADSENSE', False),
        'GOOGLE_ADSENSE_CLIENT_ID': getattr(settings, 'GOOGLE_ADSENSE_CLIENT_ID', ''),
        'ENABLE_DONATIONS': getattr(settings, 'ENABLE_DONATIONS', False),
        'PAYSTACK_PUBLIC_KEY': getattr(settings, 'PAYSTACK_PUBLIC_KEY', ''),
        'ENABLE_ANALYTICS': getattr(settings, 'ENABLE_ANALYTICS', False),
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', ''),
    }


def notification_count(request):
    """Cache unread notification count to avoid N+1 queries on every page load."""
    if request.user.is_authenticated:
        from django.core.cache import cache
        cache_key = f'notif_count_{request.user.id}'
        count = cache.get(cache_key)
        if count is None:
            count = request.user.notifications.filter(unread=True).count()
            cache.set(cache_key, count, 60)  # Cache for 60 seconds
        return {'unread_notification_count': count}
    return {'unread_notification_count': 0}
