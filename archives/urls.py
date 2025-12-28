from django.urls import path
from . import views

app_name = 'archives'

urlpatterns = [
    path('', views.archive_list, name='list'),
    path('create/', views.archive_create, name='create'),
    path('<int:pk>/', views.archive_detail, name='detail'),
    path('<int:pk>/edit/', views.archive_edit, name='edit'),
]
