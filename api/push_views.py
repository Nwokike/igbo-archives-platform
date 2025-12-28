"""
Push notification subscription API views.
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


@login_required
@require_POST
def push_subscribe(request):
    """Save push notification subscription using django-webpush."""
    try:
        from webpush.models import SubscriptionInfo, PushInformation
        
        data = json.loads(request.body)
        
        endpoint = data.get('endpoint')
        keys = data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not endpoint:
            return JsonResponse({
                'status': 'error',
                'message': 'Subscription must have an endpoint.'
            }, status=400)

        subscription_info, _ = SubscriptionInfo.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'p256dh': p256dh or '',
                'auth': auth or '',
            }
        )
        
        PushInformation.objects.update_or_create(
            user=request.user,
            subscription=subscription_info,
        )
        
        logger.info(f"Push subscription saved for user {request.user.id}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Push subscription saved successfully'
        })
    except Exception as e:
        logger.error(f"Push subscribe error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def push_unsubscribe(request):
    """Remove a push notification subscription."""
    try:
        from webpush.models import SubscriptionInfo, PushInformation
        
        data = json.loads(request.body)
        endpoint = data.get('endpoint')

        if not endpoint:
            return JsonResponse({
                'status': 'error',
                'message': 'Endpoint not provided to unsubscribe.'
            }, status=400)

        subscription = SubscriptionInfo.objects.filter(endpoint=endpoint).first()
        if subscription:
            PushInformation.objects.filter(
                user=request.user,
                subscription=subscription
            ).delete()
            
            if not PushInformation.objects.filter(subscription=subscription).exists():
                subscription.delete()
        
        logger.info(f"Push subscription removed for user {request.user.id}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Push subscription removed successfully'
        })
    except Exception as e:
        logger.error(f"Push unsubscribe error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
