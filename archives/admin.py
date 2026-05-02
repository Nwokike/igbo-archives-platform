from django.contrib import admin
from .models import Category, Archive, ArchiveItem, Author


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


class ArchiveItemInline(admin.StackedInline):
    """
    Allows editing multiple items directly inside the Parent Archive page.
    Using StackedInline because file upload fields need horizontal space.
    """
    model = ArchiveItem
    extra = 0
    fields = ['item_number', 'item_type', 'image', 'video', 'audio', 'document', 'caption', 'alt_text', 'description']
    ordering = ['item_number']


@admin.action(description='✅ Approve selected archives')
def approve_archives(modeladmin, request, queryset):
    from core.notifications_utils import send_post_approved_notification
    from core.tasks import notify_indexnow
    from django.core.cache import cache
    count = 0
    for archive in queryset.filter(is_approved=False):
        archive.is_approved = True
        archive.is_rejected = False
        archive.save(update_fields=['is_approved', 'is_rejected'])
        send_post_approved_notification(archive, post_type='archive')
        if archive.slug:
            notify_indexnow(f"https://igboarchives.com.ng/archives/{archive.slug}/")
        count += 1
    cache.delete('all_approved_archive_ids')
    cache.delete('archive_categories')
    modeladmin.message_user(request, f'{count} archive(s) approved and notifications sent.')


@admin.action(description='❌ Reject selected archives')
def reject_archives(modeladmin, request, queryset):
    from core.notifications_utils import send_post_rejected_notification
    count = 0
    for archive in queryset.filter(is_rejected=False):
        archive.is_approved = False
        archive.is_rejected = True
        archive.save(update_fields=['is_approved', 'is_rejected'])
        send_post_rejected_notification(archive, reason=archive.rejection_reason or 'Did not meet guidelines', post_type='archive')
        count += 1
        count += 1
    modeladmin.message_user(request, f'{count} archive(s) rejected and notifications sent.')


@admin.action(description='📱 Post selected to Social Media (FB, IG, Mastodon)')
def post_to_social_media_action(modeladmin, request, queryset):
    from core.tasks import post_to_social_media_task
    count = 0
    for obj in queryset:
        post_to_social_media_task(app_label=obj._meta.app_label, model_name=obj._meta.model_name, object_id=obj.id)
        count += 1
    modeladmin.message_user(request, f'{count} item(s) queued for social media posting.')


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = ['title', 'archive_type', 'category', 'item_count', 'uploaded_by', 'created_at', 'is_approved']
    list_filter = ['archive_type', 'category', 'is_approved', 'is_rejected', 'item_count']
    search_fields = ['title', 'description', 'original_author']
    list_editable = ['category']
    actions = [approve_archives, reject_archives, post_to_social_media_action]
    inlines = [ArchiveItemInline]
    raw_id_fields = ['uploaded_by']
    readonly_fields = ['slug', 'sort_year', 'created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'description', 'archive_type', 'category', 'item_count')
        }),
        ('Primary Media (Cover)', {
            'fields': ('image', 'video', 'audio', 'document', 'featured_image')
        }),
        ('Caption & Copyright', {
            'fields': ('caption', 'copyright_holder', 'alt_text')
        }),
        ('Source Information', {
            'fields': ('original_author', 'author', 'original_url', 'original_identity_number')
        }),
        ('Date & Location', {
            'fields': ('date_created', 'circa_date', 'location', 'sort_year')
        }),
        ('Status', {
            'fields': ('uploaded_by', 'is_approved', 'is_rejected', 'rejection_reason', 'created_at', 'updated_at')
        }),
    )