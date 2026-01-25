from django.urls import path
from . import views
from . import edit_suggestion_views

app_name = 'insights'

urlpatterns = [
    path('', views.insight_list, name='list'),
    path('create/', views.insight_create, name='create'),
    path('<slug:slug>/', views.insight_detail, name='detail'),
    path('<slug:slug>/edit/', views.insight_edit, name='edit'),
    path('<slug:slug>/delete/', views.insight_delete, name='delete'),
    path('<slug:slug>/suggest-edit/', views.suggest_edit, name='suggest_edit'),
    path('suggestions/<int:pk>/approve/', edit_suggestion_views.approve_edit_suggestion, name='approve_suggestion'),
    path('suggestions/<int:pk>/reject/', edit_suggestion_views.reject_edit_suggestion, name='reject_suggestion'),
]
