"""
Core app models for email tracking and digest system.

These models support:
- EmailLog: Tracks daily email quota (300/day Brevo limit)
- DigestQueue: Stores content for weekly digest emails
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class EmailLog(models.Model):
    """
    Tracks sent emails for daily quota enforcement.
    Brevo limit: 300 emails/day
    """
    EMAIL_TYPE_CHOICES = [
        ('instant', 'Instant (approval, rejection, direct action)'),
        ('admin', 'Admin notification'),
        ('digest', 'Weekly digest'),
    ]
    
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPE_CHOICES, default='instant')
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['sent_at'], name='email_sent_date_idx'),
            models.Index(fields=['email_type', 'sent_at'], name='email_type_date_idx'),
        ]
    
    def __str__(self):
        return f"{self.email_type}: {self.recipient_email} @ {self.sent_at.date()}"
    
    @classmethod
    def get_daily_count(cls, date=None):
        """Get number of emails sent on a specific date (default today)."""
        if date is None:
            date = timezone.now().date()
        return cls.objects.filter(
            sent_at__date=date,
            success=True
        ).count()
    
    @classmethod
    def quota_remaining(cls, daily_limit=300):
        """Get remaining email quota for today."""
        sent_today = cls.get_daily_count()
        return max(0, daily_limit - sent_today)
    
    @classmethod
    def can_send(cls, count=1, daily_limit=300):
        """Check if we can send `count` emails without exceeding quota."""
        return cls.quota_remaining(daily_limit) >= count


class DigestQueue(models.Model):
    """
    Queue for weekly digest content.
    Instead of sending instant emails for new posts, queue them
    for the weekly digest. Only processed once per week.
    """
    CONTENT_TYPE_CHOICES = [
        ('archive', 'New Archive'),
        ('insight', 'New Insight'),
        ('book', 'New Book Recommendation'),
    ]
    
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_id = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    author_name = models.CharField(max_length=200)
    url = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['processed', 'created_at'], name='digest_queue_idx'),
        ]
    
    def __str__(self):
        return f"{self.content_type}: {self.title}"
    
    @classmethod
    def get_pending_content(cls):
        """Get all unprocessed content for the digest."""
        return cls.objects.filter(processed=False).order_by('created_at')
    
    @classmethod
    def mark_processed(cls, ids):
        """Mark items as processed."""
        cls.objects.filter(id__in=ids).update(
            processed=True,
            processed_at=timezone.now()
        )
