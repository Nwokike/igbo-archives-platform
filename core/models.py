"""
Core app models.

This file is intentionally empty. The core app contains shared utilities,
context processors, and views but does not define any database models.
All content models are defined in their respective apps:
- archives.models: Archive, Category
- insights.models: InsightPost, EditSuggestion, UploadedImage
- books.models: BookReview
- users.models: CustomUser, Notification, SavedArchive
"""
from django.db import models  # noqa: F401
