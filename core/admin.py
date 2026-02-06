from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import EmailLog, DigestQueue


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """
    Centralized view of all email activity.
    Shows daily quota, email types, and allows filtering by date/type.
    """
    list_display = ['recipient_email', 'subject_truncated', 'email_type', 'success_badge', 'sent_at']
    list_filter = ['email_type', 'success', 'sent_at']
    search_fields = ['recipient_email', 'subject']
    readonly_fields = ['recipient_email', 'subject', 'email_type', 'sent_at', 'success']
    date_hierarchy = 'sent_at'
    ordering = ['-sent_at']
    
    def subject_truncated(self, obj):
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
    subject_truncated.short_description = 'Subject'
    
    def success_badge(self, obj):
        if obj.success:
            return format_html('<span style="color:green;">✓ Sent</span>')
        return format_html('<span style="color:red;">✗ Failed</span>')
    success_badge.short_description = 'Status'
    
    def changelist_view(self, request, extra_context=None):
        """Add quota information to the top of the list view."""
        extra_context = extra_context or {}
        
        today = timezone.now().date()
        sent_today = EmailLog.get_daily_count(today)
        remaining = max(0, 300 - sent_today)
        
        extra_context['title'] = f'Email Log - Today: {sent_today}/300 sent, {remaining} remaining'
        return super().changelist_view(request, extra_context=extra_context)
    
    def has_add_permission(self, request):
        return False  # Read-only log
    
    def has_change_permission(self, request, obj=None):
        return False  # Read-only log


@admin.register(DigestQueue)
class DigestQueueAdmin(admin.ModelAdmin):
    """
    Manage weekly digest queue.
    View pending content and manually trigger digest if needed.
    """
    list_display = ['content_type', 'title', 'author_name', 'processed_status', 'created_at']
    list_filter = ['content_type', 'processed', 'created_at']
    search_fields = ['title', 'author_name']
    readonly_fields = ['content_type', 'content_id', 'title', 'author_name', 'url', 'created_at', 'processed', 'processed_at']
    ordering = ['-created_at']
    actions = ['mark_as_processed']
    
    def processed_status(self, obj):
        if obj.processed:
            return format_html('<span style="color:gray;">✓ Sent</span>')
        return format_html('<span style="color:orange;">⏳ Pending</span>')
    processed_status.short_description = 'Status'
    
    @admin.action(description='Mark selected as processed')
    def mark_as_processed(self, request, queryset):
        count = queryset.update(processed=True, processed_at=timezone.now())
        self.message_user(request, f'{count} items marked as processed.')
    
    def has_add_permission(self, request):
        return False  # Content is automatically queued
