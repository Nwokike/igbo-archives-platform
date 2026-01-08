from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    social_links = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return self.full_name or self.email or self.username
    
    def get_display_name(self):
        return self.full_name or (self.email.split('@')[0] if self.email else self.username)


class Thread(models.Model):
    participants = models.ManyToManyField(CustomUser, related_name='message_threads')
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self) -> str:
        return str(self.subject)


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'is_read'], name='msg_thread_read_idx'),
            models.Index(fields=['sender', '-created_at'], name='msg_sender_date_idx'),
        ]
    
    def __str__(self) -> str:
        return f"Message from {self.sender.get_display_name()} in {self.thread.subject}"


class Notification(models.Model):
    """
    Custom model to store in-app notifications, replacing django-notifications-hq.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sent_notifications'
    )
    
    unread = models.BooleanField(default=True, db_index=True)
    
    verb = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ('-timestamp',)
        indexes = [
            models.Index(fields=['recipient', 'unread', '-timestamp'], name='notif_user_unread_idx'),
        ]

    def __str__(self):
        return f'{self.recipient.username} - {self.verb}'

    def mark_as_read(self):
        """Helper method to mark as read, used by views."""
        if self.unread:
            self.unread = False
            self.save(update_fields=['unread'])
