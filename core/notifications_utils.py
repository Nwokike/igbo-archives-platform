from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from users.models import Notification  # <-- IMPORT YOUR NEW MODEL
from webpush import send_user_notification  # <-- IMPORT WEBPUSH
import logging

logger = logging.getLogger(__name__)

def _get_post_author(post):
    """Helper to get author from different post types."""
    if hasattr(post, 'author'):
        return post.author
    if hasattr(post, 'reviewer'):
        return post.reviewer
    if hasattr(post, 'uploaded_by'):
        return post.uploaded_by
    return None

def _get_post_title(post):
    """Helper to get title from different post types."""
    if hasattr(post, 'title'):
        return post.title
    if hasattr(post, 'review_title'):
        return post.review_title
    return "your post"

def _get_absolute_url(obj):
    """Helper to safely get a URL, or fallback."""
    if hasattr(obj, 'get_absolute_url'):
        return obj.get_absolute_url()
    return "/"

def _send_notification_and_push(recipient, sender, verb, description, target_object=None, push_head="", push_body="", push_url="/"):
    """
    A private helper to:
    1. Create the in-app Notification object (for your template).
    2. Send the webpush notification (for browser pop-ups).
    """
    if not recipient or recipient == sender:
        return  # Don't notify users of their own actions or if no recipient

    try:
        # 1. Create the In-App Notification
        content_type = None
        object_id = None
        if target_object:
            content_type = ContentType.objects.get_for_model(target_object)
            object_id = target_object.id
            
        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            verb=verb,
            description=description,
            content_type=content_type,
            object_id=object_id
        )
        
        # 2. Send the Browser Push Notification
        payload = {
            "head": push_head,
            "body": push_body,
            "icon": "/static/images/logos/logo-light.png",
            "url": push_url
        }
        send_user_notification(user=recipient, payload=payload, ttl=1000)
        
        logger.info(f"Sent notification ('{verb}') to {recipient.username}")
        
    except Exception as e:
        # Most common error is user has no push subscription, which is fine.
        logger.warning(f"Error sending notification or push to {recipient.username}: {str(e)}")


# --- YOUR REWRITTEN FUNCTIONS ---

def send_post_approved_notification(post, post_type='insight'):
    author = _get_post_author(post)
    post_title = _get_post_title(post)
    description = f'Your {post_type} "{post_title}" has been approved and is now published!'
    
    _send_notification_and_push(
        recipient=author,
        sender=None,  # Approved by system/admin
        verb='approved your post',
        description=description,
        target_object=post,
        push_head="Post Approved!",
        push_body=description,
        push_url=_get_absolute_url(post)
    )
    send_email_notification(author.email, f'Your {post_type.title()} has been approved!', description)


def send_post_rejected_notification(post, reason, post_type='insight'):
    author = _get_post_author(post)
    post_title = _get_post_title(post)
    description = f'Your {post_type} "{post_title}" was not approved. Reason: {reason}'

    _send_notification_and_push(
        recipient=author,
        sender=None,
        verb='rejected your post',
        description=description,
        target_object=post,
        push_head="Post Revision Needed",
        push_body=f'Your {post_type} "{post_title}" was not approved.',
        push_url="/dashboard/"  # Link to their dashboard
    )
    email_message = f'{description}\n\nYou can revise and resubmit it from your dashboard.'
    send_email_notification(author.email, f'Your {post_type.title()} needs revision', email_message)


def send_new_comment_notification(comment, post):
    post_author = _get_post_author(post)
    if not post_author or (comment.user and comment.user == post_author):
        return # Don't notify if commenting on own post
        
    commenter_name = comment.user.full_name if comment.user else comment.name
    description = f'{commenter_name} commented on your post'

    _send_notification_and_push(
        recipient=post_author,
        sender=comment.user,
        verb='commented on your post',
        description=description,
        target_object=post,
        push_head="New Comment",
        push_body=f'{commenter_name} commented on "{_get_post_title(post)}".',
        push_url=f"{_get_absolute_url(post)}#comment-{comment.id}" # Link to comment
    )


def send_comment_reply_notification(comment, parent_comment):
    if not parent_comment.user:
        return  # Can't notify guest users
    if comment.user and comment.user == parent_comment.user:
        return # Don't notify if replying to own comment
    
    commenter_name = comment.user.full_name if comment.user else comment.name
    description = f'{commenter_name} replied to your comment'

    _send_notification_and_push(
        recipient=parent_comment.user,
        sender=comment.user,
        verb='replied to your comment',
        description=description,
        target_object=comment,
        push_head="New Reply",
        push_body=f'{commenter_name} replied to your comment.',
        push_url=f"{_get_absolute_url(parent_comment)}#comment-{comment.id}"
    )


def send_message_notification(message, recipient):
    """Send notification when someone sends you a message"""
    description = f'{message.sender.full_name} sent you a message'
    
    _send_notification_and_push(
        recipient=recipient,
        sender=message.sender,
        verb='sent you a message',
        description=description,
        target_object=message.thread,
        push_head="New Message",
        push_body=f'{message.sender.full_name} sent you a message.',
        push_url=f"/messages/{message.thread.id}/"
    )
    
    subject = f'New message from {message.sender.full_name}'
    site_url = getattr(settings, "SITE_URL", "")
    email_message = f'{description}\n\nSubject: {message.thread.subject}\n\nLog in to read and reply: {site_url}/profile/messages/{message.thread.id}/'
    send_email_notification(recipient.email, subject, email_message)


def send_edit_suggestion_notification(suggestion):
    post_author = suggestion.post.author
    suggester = suggestion.suggested_by
    
    if suggester == post_author:
        return

    description = f'{suggester.full_name} suggested an edit to "{suggestion.post.title}"'

    _send_notification_and_push(
        recipient=post_author,
        sender=suggester,
        verb='suggested an edit to your post',
        description=description,
        target_object=suggestion,
        push_head="New Edit Suggestion",
        push_body=f'{suggester.full_name} suggested an edit to your post.',
        push_url="/dashboard/" # Or link to moderation
    )
    
    email_message = f'{description}\n\nSuggestion: {suggestion.suggestion_text}\n\nReview from your dashboard.'
    send_email_notification(post_author.email, 'Edit suggestion on your post', email_message)


def send_edit_suggestion_approved_notification(suggestion):
    description = f'Your edit suggestion for "{suggestion.post.title}" was approved. You can now edit the post.'
    _send_notification_and_push(
        recipient=suggestion.suggested_by,
        sender=suggestion.post.author,
        verb='approved your edit suggestion',
        description=description,
        target_object=suggestion.post,
        push_head="Suggestion Approved",
        push_body=description,
        push_url=_get_absolute_url(suggestion.post)
    )


def send_edit_suggestion_rejected_notification(suggestion, reason=''):
    description = f'Your edit suggestion for "{suggestion.post.title}" was declined. {reason}'
    _send_notification_and_push(
        recipient=suggestion.suggested_by,
        sender=suggestion.post.author,
        verb='declined your edit suggestion',
        description=description,
        target_object=suggestion.post,
        push_head="Suggestion Declined",
        push_body=f'Your edit suggestion for "{suggestion.post.title}" was declined.',
        push_url=_get_absolute_url(suggestion.post)
    )


def send_email_notification(to_email, subject, message):
    """Helper function to send email notifications (Unchanged)"""
    if not settings.EMAIL_BACKEND or 'console' in settings.EMAIL_BACKEND:
        logger.info(f"Email (to: {to_email}) not sent: EMAIL_BACKEND not configured.")
        return
    
    try:
        send_mail(
            subject=f'Igbo Archives - {subject}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")