from django.db import models
from django.contrib.auth import get_user_model
from taggit.managers import TaggableManager
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

User = get_user_model()

def validate_image_size(file):
    """Validate image file size - Max 5MB"""
    file_size = file.size
    max_mb = 5
    min_mb = 2
    if file_size > max_mb * 1024 * 1024:
        raise ValidationError(f'Maximum file size is {max_mb}MB')
    if file_size < min_mb * 1024 * 1024:
        raise ValidationError(f'Minimum file size is {min_mb}MB for quality. Please use higher quality images.')

def validate_video_size(file):
    """Validate video file size - max 50MB"""
    file_size = file.size
    limit_mb = 50
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f'Maximum video file size is {limit_mb}MB')

def validate_document_size(file):
    """Validate document file size - Max 5MB"""
    file_size = file.size
    max_mb = 5
    min_mb = 2
    if file_size > max_mb * 1024 * 1024:
        raise ValidationError(f'Maximum document file size is {max_mb}MB')
    if file_size < min_mb * 1024 * 1024:
        raise ValidationError(f'Minimum document file size is {min_mb}MB')

def validate_audio_size(file):
    """Validate audio file size - Max 5MB"""
    file_size = file.size
    max_mb = 5
    min_mb = 2
    if file_size > max_mb * 1024 * 1024:
        raise ValidationError(f'Maximum audio file size is {max_mb}MB')
    if file_size < min_mb * 1024 * 1024:
        raise ValidationError(f'Minimum audio file size is {min_mb}MB for quality')

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
    
    # Basic Information
    title = models.CharField(max_length=255, help_text="Required: Archive title")
    description = models.TextField(help_text="Required: Detailed description (plain text)")
    archive_type = models.CharField(max_length=20, choices=ARCHIVE_TYPES, help_text="Required: Type of archive")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Media Files
    image = models.ImageField(
        upload_to='archives/',
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ],
        blank=True,
        null=True,
        help_text="For image-type archives"
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
        help_text="For document-type archives (max 5MB)"
    )
    audio = models.FileField(
        upload_to='archives/audio/',
        validators=[
            FileExtensionValidator(['mp3', 'wav', 'ogg', 'm4a']),
            validate_audio_size
        ],
        blank=True,
        null=True,
        help_text="For audio-type archives (max 5MB)"
    )
    
    # Featured image for non-image archives (e.g., video thumbnail)
    featured_image = models.ImageField(
        upload_to='archives/featured/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ],
        help_text="Thumbnail for videos/audio (optional)"
    )
    
    # Metadata
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
    
    # Historical Information
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
    
    # System fields
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archives')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True, help_text="Admin approval status")
    
    tags = TaggableManager(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Archives'
    
    def __str__(self):
        return self.title
    
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
