"""
AI views for Igbo Archives.
World-class cultural AI assistant - no visible provider branding.
"""
import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.core.cache import cache
from django.db.models import Count
from .services.chat_service import chat_service
from .services.vision_service import vision_service
from .services.tts_service import tts_service

logger = logging.getLogger(__name__)


def ai_home(request):
    """AI landing page."""
    context = {
        'chat_available': chat_service.is_available,
        'vision_available': vision_service.is_available,
    }
    return render(request, 'ai/home.html', context)


@login_required
def chat_view(request):
    """Stateless chat view."""
    context = {
        'messages': [],
        'chat_available': chat_service.is_available,
    }
    return render(request, 'ai/chat.html', context)


@login_required
@require_POST
def chat_send(request):
    """Send a message to the AI assistant (Stateless)."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    message_content = data.get('message', '').strip()
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
    
    # Stateless: We don't save messages to the database
    
    # Get history from client if available for context
    messages = data.get('history', [])
    if not isinstance(messages, list):
        messages = []
    
    # Filter for safety (ensure only role and content are passed)
    sanitized_history = []
    for msg in messages[-10:]: # Keep only last 10 for context window efficiency
        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
            sanitized_history.append({
                'role': msg['role'],
                'content': msg['content']
            })
    
    # Append current message
    sanitized_history.append({'role': 'user', 'content': message_content})
    
    # Get AI response with task-appropriate model
    task_type = 'analysis' if mode == 'advanced' else 'chat'
    result = chat_service.chat(sanitized_history, use_web_search=True, task_type=task_type)
    
    # Update rate limit
    cache.set(rate_key, chat_count + 1, 3600)
    
    return JsonResponse({
        'success': result['success'],
        'message': result['content'],
        'session_id': 0, # dummy ID for JS compatibility
        'session_title': 'Chat',
        'message_id': 0,
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
    
    valid_types = ['description', 'historical', 'cultural', 'translation', 'artifact']
    if analysis_type not in valid_types:
        analysis_type = 'description'
    
    # Map old 'describe' to new 'description' for backwards compatibility
    if analysis_type == 'describe':
        analysis_type = 'description'
    
    # Rate limiting
    rate_key = f'ai_vision_{request.user.id}'
    count = cache.get(rate_key, 0)
    if count >= 20:  # 20 analyses per hour
        return JsonResponse({'error': 'Analysis limit reached. Please wait.'}, status=429)
    
    archive = get_object_or_404(Archive, id=archive_id, is_approved=True)
    
    # Stateless: we no longer cache or check ArchiveAnalysis model
    
    # Get image
    if archive.image:
        image_file = archive.image
    elif archive.featured_image:
        image_file = archive.featured_image
    else:
        return JsonResponse({'error': 'No image to analyze'}, status=400)

    # Use a temporary file to handle both local and cloud storage
    import tempfile
    import os
    import shutil
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
        try:
            image_file.open('rb')
            shutil.copyfileobj(image_file, tmp)
            image_file.close()
            tmp_path = tmp.name
        except Exception as e:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            logger.error(f"Error processing image for archive analysis: {e}")
            return JsonResponse({'error': 'Failed to process image. Please try again.'}, status=500)
    
    metadata = {
        'title': archive.title,
        'description': archive.description,
        'caption': archive.caption,
        'location': archive.location,
        'date': archive.circa_date or (str(archive.date_created) if archive.date_created else ''),
        'author': archive.original_author,
        'category': archive.category.name if archive.category else ''
    }
    
    try:
        # Analyze
        result = vision_service.analyze(tmp_path, analysis_type, archive_context=metadata)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    if result['success']:
        cache.set(rate_key, count + 1, 3600)
    
    return JsonResponse({
        'success': result['success'],
        'content': result['content'],
        'cached': False,
    })


@login_required
@require_POST
def generate_tts(request):
    """Generate text-to-speech audio metadata and store in cache."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    text = data.get('text', '').strip()
    voice = data.get('voice', data.get('language', 'default'))
    
    if not text:
        return JsonResponse({'error': 'Text is required'}, status=400)
    
    # Rate limiting
    rate_key = f'ai_tts_{request.user.id}'
    count = cache.get(rate_key, 0)
    if count >= 30:
        return JsonResponse({'error': 'TTS limit reached'}, status=429)
    
    result = tts_service.generate_audio(text, voice)
    
    if result['success']:
        import uuid
        audio_id = str(uuid.uuid4())
        
        # Store audio bytes and content type in cache for 5 minutes
        cache_data = {
            'bytes': result['audio_bytes'],
            'content_type': result['content_type']
        }
        cache.set(f"tts_data_{audio_id}", cache_data, 300)
        
        # Construct serve URL
        from django.urls import reverse
        serve_url = reverse('ai:serve_tts', kwargs={'audio_id': audio_id})
        
        cache.set(rate_key, count + 1, 3600)
        
        return JsonResponse({
            'success': True,
            'url': serve_url,
            'provider': result['provider']
        })
    
    return JsonResponse({
        'success': False,
        'error': result.get('error', 'TTS failed')
    })


@require_GET
def serve_tts_audio(request, audio_id):
    """Serve audio bytes directly from cache."""
    from django.http import HttpResponse, Http404
    
    cache_key = f"tts_data_{audio_id}"
    cache_data = cache.get(cache_key)
    
    if not cache_data:
        raise Http404("Audio expired or not found")
    
    response = HttpResponse(cache_data['bytes'], content_type=cache_data['content_type'])
    response['Content-Disposition'] = f'inline; filename="tts_{str(audio_id)[:8]}"'
    # Prevent caching by browser
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response





@login_required
@require_GET
def chat_history(request):
    """Stateless: history is no longer provided."""
    return JsonResponse({'sessions': []})


@login_required
@require_POST
def delete_session(request):
    """Stateless: delete is a no-op but returns success."""
    return JsonResponse({'success': True})


@login_required
@require_POST
def generate_insight_content(request):
    """Generate or refine insight content using AI."""
    
    # Rate limiting — consistent with analyze_archive (20/hour)
    rate_key = f'ai_insight_gen_{request.user.id}'
    gen_count = cache.get(rate_key, 0)
    if gen_count >= 20:
        return JsonResponse({'success': False, 'error': 'Generation limit reached. Please wait a while.'}, status=429)
    
    try:
        data = json.loads(request.body)
        topic = data.get('topic', '')
        current_content = data.get('current_content', '')
        instruction = data.get('instruction', '')
        archive_context = data.get('archive_context', '')
        
        if not topic and not current_content and not instruction:
            return JsonResponse({'success': False, 'error': 'No input provided'}, status=400)
        
        # Construct message
        messages = []
        
        prompt = "Help me write or refine a post for the Igbo Archives."
        if topic:
            prompt += f"\n\nTopic: {topic}"
        if instruction:
            prompt += f"\n\nInstruction: {instruction}"
        if archive_context:
            prompt += f"\n\nArchive Context (Source Material):\n{archive_context}"
        if current_content:
            prompt += f"\n\nCurrent Content to Refine:\n{current_content}"
            
        messages.append({'role': 'user', 'content': prompt})
        
        # Call AI
        # We prefer using web search if topic is provided to get facts
        response = chat_service.chat(messages, use_web_search=bool(topic))
        
        if response['success']:
            cache.set(rate_key, gen_count + 1, 3600)
            return JsonResponse({
                'success': True,
                'content': response['content']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': response.get('content', 'AI generation failed')
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Insight content generation error: {e}")
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred. Please try again.'}, status=500)


def coming_soon(request):
    """Legacy redirect to AI home."""
    return redirect('ai:home')
