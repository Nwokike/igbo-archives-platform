"""
Shared validators for file uploads across all apps.
"""
from django.core.exceptions import ValidationError


def validate_file_size(file, max_mb):
    """Validate file size against maximum MB limit."""
    if file.size > max_mb * 1024 * 1024:
        raise ValidationError(f'Maximum file size is {max_mb}MB')


def validate_image_size(file):
    """Validate image file size - max 5MB."""
    validate_file_size(file, 5)


def validate_video_size(file):
    """Validate video file size - max 50MB."""
    validate_file_size(file, 50)


def validate_document_size(file):
    """Validate document file size - max 10MB."""
    validate_file_size(file, 10)


def validate_audio_size(file):
    """Validate audio file size - max 10MB."""
    validate_file_size(file, 10)


ALLOWED_ARCHIVE_SORTS = {
    'recently-added': '-created_at',
    'newest': '-sort_year',
    'oldest': 'sort_year',
    'a-z': 'title',
    'z-a': '-title',
}

ALLOWED_INSIGHT_SORTS = {
    'recently-added': '-created_at',
    'newest': '-created_at',
    'oldest': 'created_at',
}

ALLOWED_BOOK_SORTS = {
    'recently-added': '-created_at',
    'newest': '-publication_year',
    'oldest': 'publication_year',
    'top-rated': '-rating',
}


def get_safe_sort(sort_param, allowed_sorts, default='-created_at'):
    """Get a safe sort parameter from whitelist."""
    return allowed_sorts.get(sort_param, default)
