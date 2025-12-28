"""
AI views for Igbo Archives.
World-class cultural AI assistant - no visible provider branding.
"""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.core.cache import cache
from .models import ChatSession, ChatMessage, ArchiveAnalysis
from .services.chat_service import chat_service
from .services.vision_service import vision_service
from .services.tts_service import tts_service


def ai_home(request):
    """AI landing page."""
    sessions = []
    if request.user.is_authenticated:
        sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-updated_at')[:10]
    
    context = {
        'sessions': sessions,
        'chat_available': chat_service.is_available,
        'vision_available': vision_service.is_available,
    }
    return render(request, 'ai/home.html', context)


@login_required
def chat_session(request, session_id=None):
    """View or continue a chat session."""
    if session_id:
        session = get_object_or_404(
            ChatSession,
            id=session_id,
            user=request.user
        )
    else:
        session = ChatSession.objects.create(
            user=request.user,
            title='New Conversation'
        )
        return redirect('ai:chat_session', session_id=session.id)
    
    messages = session.messages.all()[:50]
    
    context = {
        'session': session,
        'messages': messages,
        'chat_available': chat_service.is_available,
    }
    return render(request, 'ai/chat.html', context)


@login_required
@require_POST
def chat_send(request):
    """Send a message to the AI assistant."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    message_content = data.get('message', '').strip()
    session_id = data.get('session_id')
    mode = data.get('mode', 'fast')  # 'fast' or 'advanced'
    
    if not message_content:
        return JsonResponse({'error': 'Message is required'}, status=400)
    
    if len(message_content) > 3000:
        return JsonResponse({'error': 'Message too long (max 3000 characters)'}, status=400)
    
    # Rate limiting
    rate_key = f'ai_chat_{request.user.id}'
    chat_count = cache.get(rate_key, 0)
    if chat_count >= 50:  # 50 messages per hour
        return JsonResponse({'error': 'You\'ve reached your message limit. Please wait a while.'}, status=429)
    
    # Get or create session
    if session_id:
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    else:
        session = ChatSession.objects.create(
            user=request.user,
            title='New Conversation'
        )
    
    # Save user message
    ChatMessage.objects.create(
        session=session,
        role='user',
        content=message_content
    )
    
    # Build message history
    history = session.messages.order_by('-created_at')[:10]
    messages = [{'role': m.role, 'content': m.content} for m in reversed(history)]
    
    # Get AI response
    result = chat_service.chat(messages, use_web_search=True)
    
    # Save AI response
    ai_message = ChatMessage.objects.create(
        session=session,
        role='assistant',
        content=result['content'],
        model_used=result.get('model_type', '')
    )
    
    # Update session title if first exchange
    if session.messages.count() == 2:
        title = chat_service.generate_title(message_content)
        session.title = title
        session.save()
    
    # Update rate limit
    cache.set(rate_key, chat_count + 1, 3600)
    
    return JsonResponse({
        'success': result['success'],
        'message': result['content'],
        'session_id': session.id,
        'session_title': session.title,
        'message_id': ai_message.id,
    })


@login_required
@require_POST
def analyze_archive(request):
    """Analyze an archive image."""
    from archives.models import Archive
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    archive_id = data.get('archive_id')
    analysis_type = data.get('type', 'describe')
    
    if not archive_id:
        return JsonResponse({'error': 'Archive ID required'}, status=400)
    
    valid_types = ['describe', 'historical', 'cultural', 'translation', 'artifact']
    if analysis_type not in valid_types:
        analysis_type = 'describe'
    
    # Rate limiting
    rate_key = f'ai_vision_{request.user.id}'
    count = cache.get(rate_key, 0)
    if count >= 20:  # 20 analyses per hour
        return JsonResponse({'error': 'Analysis limit reached. Please wait.'}, status=429)
    
    archive = get_object_or_404(Archive, id=archive_id, is_approved=True)
    
    # Check cache
    existing = ArchiveAnalysis.objects.filter(
        archive=archive,
        analysis_type=analysis_type
    ).first()
    
    if existing:
        return JsonResponse({
            'success': True,
            'content': existing.content,
            'cached': True,
        })
    
    # Get image path
    if archive.image:
        image_path = archive.image.path
    elif archive.featured_image:
        image_path = archive.featured_image.path
    else:
        return JsonResponse({'error': 'No image to analyze'}, status=400)
    
    # Analyze
    result = vision_service.analyze(image_path, analysis_type)
    
    if result['success']:
        ArchiveAnalysis.objects.create(
            archive=archive,
            user=request.user,
            analysis_type=analysis_type,
            content=result['content'],
            model_used='vision'
        )
        cache.set(rate_key, count + 1, 3600)
    
    return JsonResponse({
        'success': result['success'],
        'content': result['content'],
        'cached': False,
    })


@login_required
@require_POST
def generate_tts(request):
    """Generate text-to-speech audio."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    text = data.get('text', '').strip()
    language = data.get('language', 'en')
    
    if not text:
        return JsonResponse({'error': 'Text is required'}, status=400)
    
    if len(text) > 5000:
        return JsonResponse({'error': 'Text too long'}, status=400)
    
    # Rate limiting
    rate_key = f'ai_tts_{request.user.id}'
    count = cache.get(rate_key, 0)
    if count >= 30:
        return JsonResponse({'error': 'TTS limit reached'}, status=429)
    
    result = tts_service.generate_audio(text, language)
    
    if result['success']:
        cache.set(rate_key, count + 1, 3600)
    
    return JsonResponse(result)


@login_required
@require_POST
def transcribe_audio(request):
    """Transcribe audio to text."""
    if 'audio' not in request.FILES:
        return JsonResponse({'error': 'No audio file'}, status=400)
    
    audio_file = request.FILES['audio']
    
    # Size limit (10MB)
    if audio_file.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'File too large'}, status=400)
    
    # Rate limiting
    rate_key = f'ai_stt_{request.user.id}'
    count = cache.get(rate_key, 0)
    if count >= 20:
        return JsonResponse({'error': 'Transcription limit reached'}, status=429)
    
    # Save temp file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
        for chunk in audio_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name
    
    try:
        result = chat_service.transcribe(tmp_path)
        
        if result['success']:
            cache.set(rate_key, count + 1, 3600)
        
        return JsonResponse({
            'success': result['success'],
            'text': result.get('text', ''),
            'error': result.get('error', '')
        })
    finally:
        os.unlink(tmp_path)


@login_required
@require_GET
def chat_history(request):
    """Get user's chat history."""
    sessions = ChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-updated_at')[:20]
    
    data = [{
        'id': s.id,
        'title': s.title,
        'updated_at': s.updated_at.isoformat(),
        'message_count': s.messages.count(),
    } for s in sessions]
    
    return JsonResponse({'sessions': data})


@login_required
@require_POST
def delete_session(request, session_id):
    """Delete a chat session."""
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.is_active = False
    session.save()
    return JsonResponse({'success': True})


def coming_soon(request):
    """Fallback - redirect if AI is available."""
    if chat_service.is_available:
        return redirect('ai:home')
    return render(request, 'ai/coming_soon.html')
