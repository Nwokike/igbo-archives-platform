from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from archives.models import Archive
from insights.models import InsightPost
from books.models import BookReview
from django.contrib.auth import get_user_model

User = get_user_model()


class StaticPagesSitemap(Sitemap):
    """Sitemap for static/informational pages"""
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return [
            'core:home',
            'core:about',
            'core:privacy',
            'core:terms',
            'core:copyright',
            'core:contact',
            'core:donate',
        ]

    def location(self, item):
        return reverse(item)


class ArchiveSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    
    def items(self):
        return Archive.objects.filter(is_approved=True).only('id', 'updated_at').iterator(chunk_size=500)
    
    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else obj.created_at
    
    def location(self, obj):
        return reverse('archives:detail', args=[obj.id])


class InsightSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9
    
    def items(self):
        return InsightPost.objects.filter(
            is_published=True, is_approved=True
        ).only('id', 'slug', 'updated_at').iterator(chunk_size=500)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('insights:detail', args=[obj.slug])


class BookSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7
    
    def items(self):
        return BookReview.objects.filter(
            is_published=True, is_approved=True
        ).only('id', 'slug', 'updated_at').iterator(chunk_size=500)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('books:detail', args=[obj.slug])


class UserProfileSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    
    def items(self):
        return User.objects.filter(is_active=True).only('id', 'username').iterator(chunk_size=500)
    
    def location(self, obj):
        return reverse('users:profile', args=[obj.username])
