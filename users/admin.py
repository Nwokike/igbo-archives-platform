from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Notification, Thread, Message

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'full_name', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('full_name', 'bio', 'profile_picture', 'social_links')}),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'verb', 'unread', 'timestamp']
    list_filter = ['unread', 'timestamp']
    search_fields = ['recipient__username', 'verb', 'description']


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['subject', 'created_at']
    search_fields = ['subject']
    filter_horizontal = ['participants']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['thread', 'sender', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__username', 'content']
