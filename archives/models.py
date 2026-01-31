from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.validators import FileExtensionValidator

from core.validators import (
    validate_image_size,
    validate_video_size,
    validate_document_size,
    validate_audio_size,
)

User = get_user_model()


class Category(models.Model):
    CATEGORY_TYPES = [
        ('archive', 'Archive'),
        ('insight', 'Insight'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=20, 
        choices=CATEGORY_TYPES, 
        default='archive',
        help_text="Is this for Archives or Insights?"
    )
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}"


class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Bio or description of the author")
    image = models.ImageField(upload_to='authors/', blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('archives:author_detail', args=[self.slug])


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
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'type': 'archive'}
    )
    
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
        help_text="Caption for the archive"
    )
    copyright_holder = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Copyright holder (displays small after caption)"
    )
    original_url = models.URLField(
        blank=True,
        default='',
        help_text="Original URL from source museum/collection"
    )
    original_identity_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Museum catalog/identity number"
    )
    item_count = models.PositiveSmallIntegerField(
        default=1,
        help_text="Number of items in this archive (1-5)"
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
        help_text="Optional: Original photographer/creator (e.g., Northcote Thomas). Will auto-link to Author profile if match exists."
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archives',
        help_text="Link to a full author profile"
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
    is_approved = models.BooleanField(default=False, help_text="Admin approval status")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Archives'
        indexes = [
            models.Index(fields=['is_approved', '-created_at'], name='arch_approved_date_idx'),
            models.Index(fields=['archive_type', 'is_approved'], name='arch_type_approved_idx'),
            models.Index(fields=['category', 'is_approved'], name='arch_cat_approved_idx'),
            models.Index(fields=['slug'], name='arch_slug_idx'),
            models.Index(fields=['circa_date'], name='arch_circa_date_idx'),
            models.Index(fields=['location'], name='arch_location_idx'),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if missing
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            
            base_slug = slugify(self.title)[:200]
            if not base_slug:
                base_slug = "archive"
            
            slug = base_slug
            counter = 1
            
            # Check for slug collision
            while Archive.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                if counter > 100:
                    slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                    break
            
            self.slug = slug

        # Auto-link logic:
        if self.original_author and not self.author:
            match = Author.objects.filter(name__iexact=self.original_author.strip()).first()
            if match:
                self.author = match
        
        if self.author and not self.original_author:
            self.original_author = self.author.name
            
        super().save(*args, **kwargs)
    
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


class ArchiveItem(models.Model):
    """
    Individual items within a multi-item archive.
    Allows archives to have 1-5 items (e.g., front/side views, image+audio).
    """
    ITEM_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('audio', 'Audio'),
    ]
    
    archive = models.ForeignKey(
        Archive,
        on_delete=models.CASCADE,
        related_name='items'
    )
    item_number = models.PositiveSmallIntegerField(
        help_text="Order of this item (1-5)"
    )
    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPES,
        help_text="Type of this item"
    )
    
    # File fields - only one should be filled based on item_type
    image = models.ImageField(
        upload_to='archives/items/',
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ],
        blank=True,
        null=True
    )
    video = models.FileField(
        upload_to='archives/items/videos/',
        validators=[
            FileExtensionValidator(['mp4', 'webm', 'ogg', 'mov']),
            validate_video_size
        ],
        blank=True,
        null=True
    )
    audio = models.FileField(
        upload_to='archives/items/audio/',
        validators=[
            FileExtensionValidator(['mp3', 'wav', 'ogg', 'm4a']),
            validate_audio_size
        ],
        blank=True,
        null=True
    )
    document = models.FileField(
        upload_to='archives/items/documents/',
        validators=[
            FileExtensionValidator(['pdf', 'doc', 'docx', 'txt']),
            validate_document_size
        ],
        blank=True,
        null=True
    )
    
    # Item-specific metadata
    caption = models.CharField(max_length=500, blank=True, help_text="Caption for this item")
    description = models.TextField(blank=True, help_text="Description for this item")
    alt_text = models.CharField(max_length=255, blank=True, help_text="Alt text for accessibility")
    
    class Meta:
        ordering = ['item_number']
        constraints = [
            models.UniqueConstraint(
                fields=['archive', 'item_number'],
                name='unique_archive_item_number'
            )
        ]
        verbose_name = 'Archive Item'
        verbose_name_plural = 'Archive Items'
    
    def __str__(self):
        return f"{self.archive.title} - Item {self.item_number}"
    
    def get_file(self):
        """Return the file based on item type."""
        if self.item_type == 'image' and self.image:
            return self.image
        elif self.item_type == 'video' and self.video:
            return self.video
        elif self.item_type == 'audio' and self.audio:
            return self.audio
        elif self.item_type == 'document' and self.document:
            return self.document
        return None