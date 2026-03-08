from django.urls import path
from . import views

app_name = 'archives'

urlpatterns = [
    path('', views.archive_list, name='list'),
    path('create/', views.archive_create, name='create'),
    path('author/<slug:slug>/', views.author_detail, name='author_detail'),
    path('suggestions/', views.metadata_suggestions, name='suggestions'),
    path('author-suggestions/', views.author_suggestions, name='author_suggestions'),
    
    # Numeric pk URLs first (so they match before slug patterns)
    path('<int:pk>/', views.archive_detail, name='detail_pk'),
    path('<int:pk>/edit/', views.archive_edit, name='edit_pk'),
    path('<int:pk>/delete/', views.archive_delete, name='delete_pk'),
    
    # Slug URLs second (CATCH-ALLS)
    path('<slug:slug>/', views.archive_detail, name='detail'),
    path('<slug:slug>/edit/', views.archive_edit, name='edit'),
    path('<slug:slug>/delete/', views.archive_delete, name='delete'),
    
    # Community Notes
    path('<slug:slug>/add-note/', views.add_archive_note, name='add_note'),
    path('note/<int:pk>/edit/', views.edit_archive_note, name='edit_note'),
    path('note/<int:note_id>/suggest/', views.suggest_note_edit, name='suggest_note_edit'),
    
    # Author Enhancements
    path('author/<slug:slug>/describe/', views.submit_author_description, name='submit_author_description'),
]
