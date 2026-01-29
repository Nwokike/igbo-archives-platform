from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import push_views
from . import viewsets as api_viewsets

app_name = 'api'

# REST API router
router = DefaultRouter()
router.register('archives', api_viewsets.ArchiveViewSet, basename='archive')
router.register('books', api_viewsets.BookRecommendationViewSet, basename='book')
router.register('categories', api_viewsets.CategoryViewSet, basename='category')

urlpatterns = [
    # REST API v1
    path('v1/', include(router.urls)),
    
    # Existing endpoints
    path('push-subscribe/', push_views.push_subscribe, name='push_subscribe'),
    path('push-unsubscribe/', push_views.push_unsubscribe, name='push_unsubscribe'),
    path('archive-media-browser/', views.archive_media_browser, name='archive_media_browser'),
    path('upload-image/', views.upload_image, name='upload_image'),
    path('upload-media/', views.upload_media, name='upload_media'),
    path('notification-list/', views.notification_list_api, name='notification_list'),
]

