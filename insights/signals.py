from django.db.models.signals import post_save
from django.dispatch import receiver
# from notifications.signals import notify # <--- REMOVED OLD IMPORT
from .models import InsightPost, EditSuggestion
import logging

# --- NEW IMPORT ---
# Import the function we already built in the previous step
from core.notifications_utils import send_edit_suggestion_notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=InsightPost)
def handle_insight_post_approval(sender, instance, created, **kwargs):
    """
    Signal handler for InsightPost save.
    Logs when a post is approved and published.
    """
    # This function did not use notifications, so it remains unchanged.
    if not created and instance.is_approved and instance.is_published:
        if not instance.posted_to_social:
            logger.info(f"Post approved: {instance.title}")


@receiver(post_save, sender=EditSuggestion)
def notify_author_of_suggestion(sender, instance, created, **kwargs):
    """
    Notify the post author when someone suggests an edit.
    """
    # We only need to check if it's new.
    # The utility function handles the logic of not notifying the author
    # if they are suggesting an edit on their own post.
    if created:
        try:
            # --- REPLACED ---
            # Call the single utility function we built.
            # It handles in-app, webpush, and email notifications.
            send_edit_suggestion_notification(instance)
            logger.info(f"Notification sent to {instance.post.author.full_name} for edit suggestion")
            
        except Exception as e:
            logger.error(f"Error sending edit suggestion notification: {str(e)}")