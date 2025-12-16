from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Notification
from django.http import JsonResponse, HttpRequest


@login_required
def notifications_list(request: HttpRequest):
    """Display all notifications for the logged-in user"""
    notifications_query = request.user.notifications.all()
    
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications_query = notifications_query.filter(unread=True)
    elif filter_type == 'read':
        notifications_query = notifications_query.filter(unread=False)
    
    paginator = Paginator(notifications_query, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'notifications': page_obj,
        'filter_type': filter_type,
    }
    
    return render(request, 'users/notifications.html', context)


@login_required
def notification_mark_read(request: HttpRequest, notification_id: int):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    notification.mark_as_read()
    
    if request.htmx or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('users:notifications')


@login_required
def notification_mark_all_read(request: HttpRequest):
    """Mark all notifications as read"""
    request.user.notifications.filter(unread=True).update(unread=False)
    
    if request.htmx or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('users:notifications')


@login_required
def notification_dropdown(request: HttpRequest):
    """Return top 5 unread notifications for dropdown - optimized single query"""
    unread_qs = request.user.notifications.filter(unread=True)
    unread_count = unread_qs.count()
    notifications = unread_qs[:5]
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'users/partials/notification_dropdown.html', context)
