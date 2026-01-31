from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('terms/', views.terms_of_service, name='terms'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('copyright/', views.copyright_policy, name='copyright'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('donate/', views.donate, name='donate'),
    path('offline/', views.offline, name='offline'),
    path('health/', views.health_check, name='health'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]
