from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from webpush.models import PushInformation
import json

@login_required
@require_POST
@csrf_exempt  # Service workers often can't send CSRF tokens
def push_subscribe(request):
    """Save push notification subscription for the user using django-webpush"""
    try:
        # Assumes request.body is the subscription object:
        # {"endpoint": "...", "keys": {"p256dh": "...", "auth": "..."}}
        data = json.loads(request.body)
        
        # Get the keys from the subscription object
        endpoint = data.get('endpoint')
        keys = data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not endpoint:
            return JsonResponse({
                'status': 'error',
                'message': 'Subscription must have an endpoint.'
            }, status=400)

        # Use update_or_create on the unique endpoint
        # This correctly links a user to a specific subscription
        subscription, created = PushInformation.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': request.user,
                'p256dh': p256dh,
                'auth': auth
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
@csrf_exempt  # Service workers often can't send CSRF tokens
def push_unsubscribe(request):
    """Remove a specific push notification subscription"""
    try:
        # Assumes request.body is the subscription object
        data = json.loads(request.body)
        endpoint = data.get('endpoint')

        if not endpoint:
            return JsonResponse({
                'status': 'error',
                'message': 'Endpoint not provided to unsubscribe.'
            }, status=400)

        # Delete the specific subscription by its unique endpoint
        # We also filter by user for security, so one user can't delete
        # another user's subscription, even if they know the endpoint.
        PushInformation.objects.filter(
            endpoint=endpoint, 
            user=request.user
        ).delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Push subscription removed successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)