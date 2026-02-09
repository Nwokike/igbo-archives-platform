"""
User views for authentication, profiles, messaging, and notifications.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages as django_messages
from django.core.cache import cache
from django.db.models import Q
import bleach
import logging
from .models import Thread, Message
from .forms import ProfileEditForm

logger = logging.getLogger(__name__)

User = get_user_model()


@login_required
def dashboard(request):
    """User dashboard showing their content and activity."""
    from archives.models import Archive
    from insights.models import InsightPost, EditSuggestion
    from books.models import BookRecommendation
    from django.core.paginator import Paginator
    
    user = request.user
    
    messages_threads = user.message_threads.prefetch_related('participants')[:10]
    
    # Insights with pagination
    insights_queryset = InsightPost.objects.filter(
        author=user
    ).filter(
        Q(is_published=True) | Q(pending_approval=True)
    ).order_by('-created_at')
    insights_paginator = Paginator(insights_queryset, 20)
    my_insights = insights_paginator.get_page(request.GET.get('insights_page', 1))
    
    my_drafts = InsightPost.objects.filter(
        author=user,
        is_published=False,
        pending_approval=False
    ).order_by('-created_at')[:10]
    
    # Books with pagination
    books_queryset = BookRecommendation.objects.filter(
        added_by=user
    ).order_by('-created_at')
    books_paginator = Paginator(books_queryset, 20)
    my_book_recommendations = books_paginator.get_page(request.GET.get('books_page', 1))
    
    # Archives with pagination
    archives_queryset = Archive.objects.filter(
        uploaded_by=user
    ).select_related('category').order_by('-created_at')
    archives_paginator = Paginator(archives_queryset, 20)
    my_archives = archives_paginator.get_page(request.GET.get('archives_page', 1))
    
    edit_suggestions = EditSuggestion.objects.filter(
        post__author=user,
        is_approved=False,
        is_rejected=False
    ).select_related('post', 'suggested_by').order_by('-created_at')[:10]
    
    context = {
        'messages_threads': messages_threads,
        'my_insights': my_insights,
        'my_insights_count': insights_queryset.count(),
        'my_drafts': my_drafts,
        'my_drafts_count': my_drafts.count(),
        'my_book_recommendations': my_book_recommendations,
        'my_book_recommendations_count': books_queryset.count(),
        'my_archives': my_archives,
        'my_archives_count': archives_queryset.count(),
        'edit_suggestions': edit_suggestions,
    }
    
    if request.htmx:
        target = request.GET.get('target')
        if target == 'insights':
            return render(request, 'users/partials/dashboard_insights.html', context)
        elif target == 'books':
            return render(request, 'users/partials/dashboard_books.html', context)
        elif target == 'archives':
            return render(request, 'users/partials/dashboard_archives.html', context)
            
    return render(request, 'users/dashboard.html', context)


def profile_view(request, username):
    """Public profile view - only shows approved content."""
    from archives.models import Archive
    from insights.models import InsightPost
    from books.models import BookRecommendation
    from django.core.paginator import Paginator
    
    user = get_object_or_404(User, username=username)
    
    # Archives with pagination
    archives_queryset = Archive.objects.filter(
        uploaded_by=user,
        is_approved=True
    ).select_related('category').order_by('-created_at')
    archives_paginator = Paginator(archives_queryset, 20)
    archives = archives_paginator.get_page(request.GET.get('archives_page', 1))
    
    # Insights with pagination
    insights_queryset = InsightPost.objects.filter(
        author=user,
        is_published=True,
        is_approved=True
    ).order_by('-created_at')
    insights_paginator = Paginator(insights_queryset, 20)
    insights = insights_paginator.get_page(request.GET.get('insights_page', 1))
    
    # Books with pagination
    books_queryset = BookRecommendation.objects.filter(
        added_by=user,
        is_published=True,
        is_approved=True
    ).order_by('-created_at')
    books_paginator = Paginator(books_queryset, 20)
    book_recommendations = books_paginator.get_page(request.GET.get('books_page', 1))
    
    context = {
        'profile_user': user,
        'user_archives': archives,
        'user_archives_count': archives_queryset.count(),
        'user_insights': insights,
        'user_insights_count': insights_queryset.count(),
        'user_book_recommendations': book_recommendations,
        'user_book_recommendations_count': books_queryset.count(),
    }
    
    if request.htmx:
        target = request.GET.get('target')
        if target == 'insights':
            return render(request, 'users/partials/profile_insights.html', context)
        elif target == 'books':
            return render(request, 'users/partials/profile_books.html', context)
        elif target == 'archives':
            return render(request, 'users/partials/profile_archives.html', context)
            
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
        # Rate limiting: 20 messages per hour
        rate_key = f'msg_rate_{request.user.id}'
        msg_count = cache.get(rate_key, 0)
        if msg_count >= 20:
            django_messages.error(request, 'Message limit reached. Please wait before sending more.')
            return redirect('users:thread', thread_id=thread_id)
        
        content = request.POST.get('content', '').strip()
        if not content:
            django_messages.error(request, 'Message cannot be empty.')
        elif len(content) > 10000:
            django_messages.error(request, 'Message is too long (max 10,000 characters).')
        else:
            # Sanitize content with bleach to prevent XSS
            clean_content = bleach.clean(content, strip=True)
            Message.objects.create(
                thread=thread,
                sender=request.user,
                content=clean_content
            )
            cache.set(rate_key, msg_count + 1, 3600)
            # Bell Notification (Confirmation for sender)
            try:
                from core.notifications_utils import _send_notification_and_push
                _send_notification_and_push(
                    recipient=request.user,
                    sender=None,
                    verb='sent a message',
                    description=f'Your message to {thread.participants.exclude(id=request.user.id).first().get_display_name()} was sent.',
                    target_object=thread,
                    push_head="Message Sent",
                    push_body="Your message was delivered.",
                    push_url=reverse('users:thread', args=[thread.id])
                )
            except Exception as e:
                logger.warning(f"Failed to send in-app notification to sender: {e}")

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
        # Rate limiting: 20 messages per hour
        rate_key = f'msg_rate_{request.user.id}'
        msg_count = cache.get(rate_key, 0)
        if msg_count >= 20:
            django_messages.error(request, 'Message limit reached. Please wait before sending more.')
            return redirect('users:profile', username=username)
        
        subject = request.POST.get('subject', '').strip()
        content = request.POST.get('content', '').strip()
        
        if subject and content:
            # Sanitize content with bleach to prevent XSS
            clean_content = bleach.clean(content, strip=True)
            thread = Thread.objects.create(subject=bleach.clean(subject[:255], strip=True))
            thread.participants.add(request.user, recipient)
            Message.objects.create(
                thread=thread,
                sender=request.user,
                content=clean_content[:10000]
            )
            cache.set(rate_key, msg_count + 1, 3600)
            # Bell Notification (Confirmation for sender)
            try:
                from core.notifications_utils import _send_notification_and_push
                _send_notification_and_push(
                    recipient=request.user,
                    sender=None,
                    verb='sent a message',
                    description=f'Your message to {recipient.get_display_name()} was sent.',
                    target_object=thread,
                    push_head="Message Sent",
                    push_body="Your message was delivered.",
                    push_url=reverse('users:thread', args=[thread.id])
                )
            except Exception as e:
                logger.warning(f"Failed to send in-app notification to sender: {e}")

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
            import logging
            logger = logging.getLogger(__name__)
            username = request.user.username
            email = request.user.email
            logger.warning(f"User {username} ({email}) deleted their account")
            request.user.delete()
            cache.delete(rate_key)
            django_messages.success(request, 'Your account has been deleted.')
            return redirect('core:home')
        else:
            cache.set(rate_key, attempts + 1, 3600)
            django_messages.error(request, 'Incorrect password.')
    
    return render(request, 'users/delete_account.html')

