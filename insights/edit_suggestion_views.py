from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import InsightPost, EditSuggestion
from core.notifications_utils import send_edit_suggestion_notification, send_edit_suggestion_approved_notification, send_edit_suggestion_rejected_notification

# Note: suggest_edit view is now in views.py with rate limiting




@login_required
def approve_edit_suggestion(request, pk):
    """Post author approves an edit suggestion"""
    suggestion = get_object_or_404(EditSuggestion, pk=pk)
    
    # Only post author can approve
    if request.user != suggestion.post.author:
        messages.error(request, 'You can only approve suggestions on your own posts.')
        return redirect('users:dashboard')
    
    suggestion.is_approved = True
    suggestion.is_rejected = False
    suggestion.save()
    
    # Send notification to suggester
    send_edit_suggestion_approved_notification(suggestion)
    
    messages.success(request, f'{suggestion.suggested_by.full_name} can now edit your post.')
    return redirect('users:dashboard')


@login_required
def reject_edit_suggestion(request, pk):
    """Post author rejects an edit suggestion"""
    suggestion = get_object_or_404(EditSuggestion, pk=pk)
    
    # Only post author can reject
    if request.user != suggestion.post.author:
        messages.error(request, 'You can only reject suggestions on your own posts.')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        suggestion.is_rejected = True
        suggestion.is_approved = False
        suggestion.rejection_reason = rejection_reason
        suggestion.save()
        
        # Send notification to suggester
        send_edit_suggestion_rejected_notification(suggestion, rejection_reason)
        
        messages.info(request, 'Edit suggestion has been rejected.')
        return redirect('users:dashboard')
    
    return render(request, 'insights/reject_suggestion.html', {'suggestion': suggestion})
