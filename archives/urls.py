from django.urls import path
from . import views

app_name = 'archives'

urlpatterns = [
    path('', views.archive_list, name='list'),
    path('create/', views.archive_create, name='create'),
    path('author/<slug:slug>/', views.author_detail, name='author_detail'),
    path('suggestions/', views.metadata_suggestions, name='suggestions'),
    # Numeric pk URLs first (so they match before slug patterns)
    path('<int:pk>/', views.archive_detail, name='detail_pk'),
    path('<int:pk>/edit/', views.archive_edit, name='edit_pk'),
    path('<int:pk>/delete/', views.archive_delete, name='delete_pk'),
    # Slug URLs second
    path('<slug:slug>/', views.archive_detail, name='detail'),
    path('<slug:slug>/edit/', views.archive_edit, name='edit'),
    path('<slug:slug>/delete/', views.archive_delete, name='delete'),
]
