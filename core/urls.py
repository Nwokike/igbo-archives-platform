from django.urls import path
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
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
]


@require_GET
def robots_txt(request):
    """Serve robots.txt"""
    content = render_to_string('robots.txt', request=request)
    return HttpResponse(content, content_type='text/plain')


urlpatterns += [
    path('robots.txt', robots_txt, name='robots_txt'),
]
