from django.urls import path, re_path
from . import views
from . import notifications_views
from . import admin_views
from .username_utils import RESERVED_USERNAMES

app_name = 'users'


def _validate_username(view_func):
    """Decorator to reject reserved usernames in URL patterns."""
    from django.http import Http404
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, username, *args, **kwargs):
        if username.lower() in RESERVED_USERNAMES:
            raise Http404
        return view_func(request, username, *args, **kwargs)
    return wrapper


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('messages/', views.message_inbox, name='inbox'),
    path('messages/<int:thread_id>/', views.message_thread, name='thread'),
    path('messages/compose/<str:username>/', views.compose_message, name='compose'),
    path('notifications/', notifications_views.notifications_list, name='notifications'),
    path('notifications/<int:notification_id>/mark-read/', notifications_views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', notifications_views.notification_mark_all_read, name='notification_mark_all_read'),
    path('notifications/dropdown/', notifications_views.notification_dropdown, name='notification_dropdown'),
    
    # Admin / Moderation
    path('admin/moderation/', admin_views.moderation_dashboard, name='moderation_dashboard'),
    
    path('admin/insights/<int:pk>/approve/', admin_views.approve_insight, name='approve_insight'),
    path('admin/insights/<int:pk>/reject/', admin_views.reject_insight, name='reject_insight'),
    
    path('admin/books/<int:pk>/approve/', admin_views.approve_book_review, name='approve_book_review'),
    path('admin/books/<int:pk>/reject/', admin_views.reject_book_review, name='reject_book_review'),
    
    # NEW: Archive URLs
    path('admin/archives/<int:pk>/approve/', admin_views.approve_archive, name='approve_archive'),
    path('admin/archives/<int:pk>/reject/', admin_views.reject_archive, name='reject_archive'),

    path('<str:username>/', _validate_username(views.profile_view), name='profile'),
    path('<str:username>/edit/', _validate_username(views.profile_edit), name='profile_edit'),
]