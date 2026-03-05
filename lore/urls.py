from django.urls import path
from . import views

app_name = 'lore'

urlpatterns = [
    path('', views.lore_list, name='list'),
    path('create/', views.lore_create, name='create'),
    path('<slug:slug>/', views.lore_detail, name='detail'),
    path('<slug:slug>/edit/', views.lore_edit, name='edit'),
    path('<slug:slug>/delete/', views.lore_delete, name='delete'),
]
