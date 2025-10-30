from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
# Import your new, fixed utility function
from core.notifications_utils import send_message_notification
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