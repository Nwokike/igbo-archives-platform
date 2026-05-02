from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from core.validators import validate_image_size, validate_video_size, validate_audio_size

User = get_user_model()

class LorePost(models.Model):
    """
    Replaces the old Insights app, intended for folktales, proverbs, parables, and cultural history.
    """
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    # Text Content
    content_json = models.JSONField(
        blank=True,
        null=True,
        help_text="Block-based content using Editor.js"
    )
    legacy_content = models.TextField(blank=True, help_text="Legacy HTML content")
    excerpt = models.TextField(max_length=500, blank=True)
    
    # Metadata
    category = models.ForeignKey(
        'archives.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'type': 'lore'},
        related_name='lore_posts',
        help_text="Select a category, e.g., Folktale, Proverb"
    )
    
    # Storage-efficient URL streaming fields (Priority)
    image_url = models.URLField(blank=True, help_text="External URL for image streaming")
    video_url = models.URLField(blank=True, help_text="External URL for video streaming or YouTube embed")
    audio_url = models.URLField(blank=True, help_text="External URL for audio streaming")

    # Native File fields (Secondary/Fallback)
    featured_image = models.ImageField(
        upload_to='lore/images/', 
        blank=True, 
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ]
    )
    featured_video = models.FileField(
        upload_to='lore/videos/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['mp4', 'webm', 'ogg', 'mov']),
            validate_video_size
        ]
    )
    featured_audio = models.FileField(
        upload_to='lore/audio/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['mp3', 'wav', 'ogg', 'm4a']),
            validate_audio_size
        ]
    )
    
    alt_text = models.CharField(max_length=255, blank=True)
    
    # Users tracking
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lore_posts')
    original_author = models.CharField(max_length=255, blank=True, help_text="For historical authors")
    
    # Moderation
    is_published = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    pending_approval = models.BooleanField(default=False, help_text="Post is pending admin approval")
    is_rejected = models.BooleanField(default=False, help_text="Set to true if admin rejects the post")
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True, help_text="When submitted for approval")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', 'is_approved', '-created_at'], name='lore_pub_date_idx'),
        ]
    
    def __str__(self):
        return self.title
        
    def save(self, *args, **kwargs):
        if not self.slug:
            from core.editorjs_helpers import generate_unique_slug
            self.slug = generate_unique_slug(self.title, LorePost)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('lore:detail', args=[self.slug])
    
    @property
    def content(self):
        """Return content_json if it has blocks, otherwise legacy_content"""
        if self.content_json and (isinstance(self.content_json, dict) and self.content_json.get('blocks')):
            return self.content_json
        return self.legacy_content
