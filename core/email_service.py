"""
Email service with rate limiting for Brevo 300/day quota.

Email Types:
1. INSTANT: Approval/rejection, direct user actions (always send immediately)
2. ADMIN: Activity notifications to admins (always send immediately)
3. DIGEST: New post notifications (queued for weekly digest)

Usage:
    from core.email_service import send_email, queue_for_digest, get_quota_status
    
    # Instant email (approval, rejection)
    send_email(to_email, subject, message, email_type='instant')
    
    # Queue for weekly digest
    queue_for_digest('archive', archive.id, archive.title, author_name, url)
"""
import logging
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

# Brevo daily limit - reserve 10 for critical instant emails
DAILY_EMAIL_LIMIT = 300
DIGEST_BATCH_LIMIT = 290  # Leave 10 for instant/admin emails


def get_quota_status():
    """Get current email quota status."""
    from core.models import EmailLog
    
    today = timezone.now().date()
    sent_today = EmailLog.get_daily_count(today)
    remaining = max(0, DAILY_EMAIL_LIMIT - sent_today)
    
    return {
        'date': today.isoformat(),
        'sent': sent_today,
        'remaining': remaining,
        'limit': DAILY_EMAIL_LIMIT,
    }


def log_email(recipient_email, subject, email_type='instant', success=True):
    """Log email for quota tracking."""
    from core.models import EmailLog
    
    EmailLog.objects.create(
        recipient_email=recipient_email,
        subject=subject[:255],
        email_type=email_type,
        success=success,
    )


def send_email(to_email, subject, message, email_type='instant', html_message=None, force=False):
    """
    Send email with rate limiting.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        message: Plain text message
        email_type: 'instant', 'admin', or 'digest'
        html_message: Optional HTML version
        force: If True, send even if over quota (for critical emails)
    
    Returns:
        bool: True if sent, False if not sent
    """
    from core.models import EmailLog
    
    # Check if email backend is configured
    if not settings.EMAIL_BACKEND or 'console' in settings.EMAIL_BACKEND.lower():
        logger.info(f"Email (to: {to_email}) logged only: EMAIL_BACKEND not configured.")
        log_email(to_email, subject, email_type, success=True)
        return True
    
    # Check quota (unless forced or admin email)
    if not force and email_type not in ('admin', 'instant'):
        if not EmailLog.can_send():
            logger.warning(f"Email quota exceeded. Skipping email to {to_email}")
            return False
    
    try:
        send_mail(
            subject=f'Igbo Archives - {subject}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        log_email(to_email, subject, email_type, success=True)
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        log_email(to_email, subject, email_type, success=False)
        return False


def send_admin_notification(subject, message, html_message=None):
    """
    Send notification to all admin users.
    Uses 'admin' email type which bypasses quota checks.
    """
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    admin_emails = list(User.objects.filter(
        is_staff=True, 
        is_active=True
    ).exclude(email='').values_list('email', flat=True))
    
    if not admin_emails:
        logger.warning("No admin emails found for notification")
        return False
    
    for email in admin_emails:
        send_email(email, subject, message, email_type='admin', html_message=html_message, force=True)
    
    return True


def queue_for_digest(content_type, content_id, title, author_name, url):
    """
    Queue content for weekly digest instead of instant email.
    
    Args:
        content_type: 'archive', 'insight', or 'book'
        content_id: ID of the content
        title: Title of the content
        author_name: Name of the author/uploader
        url: URL to the content
    """
    from core.models import DigestQueue
    
    DigestQueue.objects.create(
        content_type=content_type,
        content_id=content_id,
        title=title,
        author_name=author_name,
        url=url,
    )
    logger.info(f"Queued {content_type} '{title}' for weekly digest")


def notify_admin_new_submission(post, post_type):
    """
    Send instant notification to admins about new content submission.
    This is always sent immediately as admins need to know about pending content.
    """
    title = getattr(post, 'title', getattr(post, 'book_title', str(post)))
    author = getattr(post, 'author', getattr(post, 'added_by', getattr(post, 'uploaded_by', None)))
    author_name = author.get_display_name() if author else 'Unknown'
    
    subject = f'New {post_type} submitted for approval'
    message = f'''
A new {post_type} has been submitted and is waiting for your approval.

Title: {title}
Author: {author_name}
Submitted: {timezone.now().strftime("%Y-%m-%d %H:%M")}

Please review in the admin panel.
'''
    
    send_admin_notification(subject, message)


def notify_admin_new_published(post, post_type):
    """
    Notify admins when content is published (for tracking purposes).
    """
    title = getattr(post, 'title', getattr(post, 'book_title', str(post)))
    author = getattr(post, 'author', getattr(post, 'added_by', getattr(post, 'uploaded_by', None)))
    author_name = author.get_display_name() if author else 'Unknown'
    url = getattr(post, 'get_absolute_url', lambda: '/')()
    
    subject = f'New {post_type} published'
    message = f'''
A new {post_type} has been published on Igbo Archives.

Title: {title}
Author: {author_name}
URL: {settings.SITE_URL}{url}
'''
    
    # Also queue for user digest
    queue_for_digest(post_type, post.id, title, author_name, url)
    
    send_admin_notification(subject, message)
