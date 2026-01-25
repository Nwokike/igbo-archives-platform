from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from taggit.managers import TaggableManager
from django.core.validators import FileExtensionValidator

from core.validators import validate_image_size as validate_file_size

User = get_user_model()


class BookReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    book_title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, help_text="Book author(s)")
    isbn = models.CharField(max_length=20, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    
    review_title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    
    content_json = models.JSONField(
        blank=True,
        null=True,
        help_text="Block-based review content using Editor.js"
    )
    
    legacy_content = models.TextField(blank=True, help_text="Legacy HTML content")
    
    rating = models.IntegerField(choices=RATING_CHOICES)
    
    cover_image = models.ImageField(
        upload_to='book_covers/', 
        blank=True, 
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_file_size
        ],
        help_text="Primary book cover (max 5MB)"
    )
    cover_image_back = models.ImageField(
        upload_to='book_covers/', 
        blank=True, 
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_file_size
        ],
        help_text="Back cover (optional, max 5MB)"
    )
    alternate_cover = models.ImageField(
        upload_to='book_covers/', 
        blank=True, 
        null=True,
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_file_size
        ],
        help_text="Alternate edition cover (optional, max 5MB)"
    )
    
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_reviews')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_published = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    pending_approval = models.BooleanField(default=False, help_text="Review is pending admin approval")
    submitted_at = models.DateTimeField(null=True, blank=True, help_text="When review was submitted for approval")
    
    tags = TaggableManager()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', 'is_approved', '-created_at'], name='book_pub_date_idx'),
            models.Index(fields=['reviewer', 'is_published'], name='book_reviewer_pub_idx'),
            models.Index(fields=['rating', 'is_approved'], name='book_rating_idx'),
        ]
    
    def __str__(self):
        return f"{self.book_title} - Review by {self.reviewer.full_name if hasattr(self.reviewer, 'full_name') else self.reviewer.username}"
    
    def get_absolute_url(self):
        """Return the URL for this book review."""
        return reverse('books:detail', args=[self.slug])
    
    @property
    def content(self):
        """Return content_json if available, otherwise legacy_content"""
        return self.content_json if self.content_json else self.legacy_content
