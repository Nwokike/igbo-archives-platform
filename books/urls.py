from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list, name='list'),
    path('create/', views.book_create, name='create'),
    path('<slug:slug>/', views.book_detail, name='detail'),
    path('<slug:slug>/edit/', views.book_edit, name='edit'),
    path('<slug:slug>/delete/', views.book_delete, name='delete'),
    path('<slug:slug>/rate/', views.book_rate, name='rate'),
]