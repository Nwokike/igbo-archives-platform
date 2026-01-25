from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from taggit.managers import TaggableManager
from django.core.validators import FileExtensionValidator

from core.validators import (
    validate_image_size,
    validate_video_size,
    validate_document_size,
    validate_audio_size,
)

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class Archive(models.Model):
    ARCHIVE_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('audio', 'Audio'),
    ]
    
    title = models.CharField(max_length=255, help_text="Required: Archive title")
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, help_text="URL-friendly version of title")
    description = models.TextField(help_text="Required: Detailed description (plain text)")
    archive_type = models.CharField(max_length=20, choices=ARCHIVE_TYPES, help_text="Required: Type of archive")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    image = models.ImageField(
        upload_to='archives/',
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ],
        blank=True,
        null=True,
        help_text="For image-type archives (max 5MB)"
    )
    video = models.FileField(
        upload_to='archives/videos/',
        validators=[
            FileExtensionValidator(['mp4', 'webm', 'ogg', 'mov']),
            validate_video_size
        ],
        blank=True,
        null=True,
        help_text="For video-type archives (max 50MB)"
    )
    document = models.FileField(
        upload_to='archives/documents/',
        validators=[
            FileExtensionValidator(['pdf', 'doc', 'docx', 'txt']),
            validate_document_size
        ],
        blank=True,
        null=True,
        help_text="For document-type archives (max 10MB)"
    )
    audio = models.FileField(
        upload_to='archives/audio/',
        validators=[
            FileExtensionValidator(['mp3', 'wav', 'ogg', 'm4a']),
            validate_audio_size
        ],
        blank=True,
        null=True,
        help_text="For audio-type archives (max 10MB)"
    )
    
    featured_image = models.ImageField(
        upload_to='archives/featured/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ],
        help_text="Thumbnail for videos/audio (optional, max 5MB)"
    )
    
    caption = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Required: Caption with copyright/source information"
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Required for images: Alt text for accessibility"
    )
    
    original_author = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Optional: Original photographer/creator (e.g., Northcote Thomas)"
    )
    date_created = models.DateField(
        null=True, 
        blank=True,
        help_text="Optional: Exact date if known"
    )
    circa_date = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Optional: Approximate date (e.g., 'c1910', 'around 1910s')"
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional: Where the photo/artifact was taken/found"
    )
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archives')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True, help_text="Admin approval status")
    
    tags = TaggableManager(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Archives'
        indexes = [
            models.Index(fields=['is_approved', '-created_at'], name='arch_approved_date_idx'),
            models.Index(fields=['archive_type', 'is_approved'], name='arch_type_approved_idx'),
            models.Index(fields=['category', 'is_approved'], name='arch_cat_approved_idx'),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Return the URL for this archive."""
        if self.slug:
            return reverse('archives:detail', args=[self.slug])
        return reverse('archives:detail', args=[self.pk])
    
    def get_primary_file(self):
        """Return the primary file based on archive type"""
        if self.archive_type == 'image' and self.image:
            return self.image
        elif self.archive_type == 'video' and self.video:
            return self.video
        elif self.archive_type == 'document' and self.document:
            return self.document
        elif self.archive_type == 'audio' and self.audio:
            return self.audio
        return None
    
    def has_featured_image(self):
        """Check if archive has a displayable featured image"""
        if self.archive_type == 'image' and self.image:
            return True
        elif self.featured_image:
            return True
        return False
