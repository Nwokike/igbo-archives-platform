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


class ArchiveItemInline(admin.TabularInline):
    model = ArchiveItem
    extra = 0
    fields = ['item_number', 'item_type', 'image', 'video', 'audio', 'document', 'caption', 'alt_text']


@admin.action(description='✅ Approve selected archives')
def approve_archives(modeladmin, request, queryset):
    count = queryset.update(is_approved=True)
    modeladmin.message_user(request, f'{count} archive(s) approved.')


@admin.action(description='❌ Reject selected archives')
def reject_archives(modeladmin, request, queryset):
    count = queryset.update(is_approved=False)
    modeladmin.message_user(request, f'{count} archive(s) rejected.')


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = ['title', 'archive_type', 'category', 'item_count', 'uploaded_by', 'created_at', 'is_approved']
    list_filter = ['archive_type', 'category', 'is_approved', 'item_count']
    search_fields = ['title', 'description', 'original_author']
    list_editable = ['category']  # Removed is_approved - use actions instead
    actions = [approve_archives, reject_archives]
    inlines = [ArchiveItemInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'archive_type', 'category', 'item_count')
        }),
        ('Primary Media', {
            'fields': ('image', 'video', 'audio', 'document', 'featured_image')
        }),
        ('Caption & Copyright', {
            'fields': ('caption', 'copyright_holder', 'alt_text')
        }),
        ('Source Information', {
            'fields': ('original_author', 'author', 'original_url', 'original_identity_number')
        }),
        ('Date & Location', {
            'fields': ('date_created', 'circa_date', 'location')
        }),
        ('Status', {
            'fields': ('uploaded_by', 'is_approved', 'tags')
        }),
    )
