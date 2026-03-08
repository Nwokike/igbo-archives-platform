"""
API Dashboard views — manage API tokens and view MCP connection info.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework.authtoken.models import Token

logger = logging.getLogger(__name__)


@login_required
def api_dashboard(request):
    """API & MCP dashboard — view/manage API tokens and connection info."""
    token = Token.objects.filter(user=request.user).first()
    
    # Build MCP connection URL
    from django.conf import settings
    site_url = getattr(settings, 'SITE_URL', 'https://igboarchives.com.ng')
    mcp_endpoint = f"{site_url}/api/mcp/"
    api_base = f"{site_url}/api/v1/"
    
    return render(request, 'users/api_dashboard.html', {
        'token': token,
        'mcp_endpoint': mcp_endpoint,
        'api_base': api_base,
    })


@login_required
@require_POST
def generate_api_token(request):
    """Generate or regenerate API token for the current user."""
    # Delete existing token if any
    Token.objects.filter(user=request.user).delete()
    # Create new token
    token = Token.objects.create(user=request.user)
    logger.info(f"API token generated for user {request.user.username}")
    
    if request.headers.get('HX-Request'):
        return render(request, 'users/partials/api_token_display.html', {
            'token': token,
            'just_created': True,
        })
    return redirect('users:api_dashboard')


@login_required
@require_POST
def revoke_api_token(request):
    """Revoke the current user's API token."""
    deleted_count, _ = Token.objects.filter(user=request.user).delete()
    if deleted_count:
        logger.info(f"API token revoked for user {request.user.username}")
    
    if request.headers.get('HX-Request'):
        return render(request, 'users/partials/api_token_display.html', {
            'token': None,
            'just_revoked': True,
        })
    return redirect('users:api_dashboard')
