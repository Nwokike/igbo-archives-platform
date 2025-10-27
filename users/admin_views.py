from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from insights.models import InsightPost
from books.models import BookReview
from core.notifications_utils import send_post_approved_notification, send_post_rejected_notification
from django.utils import timezone


@staff_member_required
def moderation_dashboard(request):
    """Admin moderation dashboard showing pending posts"""
    pending_insights = InsightPost.objects.filter(pending_approval=True, is_approved=False)
    pending_books = BookReview.objects.filter(pending_approval=True, is_approved=False)
    
    context = {
        'pending_insights': pending_insights,
        'pending_books': pending_books,
    }
    
    return render(request, 'users/admin/moderation_dashboard.html', context)


@staff_member_required
def approve_insight(request, pk):
    """Approve an insight post"""
    post = get_object_or_404(InsightPost, pk=pk)
    
    post.is_published = True
    post.is_approved = True
    post.pending_approval = False
    post.save()
    
    # Send notification to author
    send_post_approved_notification(post, 'insight')
    
    messages.success(request, f'Insight "{post.title}" has been approved and published.')
    return redirect('users:moderation_dashboard')


@staff_member_required
def reject_insight(request, pk):
    """Reject an insight post"""
    post = get_object_or_404(InsightPost, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        post.pending_approval = False
        post.is_approved = False
        post.save()
        
        # Send notification to author
        send_post_rejected_notification(post, reason, 'insight')
        
        messages.info(request, f'Insight "{post.title}" has been rejected.')
        return redirect('users:moderation_dashboard')
    
    return render(request, 'users/admin/reject_post.html', {'post': post, 'post_type': 'insight'})


@staff_member_required
def approve_book_review(request, pk):
    """Approve a book review"""
    review = get_object_or_404(BookReview, pk=pk)
    
    review.is_published = True
    review.is_approved = True
    review.pending_approval = False
    review.save()
    
    # Send notification to reviewer
    send_post_approved_notification(review, 'book review')
    
    messages.success(request, f'Book review "{review.review_title}" has been approved and published.')
    return redirect('users:moderation_dashboard')


@staff_member_required
def reject_book_review(request, pk):
    """Reject a book review"""
    review = get_object_or_404(BookReview, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        review.pending_approval = False
        review.is_approved = False
        review.save()
        
        # Send notification to reviewer
        send_post_rejected_notification(review, reason, 'book review')
        
        messages.info(request, f'Book review "{review.review_title}" has been rejected.')
        return redirect('users:moderation_dashboard')
    
    return render(request, 'users/admin/reject_post.html', {'post': review, 'post_type': 'book review'})
