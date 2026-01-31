from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator

from core.validators import validate_image_size as validate_file_size

User = get_user_model()


class BookRecommendation(models.Model):
    """
    Book recommendations - not reviews.
    Ratings and reviews are done by users via UserBookRating model.
    """
    
    book_title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, help_text="Book author(s)")
    isbn = models.CharField(max_length=20, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    
    # Recommendation details (not review)
    title = models.CharField(max_length=255, help_text="Recommendation title")
    slug = models.SlugField(unique=True)
    
    content_json = models.JSONField(
        blank=True,
        null=True,
        help_text="Block-based content using Editor.js"
    )
    
    legacy_content = models.TextField(blank=True, help_text="Legacy HTML content")
    
    # No reviewer rating - users rate instead
    
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
    
    # Who added the recommendation
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_recommendations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_published = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    pending_approval = models.BooleanField(default=False, help_text="Pending admin approval")
    submitted_at = models.DateTimeField(null=True, blank=True, help_text="When submitted for approval")
    
    # tags field REMOVED
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', 'is_approved', '-created_at'], name='book_pub_date_idx'),
            models.Index(fields=['added_by', 'is_published'], name='book_user_pub_idx'),
        ]
    
    def __str__(self):
        return f"{self.book_title} by {self.author}"
    
    def get_absolute_url(self):
        """Return the URL for this book recommendation."""
        return reverse('books:detail', args=[self.slug])
    
    @property
    def content(self):
        """Return content_json if available, otherwise legacy_content"""
        return self.content_json if self.content_json else self.legacy_content
    
    @property
    def average_rating(self):
        """Calculate average rating from user ratings using database aggregation."""
        from django.db.models import Avg
        result = self.ratings.aggregate(avg=Avg('rating'))
        return result['avg']
    
    @property
    def rating_count(self):
        """Count of user ratings."""
        return self.ratings.count()


class UserBookRating(models.Model):
    """
    User ratings and reviews for recommended books.
    This allows users to rate books, not the recommender.
    """
    book = models.ForeignKey(
        BookRecommendation,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='book_ratings'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    review_text = models.TextField(
        blank=True,
        help_text="Optional review comment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['book', 'user'],
                name='unique_user_book_rating'
            )
        ]
        ordering = ['-created_at']
        verbose_name = 'User Book Rating'
        verbose_name_plural = 'User Book Ratings'
    
    def __str__(self):
        return f"{self.user} rated {self.book.book_title}: {self.rating}/5"