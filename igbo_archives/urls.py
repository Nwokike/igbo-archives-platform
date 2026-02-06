from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticPagesSitemap, ArchiveSitemap, InsightSitemap, BookSitemap, UserProfileSitemap
from core.views import chrome_devtools_association

sitemaps = {
    'static': StaticPagesSitemap,
    'archives': ArchiveSitemap,
    'insights': InsightSitemap,
    'books': BookSitemap,
    'users': UserProfileSitemap,
}

urlpatterns = [
    path('igbo-secure-admin/', admin.site.urls),
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

# Error handlers
handler400 = 'core.views.bad_request_handler'
handler403 = 'core.views.permission_denied_handler'
handler404 = 'core.views.page_not_found_handler'
handler500 = 'core.views.server_error_handler'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('.well-known/appspecific/com.chrome.devtools.json', chrome_devtools_association),
]
