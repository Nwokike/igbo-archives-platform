from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Notification, Thread, Message

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'full_name', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('full_name', 'bio', 'profile_picture', 'social_links')}),
    )
    actions = ['send_onboarding_email']

    @admin.action(description='Send onboarding/claim profile email')
    def send_onboarding_email(self, request, queryset):
        from .utils import send_claim_profile_email
        sent_count = 0
        skipped_count = 0
        
        for user in queryset:
            # Only send if they haven't set a password (unusable password)
            if not user.has_usable_password():
                if send_claim_profile_email(user):
                    sent_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
        
        self.message_user(
            request,
            f"Successfully sent onboarding emails to {sent_count} users. Skipped {skipped_count} (already have passwords or error).",
            level='INFO' if sent_count > 0 else 'WARNING'
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
