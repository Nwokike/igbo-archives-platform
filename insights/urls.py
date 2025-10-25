from django.urls import path
from . import views

app_name = 'insights'

urlpatterns = [
    path('', views.insight_list, name='list'),
]
