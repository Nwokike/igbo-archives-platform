from django.contrib import admin
from django.utils.safestring import mark_safe
import nh3
from .models import BookRecommendation, UserBookRating

# Allowed tags for admin preview
ADMIN_PREVIEW_ALLOWED_TAGS = {'b', 'i', 'u', 'strong', 'em', 'br'}

class UserBookRatingInline(admin.TabularInline):
    """
    NEW: Allows you to see and delete reviews directly inside the Book page.
    """
    model = UserBookRating
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('user', 'rating', 'review_text', 'created_at')
    can_delete = True
    show_change_link = True

@admin.register(BookRecommendation)
class BookRecommendationAdmin(admin.ModelAdmin):
    list_display = ['book_title', 'author', 'added_by', 'is_published', 'is_approved', 'created_at']
    list_filter = ['is_published', 'is_approved', 'created_at']
    search_fields = ['book_title', 'author', 'title', 'added_by__username', 'added_by__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['content_preview']
    
    # NEW: Add the reviews inline here
    inlines = [UserBookRatingInline]
    
    # NEW: Bulk actions to save you time
    actions = ['approve_books', 'publish_books', 'unpublish_books']

    fieldsets = (
        ('Book Info', {
            'fields': ('book_title', 'author', 'publisher', 'publication_year', 'isbn', 'external_url')
        }),
        ('Recommendation', {
            'fields': ('title', 'slug', 'added_by')
        }),
        ('Cover Image', {
            'fields': ('cover_image',),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('content_preview',),
            'classes': ('wide',)
        }),
        ('Status', {
            'fields': ('is_published', 'is_approved', 'pending_approval', 'submitted_at')
        }),
    )

    def approve_books(self, request, queryset):
        queryset.update(is_approved=True, is_published=True, pending_approval=False)
    approve_books.short_description = "Approve and publish selected books"

    def publish_books(self, request, queryset):
        queryset.update(is_published=True)
    publish_books.short_description = "Publish selected books"

    def unpublish_books(self, request, queryset):
        queryset.update(is_published=False)
    unpublish_books.short_description = "Unpublish selected books"
    
    def content_preview(self, obj):
        """Render EditorJS content as HTML for admin preview with XSS protection."""
        if not obj.content_json or not isinstance(obj.content_json, dict):
            return "No content"
        
        blocks = obj.content_json.get('blocks', [])
        if not blocks:
            return "No content blocks"
        
        html_parts = []
        for block in blocks[:20]:
            block_type = block.get('type', 'paragraph')
            data = block.get('data', {})
            
            if block_type == 'header':
                level = min(max(int(data.get('level', 2)), 1), 6)
                text = nh3.clean(data.get('text', ''), tags=ADMIN_PREVIEW_ALLOWED_TAGS)
                html_parts.append(f'<h{level} style="margin:0.5em 0">{text}</h{level}>')
            elif block_type == 'paragraph':
                text = nh3.clean(data.get('text', ''), tags=ADMIN_PREVIEW_ALLOWED_TAGS)
                html_parts.append(f'<p style="margin:0.5em 0">{text}</p>')
            elif block_type == 'list':
                style = data.get('style', 'unordered')
                tag = 'ol' if style == 'ordered' else 'ul'
                items = data.get('items', [])
                items_html_parts = []
                for item in items:
                    # Handle nested list items (dicts with 'content' key)
                    if isinstance(item, dict):
                        text = item.get('content', '')
                    elif isinstance(item, str):
                        text = item
                    else:
                        continue
                    items_html_parts.append(f'<li>{nh3.clean(text, tags=ADMIN_PREVIEW_ALLOWED_TAGS)}</li>')
                items_html = ''.join(items_html_parts)
                html_parts.append(f'<{tag} style="margin:0.5em 0;padding-left:1.5em">{items_html}</{tag}>')
            elif block_type == 'quote':
                text = nh3.clean(data.get('text', ''), tags=ADMIN_PREVIEW_ALLOWED_TAGS)
                html_parts.append(f'<blockquote style="margin:1em 0;padding:0.5em 1em;border-left:3px solid #ddd;background:#f9f9f9">{text}</blockquote>')
            elif block_type == 'delimiter':
                html_parts.append('<hr style="margin:1em 0">')
        
        if len(blocks) > 20:
            html_parts.append(f'<p style="color:#888"><em>... and {len(blocks) - 20} more blocks</em></p>')
        
        content = ''.join(html_parts)
        return mark_safe(f'<div style="max-width:700px;padding:1rem;background:#fafafa;border-radius:8px;border:1px solid #e0e0e0">{content}</div>')
    
    content_preview.short_description = 'Content Preview'


@admin.register(UserBookRating)
class UserBookRatingAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'short_review', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['book__book_title', 'user__username', 'user__email', 'review_text']
    readonly_fields = ('created_at', 'updated_at')

    def short_review(self, obj):
        return obj.review_text[:50] + "..." if obj.review_text else ""
    short_review.short_description = "Review Snippet"