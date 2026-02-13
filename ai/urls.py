"""AI app URL configuration."""
from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    path('', views.ai_home, name='home'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
    path('chat/', views.chat_session, name='new_chat'),
    path('chat/<int:session_id>/', views.chat_session, name='chat_session'),
    path('chat/send/', views.chat_send, name='chat_send'),
    path('chat/history/', views.chat_history, name='chat_history'),
    path('chat/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('analyze/', views.analyze_archive, name='analyze_archive'),
    path('tts/', views.generate_tts, name='generate_tts'),
    path('tts/serve/<uuid:audio_id>/', views.serve_tts_audio, name='serve_tts'),
    path('generate-insight/', views.generate_insight_content, name='generate_insight'),
]
