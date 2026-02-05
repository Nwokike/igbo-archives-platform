from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import BookRecommendation, UserBookRating


@admin.register(BookRecommendation)
class BookRecommendationAdmin(admin.ModelAdmin):
    list_display = ['book_title', 'author', 'added_by', 'is_published', 'created_at']
    list_filter = ['is_published', 'is_approved', 'created_at']
    search_fields = ['book_title', 'author', 'title']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['content_preview']
    
    fieldsets = (
        ('Book Info', {
            'fields': ('book_title', 'author', 'publisher', 'publication_year', 'isbn')
        }),
        ('Review', {
            'fields': ('title', 'slug', 'rating', 'added_by')
        }),
        ('Content', {
            'fields': ('content_preview',),
            'classes': ('wide',)
        }),
        ('Status', {
            'fields': ('is_published', 'is_approved', 'pending_approval')
        }),
    )
    
    def content_preview(self, obj):
        """Render EditorJS content as HTML for admin preview."""
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
                level = data.get('level', 2)
                text = data.get('text', '')
                html_parts.append(f'<h{level} style="margin:0.5em 0">{text}</h{level}>')
            elif block_type == 'paragraph':
                text = data.get('text', '')
                html_parts.append(f'<p style="margin:0.5em 0">{text}</p>')
            elif block_type == 'list':
                style = data.get('style', 'unordered')
                tag = 'ol' if style == 'ordered' else 'ul'
                items = data.get('items', [])
                items_html = ''.join(f'<li>{item}</li>' for item in items if isinstance(item, str))
                html_parts.append(f'<{tag} style="margin:0.5em 0;padding-left:1.5em">{items_html}</{tag}>')
            elif block_type == 'quote':
                text = data.get('text', '')
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
    list_display = ['book', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['book__book_title', 'user__email']
