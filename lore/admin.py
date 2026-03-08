"""
Lore App Admin Registration.
Mirrors the structure of archives and books admin for consistency.
"""
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import LorePost
from archives.models import Category


class LoreCategoryFilter(admin.SimpleListFilter):
    """Filter lore posts by their category."""
    title = 'category'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return Category.objects.filter(type='lore').values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category_id=self.value())
        return queryset


@admin.register(LorePost)
class LorePostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_published', 'is_approved', 'pending_approval', 'created_at')
    list_filter = ('is_published', 'is_approved', 'pending_approval', 'is_rejected', LoreCategoryFilter)
    search_fields = ('title', 'excerpt', 'original_author', 'author__username', 'author__full_name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'content_preview')
    list_editable = ('is_published', 'is_approved')
    date_hierarchy = 'created_at'
    actions = ['approve_posts', 'reject_posts', 'publish_posts', 'unpublish_posts']

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'original_author', 'category', 'excerpt')
        }),
        ('Media', {
            'fields': ('featured_image', 'image_url', 'featured_video', 'video_url', 'featured_audio', 'audio_url', 'alt_text'),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('content_preview',),
            'classes': ('wide',)
        }),
        ('Status', {
            'fields': ('is_published', 'is_approved', 'pending_approval', 'is_rejected', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def approve_posts(self, request, queryset):
        from core.notifications_utils import send_post_approved_notification
        from core.tasks import notify_indexnow
        from django.core.cache import cache
        count = 0
        for post in queryset.filter(is_approved=False):
            post.is_approved = True
            post.is_published = True
            post.pending_approval = False
            post.is_rejected = False
            post.save(update_fields=['is_approved', 'is_published', 'pending_approval', 'is_rejected'])
            send_post_approved_notification(post, post_type='lore')
            if post.slug:
                notify_indexnow(f"https://igboarchives.com.ng/lore/{post.slug}/")
            count += 1
        cache.delete('lore_categories')
        self.message_user(request, f"{count} lore post(s) approved, published, and notifications sent.")
    approve_posts.short_description = "Approve and publish selected lore posts"

    def reject_posts(self, request, queryset):
        from core.notifications_utils import send_post_rejected_notification
        count = 0
        for post in queryset.filter(is_rejected=False):
            post.is_approved = False
            post.is_published = False
            post.is_rejected = True
            post.pending_approval = False
            post.save(update_fields=['is_approved', 'is_published', 'is_rejected', 'pending_approval'])
            send_post_rejected_notification(post, reason=post.rejection_reason or 'Did not meet guidelines', post_type='lore')
            count += 1
        self.message_user(request, f"{count} lore post(s) rejected and notifications sent.")
    reject_posts.short_description = "Reject selected lore posts"

    def publish_posts(self, request, queryset):
        queryset.update(is_published=True)
    publish_posts.short_description = "Publish selected lore posts"

    def unpublish_posts(self, request, queryset):
        queryset.update(is_published=False)
    unpublish_posts.short_description = "Unpublish selected lore posts"

    def content_preview(self, obj):
        """Render EditorJS content as preview text."""
        if not obj.content_json or not isinstance(obj.content_json, dict):
            return obj.legacy_content[:200] if obj.legacy_content else "No content"
        blocks = obj.content_json.get('blocks', [])
        if not blocks:
            return "No content blocks"
        import re
        parts = []
        for block in blocks[:5]:
            text = block.get('data', {}).get('text', '')
            if text:
                parts.append(re.sub(r'<[^>]+>', '', text))
        return mark_safe('<br>'.join(parts[:3]) + ('...' if len(parts) > 3 else ''))
    content_preview.short_description = "Content Preview"
