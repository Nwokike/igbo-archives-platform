from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from webpush.models import PushInformation
import json


@login_required
@require_POST
def push_subscribe(request):
    """Save push notification subscription for the user using django-webpush"""
    try:
        data = json.loads(request.body)
        
        # Create or update WebPush subscription using django-webpush
        subscription, created = PushInformation.objects.update_or_create(
            user=request.user,
            defaults={
                'subscription': data
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Push subscription saved successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def push_unsubscribe(request):
    """Remove push notification subscription using django-webpush"""
    try:
        PushInformation.objects.filter(user=request.user).delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Push subscription removed successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
