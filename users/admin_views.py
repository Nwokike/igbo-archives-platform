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
    send_post_approved_notification(post, 'insight')
    messages.success(request, f'Insight "{post.title}" approved.')
    return redirect('users:moderation_dashboard')

@staff_member_required
def reject_insight(request, pk):
    post = get_object_or_404(InsightPost, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        post.pending_approval = False
        post.is_approved = False
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
    send_post_approved_notification(review, 'book review')
    messages.success(request, f'Review "{review.title}" approved.')
    return redirect('users:moderation_dashboard')

@staff_member_required
def reject_book_review(request, pk):
    review = get_object_or_404(BookRecommendation, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        review.pending_approval = False
        review.is_approved = False
        review.save()
        send_post_rejected_notification(review, reason, 'book review')
        messages.info(request, f'Review "{review.title}" rejected.')
        return redirect('users:moderation_dashboard')
    return render(request, 'users/admin/reject_post.html', {'post': review, 'post_type': 'book review'})

# --- NEW: Archive Actions ---
@staff_member_required
def approve_archive(request, pk):
    archive = get_object_or_404(Archive, pk=pk)
    archive.is_approved = True
    archive.save()
    # Notify user (You may need to ensure notifications_utils handles 'archive')
    try:
        send_post_approved_notification(archive, 'archive')
    except Exception:
        logger.warning("Failed to send archive approval notification")
        
    messages.success(request, f'Archive "{archive.title}" approved.')
    return redirect('users:moderation_dashboard')

@staff_member_required
def reject_archive(request, pk):
    archive = get_object_or_404(Archive, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        # For archives, rejection leaves it unapproved but allows user to edit/resubmit
        # We do NOT delete it automatically to prevent data loss.
        try:
            send_post_rejected_notification(archive, reason, 'archive')
        except Exception:
            logger.warning("Failed to send archive rejection notification")
        messages.info(request, f'Archive "{archive.title}" rejected.')
        return redirect('users:moderation_dashboard')
    return render(request, 'users/admin/reject_post.html', {'post': archive, 'post_type': 'archive'})