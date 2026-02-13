"""
AI Models for Igbo Archives.
Handles chat sessions, messages, and archive analysis.
"""
from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """A conversation session between a user and the AI."""
    # CASCADE is intentional (privacy-by-design): deleting a user removes their chat history
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_chat_sessions'
    )
    title = models.CharField(max_length=255, default='New Conversation')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def get_context_messages(self, limit=10):
        """Get recent messages for AI context (ordered oldest-first)."""
        # Use a subquery to get only the last N messages, then order ascending
        # Avoids loading all rows into Python memory just to slice and reverse
        recent_ids = self.messages.order_by('-created_at').values_list('id', flat=True)[:limit]
        return self.messages.filter(id__in=recent_ids).order_by('created_at')


class ChatMessage(models.Model):
    """A single message in a chat session."""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    tokens_used = models.IntegerField(default=0)
    model_used = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class ArchiveAnalysis(models.Model):
    """AI-generated analysis of an archive item."""
    archive = models.ForeignKey(
        'archives.Archive',
        on_delete=models.CASCADE,
        related_name='ai_analyses'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='archive_analyses'
    )
    analysis_type = models.CharField(max_length=50, choices=[
        ('description', 'Image Description'),
        ('historical', 'Historical Context'),
        ('cultural', 'Cultural Significance'),
        ('translation', 'Text Translation'),
        ('artifact', 'Artifact Identification'),
    ])
    content = models.TextField()
    model_used = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Archive analyses'
    
    def __str__(self):
        return f"{self.analysis_type} of {self.archive.title}"
