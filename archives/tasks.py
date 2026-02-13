"""
Background tasks for the archives app.
Uses Huey for async processing of email notifications.
"""
import logging
from huey.contrib.djhuey import task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@task()
def send_archive_notification_email(subject, message_body, staff_emails):
    """Send archive notification emails asynchronously via Huey."""
    try:
        send_mail(
            subject=subject,
            message=message_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=staff_emails,
            fail_silently=False,
        )
        logger.info(f"Sent archive notification email: {subject}")
    except Exception as e:
        logger.error(f"Failed to send archive notification email: {e}")
