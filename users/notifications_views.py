from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Notification  # <--- IMPORT YOUR NEW MODEL
from django.http import JsonResponse, HttpRequest

@login_required
def notifications_list(request: HttpRequest):
    """Display all notifications for the logged-in user"""
    # request.user.notifications.all() works because we added related_name='notifications'
    notifications_query = request.user.notifications.all()
    
    # Filter by read/unread
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications_query = notifications_query.filter(unread=True)
    elif filter_type == 'read':
        notifications_query = notifications_query.filter(unread=False)
    
    # Paginate
    paginator = Paginator(notifications_query, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'filter_type': filter_type,
    }
    
    return render(request, 'users/notifications.html', context)


@login_required
def notification_mark_read(request: HttpRequest, notification_id: int):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    # Use the method we defined on the model
    notification.mark_as_read() 
    
    if request.htmx or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # Fallback for non-JS click
    return redirect('users:notifications')


@login_required
def notification_mark_all_read(request: HttpRequest):
    """Mark all notifications as read"""
    # Use update() for an efficient bulk update
    request.user.notifications.filter(unread=True).update(unread=False)
    
    if request.htmx or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # Fallback for non-JS click
    return redirect('users:notifications')


@login_required
def notification_dropdown(request: HttpRequest):
    """Return top 5 unread notifications for dropdown"""
    notifications = request.user.notifications.filter(unread=True)[:5]
    unread_count = request.user.notifications.filter(unread=True).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'users/partials/notification_dropdown.html', context)