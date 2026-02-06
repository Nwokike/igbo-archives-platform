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
    
    # Get AI response with task-appropriate model
    task_type = 'analysis' if mode == 'advanced' else 'chat'
    result = chat_service.chat(messages, use_web_search=True, task_type=task_type)
    
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
            return JsonResponse({'error': f'Error processing image: {str(e)}'}, status=500)
    
    try:
        # Analyze
        result = vision_service.analyze(tmp_path, analysis_type)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
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


@login_required
@require_POST
def generate_insight_content(request):
    """Generate or refine insight content using AI."""
    
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
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def coming_soon(request):
    """Legacy redirect to AI home."""
    return redirect('ai:home')
