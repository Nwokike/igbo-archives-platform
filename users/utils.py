from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from allauth.account.forms import default_token_generator
from allauth.account.utils import user_pk_to_url_str
import logging

logger = logging.getLogger(__name__)


def _build_claim_email_context(user, name=None, mode='commenter'):
    """
    Build subject, plain message, and HTML for a claim/onboarding email.
    Returns (subject, plain_message, html_message) tuple.
    """
    # Generate password reset URL
    token = default_token_generator.make_token(user)
    uid = user_pk_to_url_str(user)
    
    try:
        reset_url = reverse('account_reset_password_from_key', kwargs={'uidb36': uid, 'key': token})
    except Exception:
        uid_django = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = reverse('password_reset_confirm', kwargs={'uidb64': uid_django, 'token': token})

    claim_url = f"{settings.SITE_URL}{reset_url}"
    display_name = name or user.full_name or 'there'
    
    # Mode-specific configuration
    if mode == 'onboarding':
        template = 'account/email/onboarding_email.html'
        subject = "Welcome back to the upgraded Igbo Archives"
        plain_message = f"Hello {display_name},\n\nWe've upgraded the Igbo Archives platform! You can now review books, save archives, and more.\n\nComplete your profile to get started: {claim_url}"
    else:
        template = 'account/email/claim_profile_email.html'
        subject = "Regarding your activity on Igbo Archives"
        plain_message = f"Hello {display_name},\n\nYou've started the conversation on Igbo Archives. Don't miss out on replies and new features.\n\nComplete your profile here: {claim_url}"
    
    context = {
        'name': display_name,
        'claim_url': claim_url,
    }
    
    html_message = render_to_string(template, context)
    return subject, plain_message, html_message


def send_claim_profile_email(user, name=None, mode='commenter'):
    """
    Sends a profile claim/onboarding email to a user via email_service.
    Modes:
    - 'commenter': For guest commenters (personal follow-up).
    - 'onboarding': For migrated WordPress users (welcome back/upgrade).
    """
    if not user.email:
        return False

    try:
        subject, plain_message, html_message = _build_claim_email_context(user, name, mode)
        
        from core.email_service import send_email
        send_email(
            to_email=user.email,
            subject=subject,
            message=plain_message,
            email_type=f'claim_profile_{mode}',
            html_message=html_message,
        )
        logger.info(f"Sent {mode} email to {user.email}")
        return True

    except Exception as e:
        logger.error(f"Error in send_claim_profile_email ({mode}) for {user.email}: {str(e)}")
        return False
