from django.contrib import admin
from .models import BookReview

@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ['book_title', 'author', 'reviewer', 'rating', 'is_published', 'created_at']
    list_filter = ['rating', 'is_published', 'created_at']
    search_fields = ['book_title', 'author', 'review_title']
    prepopulated_fields = {'slug': ('review_title',)}
