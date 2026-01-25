from django.urls import path
from . import views

app_name = 'archives'

urlpatterns = [
    path('', views.archive_list, name='list'),
    path('create/', views.archive_create, name='create'),
    path('<slug:slug>/', views.archive_detail, name='detail'),
    path('<slug:slug>/edit/', views.archive_edit, name='edit'),
    path('<slug:slug>/delete/', views.archive_delete, name='delete'),
    # Backward compatibility - support pk URLs
    path('<int:pk>/', views.archive_detail, name='detail_pk'),
    path('<int:pk>/edit/', views.archive_edit, name='edit_pk'),
    path('<int:pk>/delete/', views.archive_delete, name='delete_pk'),
]
