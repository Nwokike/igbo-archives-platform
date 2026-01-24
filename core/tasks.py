"""
Huey background tasks for the Igbo Archives platform.
Memory-efficient async tasks for 1GB RAM constraint.
"""

from huey.contrib.djhuey import task, periodic_task, db_task
from huey import crontab
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@db_task()
def send_email_async(subject, message, recipient_list, from_email=None):
    """Send email asynchronously to reduce request latency"""
    try:
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f"Email sent to {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


@db_task()
def send_push_notification_async(user_id, title, body, url=None):
    """Send push notification asynchronously"""
    try:
        from django.contrib.auth import get_user_model
        from webpush.models import PushInformation
        from webpush import send_user_notification
        
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        payload = {
            "head": title,
            "body": body,
        }
        if url:
            payload["url"] = url
        
        send_user_notification(user=user, payload=payload, ttl=86400)
        logger.info(f"Push notification sent to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        return False


@db_task()
def notify_post_approved(post_id, post_type):
    """Notify author when their post is approved"""
    try:
        if post_type == 'insight':
            from insights.models import InsightPost
            post = InsightPost.objects.select_related('author').get(id=post_id)
            author = post.author
            title = post.title
        elif post_type == 'book':
            from books.models import BookReview
            post = BookReview.objects.select_related('reviewer').get(id=post_id)
            author = post.reviewer
            title = post.review_title
        else:
            return False
        
        from users.models import Notification
        Notification.objects.create(
            recipient=author,
            verb=f'Your {post_type} "{title}" has been approved and published!',
            description=f'Your submission is now live on Igbo Archives.',
        )
        
        if author.email:
            send_email_async(
                subject=f'Your {post_type} has been approved!',
                message=f'Congratulations! Your {post_type} "{title}" has been approved and is now live on Igbo Archives.',
                recipient_list=[author.email],
            )
        
        return True
    except Exception as e:
        logger.error(f"Failed to notify post approval: {e}")
        return False


@db_task()
def notify_post_rejected(post_id, post_type, reason=''):
    """Notify author when their post is rejected"""
    try:
        if post_type == 'insight':
            from insights.models import InsightPost
            post = InsightPost.objects.select_related('author').get(id=post_id)
            author = post.author
            title = post.title
        elif post_type == 'book':
            from books.models import BookReview
            post = BookReview.objects.select_related('reviewer').get(id=post_id)
            author = post.reviewer
            title = post.review_title
        else:
            return False
        
        from users.models import Notification
        description = f'Reason: {reason}' if reason else 'Please review and resubmit.'
        Notification.objects.create(
            recipient=author,
            verb=f'Your {post_type} "{title}" needs revision',
            description=description,
        )
        
        return True
    except Exception as e:
        logger.error(f"Failed to notify post rejection: {e}")
        return False


@periodic_task(crontab(hour='3', minute='0'))
def daily_database_backup():
    """Run database and media backup daily at 3 AM"""
    try:
        from django.core.management import call_command
        # Calling our wrapper command which handles both DB and Media + cleanup
        call_command('backup_database', clean=True)
        logger.info("Daily database and media backup completed")
        return True
    except Exception as e:
        logger.error(f"Daily backup failed: {e}")
        return False


@periodic_task(crontab(hour='2', minute='30'))
def cleanup_old_chat_sessions():
    """Remove chat sessions older than 30 days to keep DB light."""
    try:
        from ai.models import ChatSession
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(days=30)
        deleted_count, _ = ChatSession.objects.filter(
            updated_at__lt=cutoff,
            is_active=True
        ).update(is_active=False)
        
        # Also hard delete very old inactive sessions (90+ days)
        very_old = timezone.now() - timedelta(days=90)
        hard_deleted, _ = ChatSession.objects.filter(
            updated_at__lt=very_old,
            is_active=False
        ).delete()
        
        logger.info(f"Chat cleanup: {deleted_count} deactivated, {hard_deleted} deleted")
        return True
    except Exception as e:
        logger.error(f"Chat cleanup failed: {e}")
        return False


@periodic_task(crontab(hour='5', minute='0'))
def cleanup_tts_files():
    """Clean up old TTS audio files."""
    try:
        from ai.services.tts_service import tts_service
        tts_service.cleanup_old_files(max_age_hours=24)
        logger.info("TTS file cleanup completed")
        return True
    except Exception as e:
        logger.error(f"TTS cleanup failed: {e}")
        return False


@periodic_task(crontab(day='1', hour='4', minute='0'))
def cleanup_old_notifications():
    """Archive or delete read notifications older than 18 months to keep DB lean."""
    try:
        from users.models import Notification
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(days=540)  # 18 months
        
        # Delete read notifications older than cutoff
        deleted_count, _ = Notification.objects.filter(
            unread=False,
            timestamp__lt=cutoff
        ).delete()
        
        logger.info(f"Notification cleanup: {deleted_count} old read notifications deleted")
        return True
    except Exception as e:
        logger.error(f"Notification cleanup failed: {e}")
        return False


@periodic_task(crontab(day='1', hour='4', minute='30'))
def cleanup_old_messages():
    """Archive very old message threads to keep messaging DB lean.
    
    Note: This is a conservative cleanup - only threads with no activity
    for 2+ years and all messages read. Users should be able to access
    recent conversations.
    """
    try:
        from users.models import Thread, Message
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(days=730)  # 2 years
        
        # Find threads with no activity for 2+ years where all messages are read
        old_threads = Thread.objects.filter(
            updated_at__lt=cutoff
        ).prefetch_related('messages')
        
        deleted_count = 0
        for thread in old_threads:
            # Check if all messages are read
            unread_count = thread.messages.filter(is_read=False).count()
            if unread_count == 0:
                # All messages read, safe to delete
                thread.delete()
                deleted_count += 1
        
        logger.info(f"Message cleanup: {deleted_count} old threads deleted")
        return True
    except Exception as e:
        logger.error(f"Message cleanup failed: {e}")
        return False


@periodic_task(crontab(hour='*/6'))
def clear_expired_cache():
    """Clear expired cache entries every 6 hours.
    
    Note: Django's DatabaseCache automatically handles expiration.
    This task is kept as a placeholder for any future manual cleanup.
    We no longer call cache.clear() as that destroys ALL cache entries.
    """
    try:
        # DatabaseCache auto-expires entries, no action needed
        logger.info("Cache expiration check completed (auto-managed by DatabaseCache)")
        return True
    except Exception as e:
        logger.error(f"Cache check failed: {e}")
        return False


@db_task()
def notify_indexnow(urls):
    """Notify search engines about new/updated content via IndexNow"""
    try:
        from core.indexnow import IndexNowClient
        client = IndexNowClient()
        
        if isinstance(urls, str):
            urls = [urls]
        
        for url in urls:
            client.submit_url(url)
        
        logger.info(f"Submitted {len(urls)} URLs to IndexNow")
        return True
    except Exception as e:
        logger.error(f"IndexNow submission failed: {e}")
        return False
