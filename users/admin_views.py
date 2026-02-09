from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
import logging
from insights.models import InsightPost
from books.models import BookRecommendation
from archives.models import Archive
from core.notifications_utils import send_post_approved_notification, send_post_rejected_notification

logger = logging.getLogger(__name__)

@staff_member_required
def moderation_dashboard(request):
    """Admin moderation dashboard showing pending posts"""
    pending_insights = InsightPost.objects.filter(
        pending_approval=True, is_approved=False
    ).select_related('author').order_by('-submitted_at')
    
    pending_books = BookRecommendation.objects.filter(
        pending_approval=True, is_approved=False
    ).select_related('added_by').order_by('-submitted_at')

    # ADDED: Pending Archives
    pending_archives = Archive.objects.filter(
        is_approved=False
    ).select_related('uploaded_by', 'category').order_by('-created_at')
    
    context = {
        'pending_insights': pending_insights,
        'pending_books': pending_books,
        'pending_archives': pending_archives,
    }
    
    return render(request, 'users/admin/moderation_dashboard.html', context)

@staff_member_required
def approve_insight(request, pk):
    post = get_object_or_404(InsightPost, pk=pk)
    post.is_published = True
    post.is_approved = True
    post.pending_approval = False
    post.save()
    from core.notifications_utils import send_post_approved_notification, send_broadcast_notification
    send_post_approved_notification(post, 'insight')
    send_broadcast_notification(
        f"New Insight: {post.title}", 
        f"Read the latest heritage insight by {post.author.get_display_name()}", 
        post.get_absolute_url()
    )
    
    # Queue for weekly digest
    from core.email_service import queue_for_digest
    queue_for_digest('insight', post.id, post.title, post.author.get_display_name(), post.get_absolute_url())
    
    messages.success(request, f'Insight "{post.title}" approved.')
    return redirect('users:moderation_dashboard')

@staff_member_required
def reject_insight(request, pk):
    post = get_object_or_404(InsightPost, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        post.pending_approval = False
        post.is_approved = False
        post.is_rejected = True
        post.rejection_reason = reason
        post.save()
        send_post_rejected_notification(post, reason, 'insight')
        messages.info(request, f'Insight "{post.title}" rejected.')
        return redirect('users:moderation_dashboard')
    return render(request, 'users/admin/reject_post.html', {'post': post, 'post_type': 'insight'})

@staff_member_required
def approve_book_review(request, pk):
    review = get_object_or_404(BookRecommendation, pk=pk)
    review.is_published = True
    review.is_approved = True
    review.pending_approval = False
    review.save()
    from core.notifications_utils import send_post_approved_notification, send_broadcast_notification
    send_post_approved_notification(review, 'book review')
    send_broadcast_notification(
        f"New Book: {review.book_title}", 
        f"A new book recommendation has been published by {review.added_by.get_display_name()}", 
        review.get_absolute_url()
    )
    
    # Queue for weekly digest
    from core.email_service import queue_for_digest
    queue_for_digest('book', review.id, review.book_title, review.added_by.get_display_name(), review.get_absolute_url())
    
    messages.success(request, f'Review "{review.title}" approved.')
    return redirect('users:moderation_dashboard')

@staff_member_required
def reject_book_review(request, pk):
    review = get_object_or_404(BookRecommendation, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        review.pending_approval = False
        review.is_approved = False
        review.is_rejected = True
        review.rejection_reason = reason
        review.save()
        send_post_rejected_notification(review, reason, 'book review')
        messages.info(request, f'Review "{review.title}" rejected.')
        return redirect('users:moderation_dashboard')
    return render(request, 'users/admin/reject_post.html', {'post': review, 'post_type': 'book review'})

# --- NEW: Archive Actions ---
@staff_member_required
def approve_archive(request, pk):
    # Use update() to avoid triggering the full save() method which includes
    # image compression that can hold database locks for too long
    from django.utils import timezone
    updated = Archive.objects.filter(pk=pk, is_approved=False).update(
        is_approved=True,
        updated_at=timezone.now()
    )
    
    if not updated:
        messages.warning(request, 'Archive not found or already approved.')
        return redirect('users:moderation_dashboard')
    
    # Fetch for notification after the update completes
    archive = Archive.objects.get(pk=pk)
    
    try:
        from core.notifications_utils import send_post_approved_notification, send_broadcast_notification
        send_post_approved_notification(archive, 'archive')
        send_broadcast_notification(
            f"New Archive: {archive.title}", 
            f"Explore a new heritage archive from {archive.uploaded_by.get_display_name()}", 
            archive.get_absolute_url()
        )
        
        # Queue for weekly digest
        from core.email_service import queue_for_digest
        queue_for_digest('archive', archive.id, archive.title, archive.uploaded_by.get_display_name(), archive.get_absolute_url())
    except Exception:
        logger.warning("Failed to send archive approval/broadcast notification")
        
    messages.success(request, f'Archive "{archive.title}" approved.')
    return redirect('users:moderation_dashboard')

@staff_member_required
def reject_archive(request, pk):
    archive = get_object_or_404(Archive, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        # For archives, rejection leaves it unapproved but allows user to edit/resubmit
        archive.is_approved = False
        archive.is_rejected = True
        archive.rejection_reason = reason
        archive.save()
        
        try:
            send_post_rejected_notification(archive, reason, 'archive')
        except Exception:
            logger.warning("Failed to send archive rejection notification")
        messages.info(request, f'Archive "{archive.title}" rejected.')
        return redirect('users:moderation_dashboard')
    return render(request, 'users/admin/reject_post.html', {'post': archive, 'post_type': 'archive'})