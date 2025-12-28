from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticPagesSitemap, ArchiveSitemap, InsightSitemap, BookSitemap, UserProfileSitemap

sitemaps = {
    'static': StaticPagesSitemap,
    'archives': ArchiveSitemap,
    'insights': InsightSitemap,
    'books': BookSitemap,
    'users': UserProfileSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pwa.urls')),
    path('', include('core.urls')),
    path('accounts/', include('allauth.urls')),
    path('profile/', include('users.urls')),
    path('api/', include('api.urls')),
    path('archives/', include('archives.urls')),
    path('insights/', include('insights.urls')),
    path('books/', include('books.urls')),
    path('ai/', include('ai.urls')),
    path('comments/', include('django_comments.urls')),
    path('webpush/', include(('webpush.urls', 'webpush'), namespace='webpush')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
