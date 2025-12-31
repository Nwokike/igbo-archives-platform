from django.db import models
from django.contrib.auth import get_user_model
from taggit.managers import TaggableManager
from django.core.validators import FileExtensionValidator

from core.validators import validate_image_size as validate_file_size

User = get_user_model()


class InsightPost(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    
    content_json = models.JSONField(
        blank=True,
        null=True,
        help_text="Block-based content using Editor.js"
    )
    
    legacy_content = models.TextField(blank=True, help_text="Legacy HTML content")
    
    excerpt = models.TextField(max_length=500, blank=True)
    featured_image = models.ImageField(
        upload_to='insights/', 
        blank=True, 
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_file_size
        ]
    )
    alt_text = models.CharField(max_length=255, blank=True)
    
    image_caption = models.CharField(max_length=500, blank=True, help_text="Image caption with copyright/source info")
    image_description = models.TextField(blank=True, help_text="Detailed image description")
    copyright_info = models.CharField(max_length=500, blank=True, help_text="Copyright or image source")
    
    submit_as_archive = models.BooleanField(default=True, help_text="Submit uploaded images as archives")
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insights')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_published = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    pending_approval = models.BooleanField(default=False, help_text="Post is pending admin approval")
    submitted_at = models.DateTimeField(null=True, blank=True, help_text="When post was submitted for approval")
    
    posted_to_social = models.BooleanField(default=False)
    tags = TaggableManager()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', 'is_approved', '-created_at'], name='insight_pub_date_idx'),
            models.Index(fields=['author', 'is_published'], name='insight_author_pub_idx'),
            models.Index(fields=['pending_approval'], name='insight_pending_idx'),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def content(self):
        """Return content_json if available, otherwise legacy_content"""
        return self.content_json if self.content_json else self.legacy_content


class EditSuggestion(models.Model):
    post = models.ForeignKey(InsightPost, on_delete=models.CASCADE, related_name='suggestions')
    suggested_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    suggestion_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, help_text="Admin reason for rejection")
    
    class Meta:
        indexes = [
            models.Index(fields=['post', 'is_approved', 'is_rejected'], name='suggestion_status_idx'),
        ]
    
    def __str__(self):
        return f"Suggestion for {self.post.title}"


class UploadedImage(models.Model):
    """Track images uploaded within insights for potential archive submission"""
    insight = models.ForeignKey(InsightPost, on_delete=models.CASCADE, related_name='uploaded_images')
    image = models.ImageField(
        upload_to='insights/uploads/',
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_file_size
        ]
    )
    caption = models.CharField(max_length=500, help_text="Required: Caption with copyright/source")
    description = models.TextField(help_text="Required: Image description")
    alt_text = models.CharField(max_length=255, help_text="Alt text for accessibility")
    
    archive_title = models.CharField(max_length=255, blank=True)
    archive_type = models.CharField(max_length=20, default='image')
    archive_category = models.ForeignKey('archives.Category', on_delete=models.SET_NULL, null=True, blank=True)
    original_author = models.CharField(max_length=255, blank=True, help_text="e.g., Northcote Thomas")
    date_created_field = models.DateField(null=True, blank=True)
    circa_date = models.CharField(max_length=100, blank=True, help_text="e.g., c1910, around 1910s")
    
    approved_as_archive = models.BooleanField(default=False)
    archive_reference = models.ForeignKey('archives.Archive', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.insight.title}"
