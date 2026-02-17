from django.urls import reverse
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from users.models import Notification
import logging

logger = logging.getLogger(__name__)

def _get_post_author(post):
    """Helper to get author from different post types."""
    # PRIORITY FIX: Check for specific user fields first.
    if hasattr(post, 'added_by'): # For BookRecommendation
        return post.added_by
    if hasattr(post, 'uploaded_by'): # For Archive
        return post.uploaded_by
    if hasattr(post, 'reviewer'): # For some review types
        return post.reviewer
    if hasattr(post, 'author'): # For InsightPost
        return post.author
    return None

def _get_post_title(post):
    """Helper to get title from different post types."""
    if hasattr(post, 'title'):
        return post.title
    if hasattr(post, 'review_title'):
        return post.review_title
    if hasattr(post, 'book_title'): # Fallback for BookRecommendation
        return post.book_title
    return "your post"

def _get_absolute_url(obj):
    """Helper to safely get a URL, or fallback."""
    if hasattr(obj, 'get_absolute_url'):
        return obj.get_absolute_url()
    return "/"

def _send_notification_and_push(recipient, sender, verb, description, target_object=None, push_head="", push_body="", push_url="/", allow_self=False):
    """
    A private helper to:
    1. Create the in-app Notification object.
    2. Send the webpush notification.
    """
    if not recipient:
        return
        
    if recipient == sender and not allow_self:
        return  # Don't notify users of their own actions unless explicitly allowed (system confirmations)

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
        
        # 2. Send the Browser Push Notification (async via tasks)
        try:
            from core.tasks import send_push_notification_async
            send_push_notification_async(recipient.id, push_head, push_body, push_url)
        except Exception as push_err:
            logger.warning(f"Failed to queue push notification for {recipient.username}: {push_err}")
        
        logger.info(f"Sent notification ('{verb}') to {recipient.username}")
        
    except Exception as e:
        logger.warning(f"Error sending notification: {str(e)}")


# --- NOTIFICATION FUNCTIONS ---

def send_post_approved_notification(post, post_type='insight'):
    author = _get_post_author(post)
    if not author:
        return

    post_title = _get_post_title(post)
    description = f'Your {post_type} "{post_title}" has been approved and is now published!'
    
    _send_notification_and_push(
        recipient=author,
        sender=None,
        verb='approved your post',
        description=description,
        target_object=post,
        push_head="Post Approved!",
        push_body=description,
        push_url=_get_absolute_url(post)
    )
    
    if hasattr(author, 'email') and author.email:
        send_email_notification(author.email, f'Your {post_type.title()} has been approved!', description)


def send_post_submitted_notification(post, post_type='insight'):
    """
    Notify the user that their submission was received.
    """
    author = _get_post_author(post)
    if not author:
        return

    post_title = _get_post_title(post)
    description = f'Your {post_type} "{post_title}" has been submitted successfully for moderation.'

    _send_notification_and_push(
        recipient=author,
        sender=None,
        verb='received your submission',
        description=description,
        target_object=post,
        push_head="Submission Received",
        push_body=description,
        push_url=reverse('users:dashboard')
    )


def send_post_rejected_notification(post, reason, post_type='insight'):
    author = _get_post_author(post)
    if not author:
        return

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
        push_url=reverse('users:dashboard')
    )
    
    if hasattr(author, 'email') and author.email:
        email_message = f'{description}\n\nYou can revise and resubmit it from your dashboard.'
        send_email_notification(author.email, f'Your {post_type.title()} needs revision', email_message)


def send_new_comment_notification(comment, post):
    post_author = _get_post_author(post)
    if not post_author or (comment.user and comment.user == post_author):
        return 
        
    commenter_name = comment.user.get_display_name() if comment.user else comment.name
    description = f'{commenter_name} commented on your post'

    _send_notification_and_push(
        recipient=post_author,
        sender=comment.user,
        verb='commented on your post',
        description=description,
        target_object=post,
        push_head="New Comment",
        push_body=f'{commenter_name} commented on "{_get_post_title(post)}".',
        push_url=f"{_get_absolute_url(post)}#comment-{comment.id}"
    )


def send_new_review_notification(review, book):
    """
    Specific notification for Book Reviews.
    """
    post_author = book.added_by
    if not post_author or review.user == post_author:
        return # Don't notify if reviewing own recommendation

    reviewer_name = review.user.get_display_name()
    book_title = book.book_title
    
    # Example: "Onyeka reviewed your recommendation 'Things Fall Apart'"
    description = f'{reviewer_name} reviewed your recommendation "{book_title}"'
    
    _send_notification_and_push(
        recipient=post_author,
        sender=review.user,
        verb='reviewed your book',
        description=description,
        target_object=book,
        push_head="New Book Review",
        push_body=f'{reviewer_name} gave {review.rating} stars to "{book_title}".',
        push_url=_get_absolute_url(book)
    )


def send_comment_reply_notification(comment, parent_comment):
    if not parent_comment.user:
        return 
    if comment.user and comment.user == parent_comment.user:
        return 
    
    commenter_name = comment.user.get_display_name() if comment.user else comment.name
    description = f'{commenter_name} replied to your comment'

    # Get the actual post from the parent comment's content object
    post = parent_comment.content_object

    _send_notification_and_push(
        recipient=parent_comment.user,
        sender=comment.user,
        verb='replied to your comment',
        description=description,
        target_object=comment,
        push_head="New Reply",
        push_body=f'{commenter_name} replied to your comment.',
        push_url=f"{_get_absolute_url(post)}#comment-{comment.id}"
    )


def send_message_notification(message, recipient):
    description = f'{message.sender.get_display_name()} sent you a message'
    
    _send_notification_and_push(
        recipient=recipient,
        sender=message.sender,
        verb='sent you a message',
        description=description,
        target_object=message.thread,
        push_head="New Message",
        push_body=f'{message.sender.full_name} sent you a message.',
        push_url=reverse('users:thread', args=[message.thread.id])
    )
    
    # Simplified email logic for brevity in this step
    if recipient.email:
        subject = f'New message from {message.sender.full_name}'
        send_email_notification(recipient.email, subject, description)


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
        push_body=f'{suggester.full_name} suggested an edit.',
        push_url=reverse('users:dashboard')
    )
    
    if post_author.email:
        send_email_notification(post_author.email, 'Edit suggestion on your post', description)


def send_edit_suggestion_approved_notification(suggestion):
    description = f'Your edit suggestion for "{suggestion.post.title}" was approved.'
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
    description = f'Your edit suggestion for "{suggestion.post.title}" was declined.'
    _send_notification_and_push(
        recipient=suggestion.suggested_by,
        sender=suggestion.post.author,
        verb='declined your edit suggestion',
        description=description,
        target_object=suggestion.post,
        push_head="Suggestion Declined",
        push_body=description,
        push_url=_get_absolute_url(suggestion.post)
    )


def send_archive_uploaded_notification(user, archive):
    """Notify user that their archive was uploaded successfully."""
    description = f'Your archive "{archive.title}" was uploaded and is pending moderation.'
    _send_notification_and_push(
        recipient=user,
        sender=None,
        verb='uploaded an archive',
        description=description,
        target_object=archive,
        push_head="Archive Uploaded",
        push_body=description,
        push_url=reverse('users:dashboard'),
        allow_self=True
    )


def send_review_posted_notification(user, book):
    """Notify user that their review was posted successfully."""
    description = f'Your review for "{book.book_title}" was posted successfully.'
    _send_notification_and_push(
        recipient=user,
        sender=None,
        verb='posted a review',
        description=description,
        target_object=book,
        push_head="Review Posted",
        push_body=description,
        push_url=_get_absolute_url(book),
        allow_self=True
    )


def send_broadcast_notification(title, body, url="/"):
    """Trigger a site-wide push notification broadcast."""
    try:
        from core.tasks import broadcast_push_notification_task
        broadcast_push_notification_task(title, body, url)
        logger.info(f"Broadcast triggered: {title}")
    except Exception as e:
        logger.warning(f"Failed to trigger broadcast: {e}")


def send_email_notification(to_email, subject, message):
    """Send email notification routed through email_service for quota tracking."""
    try:
        from core.email_service import send_email
        send_email(to_email, subject, message, email_type='instant')
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")