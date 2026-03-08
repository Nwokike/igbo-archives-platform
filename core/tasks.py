"""
Huey background tasks for the Igbo Archives platform.
Memory-efficient async tasks for 1GB RAM constraint.

Task Schedule:
- 03:00 AM: Daily database and media backup
- 04:00 AM: Cleanup old notifications (1st of month)
- 04:30 AM: Cleanup old messages (1st of month)
- 05:00 AM: Cleanup deactivated accounts older than 30 days (1st of month)
- 06:00 AM Sunday: Send weekly digest emails (max 270/batch, Brevo 300/day limit)
"""

from django_huey import db_task, periodic_task
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
def broadcast_push_notification_task(title, body, url=None):
    """Broadcast push notification to all subscribed users in batches of 50."""
    try:
        import time
        from webpush.models import PushInformation
        # Get unique user IDs with active push subscriptions
        user_ids = list(PushInformation.objects.values_list('user', flat=True).distinct())
        
        count = 0
        batch_size = 50
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            for user_id in batch:
                if user_id:
                    send_push_notification_async(user_id, title, body, url)
                    count += 1
            # Small delay between batches to avoid overwhelming task queue
            if i + batch_size < len(user_ids):
                time.sleep(1)
        
        logger.info(f"Broadcast push triggered for {count} users: {title}")
        return True
    except Exception as e:
        logger.error(f"Failed to broadcast push notification: {e}")
        return False




@periodic_task(crontab(minute='0', hour='3'))
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




@periodic_task(crontab(minute='0', hour='4', day='1'))
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


@periodic_task(crontab(minute='30', hour='4', day='1'))
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
        from django.db.models import Count, Q
        
        cutoff = timezone.now() - timedelta(days=730)  # 2 years
        
        # Use annotation to avoid N+1 query - find threads with all messages read
        old_threads = Thread.objects.filter(
            updated_at__lt=cutoff
        ).annotate(
            unread_count=Count('messages', filter=Q(messages__is_read=False))
        ).filter(unread_count=0)
        
        deleted_count, _ = old_threads.delete()
        
        logger.info(f"Message cleanup: {deleted_count} old threads deleted")
        return True
    except Exception as e:
        logger.error(f"Message cleanup failed: {e}")
        return False


@periodic_task(crontab(minute='0', hour='5', day='1'))
def cleanup_deactivated_accounts():
    """Permanently delete soft-deleted accounts after 30-day grace period.
    
    Users who delete their account have is_active=False and deactivated_at set.
    After 30 days, permanently remove the user and cascade-delete their content.
    """
    try:
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from datetime import timedelta
        
        User = get_user_model()
        cutoff = timezone.now() - timedelta(days=30)
        
        deactivated = User.objects.filter(
            is_active=False,
            deactivated_at__isnull=False,
            deactivated_at__lt=cutoff
        )
        
        count = deactivated.count()
        if count:
            deactivated.delete()
            logger.info(f"Account cleanup: {count} deactivated accounts permanently deleted")
        else:
            logger.info("Account cleanup: No expired deactivated accounts found")
        return True
    except Exception as e:
        logger.error(f"Deactivated account cleanup failed: {e}")
        return False


@db_task()
def notify_indexnow(urls):
    """Notify search engines about new/updated content via IndexNow"""
    try:
        from core.indexnow import submit_url_to_indexnow
        
        if isinstance(urls, str):
            urls = [urls]
        
        for url in urls:
            submit_url_to_indexnow(url)
        
        logger.info(f"Submitted {len(urls)} URLs to IndexNow")
        return True
    except Exception as e:
        logger.error(f"IndexNow submission failed: {e}")
        return False


@periodic_task(crontab(minute='0', hour='6', day_of_week='0'))
def send_weekly_digest():
    """
    Process weekly digest batch. Runs daily at 6 AM but only sends
    to users whose last digest was 7+ days ago.
    - Limits to 270 users per batch to stay within Brevo daily quota.
    - Uses last_weekly_update_at to track which users need an update.
    """
    try:
        from django.contrib.auth import get_user_model
        from django.template.loader import render_to_string
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Q
        from core.models import DigestQueue, EmailLog
        from core.email_service import send_email
        
        User = get_user_model()
        now = timezone.now()
        
        # 1. Get pending digest content
        pending_items = list(DigestQueue.get_pending_content())
        if not pending_items:
            logger.info("No content for weekly digest")
            return True
        
        # 2. Check remaining quota
        remaining_quota = EmailLog.quota_remaining()
        if remaining_quota < 50:
            logger.warning("Email quota too low for digest batch today. Skipping.")
            return False
            
        # 3. Determine batch size (target 270 as requested)
        batch_limit = min(270, remaining_quota - 20)
        
        # 4. Get users who haven't received an update in the last 7 days
        # This picks up users who haven't been notified yet for this "week" cycle
        last_week = now - timedelta(days=7)
        users_to_notify = User.objects.filter(
            is_active=True
        ).filter(
            Q(last_weekly_update_at__lt=last_week) | Q(last_weekly_update_at__isnull=True)
        ).exclude(email='').order_by('id')[:batch_limit]
        
        users_list = list(users_to_notify)
        
        if not users_list:
            # Check if ALL users are now up to date
            remaining_users = User.objects.filter(
                is_active=True
            ).filter(
                Q(last_weekly_update_at__lt=last_week) | Q(last_weekly_update_at__isnull=True)
            ).exclude(email='').exists()
            
            if not remaining_users:
                # Everyone is notified. Mark these items as processed so they don't appear in future weeks.
                DigestQueue.mark_processed([i.id for i in pending_items])
                logger.info("All users have received updates. Digest items marked as processed.")
            return True

        # 5. Prepare content group by type
        archives = [i for i in pending_items if i.content_type == 'archive']
        lore = [i for i in pending_items if i.content_type == 'lore']
        books = [i for i in pending_items if i.content_type == 'book']
        
        # 6. Prepare template context
        week_end = now.date()
        week_start = week_end - timedelta(days=7)
        site_url = getattr(settings, 'SITE_URL', 'https://igboarchives.com.ng')
        
        context = {
            'week_start': week_start.strftime('%b %d'),
            'week_end': week_end.strftime('%b %d, %Y'),
            'site_url': site_url,
            'year': week_end.year,
            'new_archives': [{'title': i.title, 'author_name': i.author_name, 'url': i.url, 'archive_type': 'Archive'} for i in archives[:10]],
            'new_lore': [{'title': i.title, 'author_name': i.author_name, 'url': i.url} for i in lore[:10]],
            'new_books': [{'title': i.title, 'author_name': i.author_name, 'url': i.url} for i in books[:10]],
            'new_archives_count': len(archives),
            'new_lore_count': len(lore),
            'new_books_count': len(books),
        }
        
        # 7. Send batch
        sent_count = 0
        for user in users_list:
            user_context = context.copy()
            user_context['user_name'] = user.get_display_name()
            
            html_message = render_to_string('email/weekly_digest.html', user_context)
            text_message = render_to_string('email/weekly_digest.txt', user_context)
            
            if send_email(
                to_email=user.email,
                subject='Igbo Archives: Your Weekly Update',
                message=text_message,
                email_type='digest',
                html_message=html_message
            ):
                sent_count += 1
        
        # Bulk update all successfully-sent users in one query
        if sent_count > 0:
            from django.contrib.auth import get_user_model as _gum
            sent_ids = [u.id for u in users_list[:sent_count]]
            _gum().objects.filter(id__in=sent_ids).update(last_weekly_update_at=now)
        
        logger.info(f"Weekly digest batch: {sent_count} users notified")
        return True
        
    except Exception as e:
        logger.error(f"Weekly digest batch failed: {e}", exc_info=True)
        return False



