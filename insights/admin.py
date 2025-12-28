from django.contrib import admin
from .models import InsightPost, EditSuggestion

@admin.register(InsightPost)
class InsightPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'is_published', 'is_approved', 'created_at']
    list_filter = ['is_published', 'is_approved', 'created_at']
    search_fields = ['title', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(EditSuggestion)
class EditSuggestionAdmin(admin.ModelAdmin):
    list_display = ['post', 'suggested_by', 'is_approved', 'is_rejected', 'created_at']
    list_filter = ['is_approved', 'is_rejected']
