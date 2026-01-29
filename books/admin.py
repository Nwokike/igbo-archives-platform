from django.contrib import admin
from .models import BookRecommendation, UserBookRating


@admin.register(BookRecommendation)
class BookRecommendationAdmin(admin.ModelAdmin):
    list_display = ['book_title', 'author', 'added_by', 'is_published', 'created_at']
    list_filter = ['is_published', 'is_approved', 'created_at']
    search_fields = ['book_title', 'author', 'title']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(UserBookRating)
class UserBookRatingAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['book__book_title', 'user__email']
