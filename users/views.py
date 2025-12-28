"""
User views for authentication, profiles, messaging, and notifications.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages as django_messages
from django.core.cache import cache
from django.db.models import Q
from .models import Thread, Message
from .forms import ProfileEditForm

User = get_user_model()


@login_required
def dashboard(request):
    """User dashboard showing their content and activity."""
    from archives.models import Archive
    from insights.models import InsightPost, EditSuggestion
    from books.models import BookReview
    
    user = request.user
    
    messages_threads = user.message_threads.prefetch_related('participants')[:10]
    
    my_insights = InsightPost.objects.filter(
        author=user
    ).filter(
        Q(is_published=True) | Q(pending_approval=True)
    ).order_by('-created_at')[:20]
    
    my_drafts = InsightPost.objects.filter(
        author=user,
        is_published=False,
        pending_approval=False
    ).order_by('-created_at')[:10]
    
    my_book_reviews = BookReview.objects.filter(
        reviewer=user
    ).order_by('-created_at')[:20]
    
    my_archives = Archive.objects.filter(
        uploaded_by=user
    ).select_related('category').order_by('-created_at')[:20]
    
    edit_suggestions = EditSuggestion.objects.filter(
        post__author=user,
        is_approved=False,
        is_rejected=False
    ).select_related('post', 'suggested_by').order_by('-created_at')[:10]
    
    context = {
        'messages_threads': messages_threads,
        'my_insights': my_insights,
        'my_drafts': my_drafts,
        'my_book_reviews': my_book_reviews,
        'my_archives': my_archives,
        'edit_suggestions': edit_suggestions,
    }
    
    return render(request, 'users/dashboard.html', context)


def profile_view(request, username):
    """Public profile view - only shows approved content."""
    from archives.models import Archive
    from insights.models import InsightPost
    from books.models import BookReview
    
    user = get_object_or_404(User, username=username)
    
    archives = Archive.objects.filter(
        uploaded_by=user,
        is_approved=True
    ).select_related('category').order_by('-created_at')[:20]
    
    insights = InsightPost.objects.filter(
        author=user,
        is_published=True,
        is_approved=True
    ).order_by('-created_at')[:20]
    
    book_reviews = BookReview.objects.filter(
        reviewer=user,
        is_published=True,
        is_approved=True
    ).order_by('-created_at')[:20]
    
    context = {
        'profile_user': user,
        'archives': archives,
        'insights': insights,
        'book_reviews': book_reviews,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def profile_edit(request, username):
    """Edit user profile."""
    if request.user.username != username:
        django_messages.error(request, 'You can only edit your own profile.')
        return redirect('users:profile', username=username)
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            django_messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)
    
    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def message_inbox(request):
    """User message inbox."""
    threads = request.user.message_threads.prefetch_related('participants', 'messages')
    return render(request, 'users/inbox.html', {'threads': threads})


@login_required
def message_thread(request, thread_id):
    """View and reply to a message thread."""
    thread = get_object_or_404(
        Thread.objects.prefetch_related('messages', 'participants'),
        id=thread_id, participants=request.user
    )
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content and len(content) <= 10000:
            Message.objects.create(
                thread=thread,
                sender=request.user,
                content=content[:10000]
            )
            return redirect('users:thread', thread_id=thread_id)
    
    thread.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
    return render(request, 'users/thread.html', {'thread': thread})


@login_required
def compose_message(request, username):
    """Compose a new message to a user."""
    recipient = get_object_or_404(User, username=username)
    
    if recipient == request.user:
        django_messages.error(request, 'You cannot message yourself.')
        return redirect('users:profile', username=username)
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        content = request.POST.get('content', '').strip()
        
        if subject and content:
            thread = Thread.objects.create(subject=subject[:255])
            thread.participants.add(request.user, recipient)
            Message.objects.create(
                thread=thread,
                sender=request.user,
                content=content[:10000]
            )
            django_messages.success(request, 'Message sent successfully!')
            return redirect('users:thread', thread_id=thread.id)
        else:
            django_messages.error(request, 'Subject and message are required.')
    
    return render(request, 'users/compose.html', {'recipient': recipient})


@login_required
def delete_account(request):
    """Delete user account with password confirmation and rate limiting."""
    rate_key = f'delete_attempt_{request.user.id}'
    attempts = cache.get(rate_key, 0)
    
    if attempts >= 5:
        django_messages.error(request, 'Too many failed attempts. Try again in 1 hour.')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        
        if request.user.check_password(password):
            username = request.user.username
            request.user.delete()
            cache.delete(rate_key)
            django_messages.success(request, 'Your account has been deleted.')
            return redirect('core:home')
        else:
            cache.set(rate_key, attempts + 1, 3600)
            django_messages.error(request, 'Incorrect password.')
    
    return render(request, 'users/delete_account.html')
