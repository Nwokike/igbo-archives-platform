from django.urls import path
from . import views
from . import notifications_views
from . import admin_views

app_name = 'users'

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
    path('admin/moderation/', admin_views.moderation_dashboard, name='moderation_dashboard'),
    path('admin/insights/<int:pk>/approve/', admin_views.approve_insight, name='approve_insight'),
    path('admin/insights/<int:pk>/reject/', admin_views.reject_insight, name='reject_insight'),
    path('admin/books/<int:pk>/approve/', admin_views.approve_book_review, name='approve_book_review'),
    path('admin/books/<int:pk>/reject/', admin_views.reject_book_review, name='reject_book_review'),
    path('<str:username>/', views.profile_view, name='profile'),
    path('<str:username>/edit/', views.profile_edit, name='profile_edit'),
]
