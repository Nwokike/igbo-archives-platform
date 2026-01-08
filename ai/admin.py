from django.contrib import admin
from .models import ChatSession, ChatMessage, ArchiveAnalysis

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'created_at', 'tokens_used')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'session__title', 'session__user__username')
    readonly_fields = ('created_at',)

@admin.register(ArchiveAnalysis)
class ArchiveAnalysisAdmin(admin.ModelAdmin):
    list_display = ('archive', 'analysis_type', 'user', 'created_at')
    list_filter = ('analysis_type', 'created_at')
    search_fields = ('archive__title', 'user__username')
    readonly_fields = ('created_at',)
