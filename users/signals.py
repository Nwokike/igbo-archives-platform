from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
# Import your new, fixed utility function
from core.notifications_utils import send_message_notification
from django_comments.signals import comment_was_posted
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
import re
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Message)
def notify_message_recipient(sender, instance, created, **kwargs):
    """
    When a message is created, send notification to all
    other participants in the thread.
    """
    if created:
        # Get all participants in the thread EXCEPT the person who sent the message
        recipients = instance.thread.participants.exclude(id=instance.sender.id)
        
        for recipient in recipients:
            try:
                # Call your new util function
                # This now handles in-app, push, and email all at once
                send_message_notification(instance, recipient)
            except Exception as e:
                logger.error(f"Error in signal sending message notification: {str(e)}")

@receiver(comment_was_posted)
def send_guest_invitation_email(sender, comment, request, **kwargs):
    """
    Send an invitation email to guest commenters to encourage them to sign up.
    Creates a 'shadow' account if one doesn't exist, or prompts login if it does.
    """
    from users.models import CustomUser
    from django.core.mail import send_mail
    from django.urls import reverse
    from allauth.account.forms import default_token_generator
    from allauth.account.utils import user_pk_to_url_str

    # Check if it's a guest comment (no user object attached)
    if not comment.user and comment.user_email:
        try:
            email = comment.user_email
            if not email:
                return

            # Check if user already exists
            existing_user = CustomUser.objects.filter(email=email).first()

            if existing_user:
                # Security: DO NOT link the comment to the existing user automatically.
                # This prevents spoofing (someone posting as admin@example.com).
                # We can optionally send them a "Was this you?" email, but for now
                # we just treat it as a guest comment.
                
                # Check if this user has no usable password (incomplete profile)
                if not existing_user.has_usable_password():
                     # This is likely a previous shadow account that never claimed
                     pass # We could re-send the claim email here if we wanted
                
                logger.info(f"Guest comment from existing email {email} - Not linking to prevent spoofing.")
                return 

            # Create new shadow user
            # Generate a unique username
            base_username = re.sub(r'[^a-zA-Z0-9]', '', email.split('@')[0])[:30]
            username = base_username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = CustomUser.objects.create(
                email=email,
                username=username,
                full_name=comment.user_name or 'Guest'
            )
            user.set_unusable_password()
            user.save()
            
            # Link comment to the NEW user (safe, because we just created it)
            comment.user = user
            comment.save()

            # Send Claim Profile Email using utility
            from users.utils import send_claim_profile_email
            send_claim_profile_email(user, name=comment.user_name, mode='commenter')

        except Exception as e:
            logger.error(f"Error in send_guest_invitation_email: {str(e)}")
