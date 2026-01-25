from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from allauth.account.forms import default_token_generator
from allauth.account.utils import user_pk_to_url_str
import logging

logger = logging.getLogger(__name__)

def send_claim_profile_email(user, name=None):
    """
    Sends the 'Claim Profile' email to a user, allowing them to set a password.
    Used for guest comments and admin onboarding of migrated users.
    """
    if not user.email:
        return False

    try:
        # Generate password reset URL (Claim Profile)
        token = default_token_generator.make_token(user)
        uid = user_pk_to_url_str(user)
        
        try:
            # Try standard Allauth URL name first
            reset_url = reverse('account_reset_password_from_key', kwargs={'uidb36': uid, 'key': token})
        except:
            # Fallback to Django standard
            uid_django = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = reverse('password_reset_confirm', kwargs={'uidb64': uid_django, 'token': token})

        claim_url = f"{settings.SITE_URL}{reset_url}"
        
        subject = "Don't miss out: Complete your profile on Igbo Archives"
        
        display_name = name or user.full_name or 'Guest'
        
        # Context for the email template
        context = {
            'name': display_name,
            'claim_url': claim_url,
        }
        
        html_message = render_to_string('account/email/claim_profile_email.html', context)
        plain_message = f"Hello {display_name},\n\nYou've started the conversation on Igbo Archives. Don't miss out on what's next.\n\nComplete your profile now to save articles, track replies, and unlock exclusive community features: {claim_url}"
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Sent invitation/claim email to user {user.email}")
        return True

    except Exception as e:
        logger.error(f"Error in send_claim_profile_email for {user.email}: {str(e)}")
        return False
