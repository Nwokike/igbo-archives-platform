"""
Igbo Archives AI Chat Service.
Grounded AI with database access, web search, and citations.
Updated January 2026 with latest models.
"""
import logging
from django.conf import settings
from django.core.cache import cache
from .key_manager import key_manager

logger = logging.getLogger(__name__)

# Live site URL and routes for directing users
SITE_URL = getattr(settings, 'SITE_URL', 'https://igboarchives.com.ng')
ROUTES = {
    'archive': f'{SITE_URL}/archives/{{slug}}/',
    'insight': f'{SITE_URL}/insights/{{slug}}/',
    'book': f'{SITE_URL}/books/{{slug}}/',
    'category': f'{SITE_URL}/archives/category/{{slug}}/',
    'author': f'{SITE_URL}/archives/author/{{slug}}/',
    'search': f'{SITE_URL}/archives/?search={{query}}',
    'home': f'{SITE_URL}',
    'chat': f'{SITE_URL}/ai/',
}

SYSTEM_PROMPT = f"""You are the Igbo Archives AI, an intelligent assistant specialized in Igbo culture, history, language, and heritage.

IMPORTANT GUIDELINES:
1. Always be accurate - if you're not sure, say so.
2. When you reference information from the archives, include FULL clickable URLs.
3. When you use web search results, cite the source.
4. Use Igbo words naturally with translations (e.g., "Ndewo (Welcome)").
5. Be culturally sensitive and encourage preservation of Igbo heritage.
6. Direct users to relevant pages on the platform using full URLs.
7. You have access to both the Igbo Archives database and the internet. Use them to provide comprehensive and grounded answers.

LIVE SITE: {SITE_URL}

When citing sources, use FULL URLs:
- For archives: [{SITE_URL}/archives/slug/](full_url)
- For insights: [{SITE_URL}/insights/slug/](full_url)
- For books: [{SITE_URL}/books/slug/](full_url)
- For web: [Source](URL)

Format archive links as styled cards when appropriate:
📚 **Archive:** [Title]({SITE_URL}/archives/slug/) - Brief description

Be helpful, accurate, and celebrate Igbo culture."""


def get_database_context(query: str, max_results: int = 5) -> str:
    """Search the database for relevant content to provide context with full URLs."""
    from django.db.models import Q
    
    context_parts = []
    
    try:
        # Search archives
        from archives.models import Archive
        archives = Archive.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(caption__icontains=query),
            is_approved=True
        )[:max_results]
        
        if archives:
            context_parts.append("**Relevant Archives:**")
            for a in archives:
                full_url = f"{SITE_URL}/archives/{a.slug}/"
                desc = a.description[:200] + '...' if len(a.description) > 200 else a.description
                context_parts.append(f"- 📚 [{a.title}]({full_url}): {desc}")
        
        # Search insights
        from insights.models import InsightPost
        insights = InsightPost.objects.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query),
            is_approved=True,
            is_published=True
        )[:max_results]
        
        if insights:
            context_parts.append("\n**Relevant Insights:**")
            for i in insights:
                full_url = f"{SITE_URL}/insights/{i.slug}/"
                excerpt_text = i.excerpt[:200] if i.excerpt else ''
                context_parts.append(f"- 💡 [{i.title}]({full_url}): {excerpt_text}")
        
        # Search books
        from books.models import BookRecommendation
        books = BookRecommendation.objects.filter(
            Q(book_title__icontains=query) |
            Q(author__icontains=query) |
            Q(title__icontains=query),
            is_approved=True,
            is_published=True
        )[:max_results]
        
        if books:
            context_parts.append("\n**Relevant Book Recommendations:**")
            for b in books:
                full_url = f"{SITE_URL}/books/{b.slug}/"
                context_parts.append(f"- 📚 [{b.book_title}]({full_url}) by {b.author}")
    
    except Exception as e:
        logger.error(f"Database context error: {e}")
    
    return "\n".join(context_parts) if context_parts else ""


def web_search(query: str, max_results: int = 3) -> str:
    """Search the web using DuckDuckGo (unlimited free)."""
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return ""
        
        context_parts = ["**Web Search Results:**"]
        for r in results:
            title = r.get('title', 'No title')
            url = r.get('href', '')
            body = r.get('body', '')[:200]
            context_parts.append(f"- [{title}]({url}): {body}...")
        
        return "\n".join(context_parts)
    
    except ImportError:
        logger.warning("duckduckgo_search not installed")
        return ""
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return ""


class ChatService:
    """
    AI chat service with database grounding, web search, and smart model fallback.
    
    AI USE CASES:
    1. Chat/Conversation - Main AI chat with users (Igbo-optimized)
    2. Archive Analysis - Describe/analyze archives (cultural, historical context)
    3. Speech-to-Text (STT) - Voice input transcription (Whisper)
    4. Text-to-Speech (TTS) - Reading responses aloud (YarnGPT/gTTS)
    5. Title Generation - Quick title/summary generation
    
    MODEL STRATEGY: Fallback chain based on Igbo language testing
    - Use Groq models first (faster), fallback through chain on errors
    - Gemini as final backup (never offline)
    """
    
    # Igbo-tested models ranked by quality (fallback chain)
    GROQ_FALLBACK_CHAIN = [
        'moonshotai/kimi-k2-instruct',       
        'moonshotai/kimi-k2-instruct-0905',  
        'openai/gpt-oss-120b',               
        'openai/gpt-oss-20b',                
        'qwen/qwen3-32b',                    
    ]
    
    # Gemini fallback   
    GEMINI_FALLBACK_CHAIN = [
        'gemini-2.5-flash', 
        'gemini-3-flash',    
    ]
    
    # Note: STT moved to stt_service.py using NaijaLingo ASR (Nigerian languages)
    
    def __init__(self):
        self.max_tokens = 1500
        self.temperature = 0.7
        self._groq_clients = {}
        self._gemini_models = {}
    
    def _get_groq_client(self, api_key):
        if api_key not in self._groq_clients:
            try:
                from groq import Groq
                self._groq_clients[api_key] = Groq(api_key=api_key)
            except Exception as e:
                logger.error(f"Groq client error: {e}")
                return None
        return self._groq_clients[api_key]
    
    def _get_gemini_model(self, api_key, model_name):
        cache_key = f"{api_key}:{model_name}"
        if cache_key not in self._gemini_models:
            try:
                from google import genai
                # Store the client with model name for later use
                self._gemini_models[cache_key] = {
                    'client': genai.Client(api_key=api_key),
                    'model': model_name
                }
            except Exception as e:
                logger.error(f"Gemini client error: {e}")
                return None
        return self._gemini_models[cache_key]
    
    @property
    def is_available(self):
        return key_manager.has_groq or key_manager.has_gemini
    
    def chat(self, messages: list, use_web_search: bool = True, task_type: str = 'chat') -> dict:
        """
        Send a chat message with database and web grounding.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            use_web_search: Whether to use web search for context
            task_type: Type of task - affects model selection:
                - 'chat': Simple conversation, use fast Groq models first
                - 'analysis': Complex reasoning (archive analysis, cultural context), prefer Gemini
                - 'title': Quick title/summary generation, use fastest model
        """
        if not self.is_available:
            return {
                'success': False,
                'content': 'AI service is being configured. Please try again later.',
            }
        
        # Get the latest user message for context search
        user_message = ""
        for msg in reversed(messages):
            if msg['role'] == 'user':
                user_message = msg['content']
                break
        
        # Build grounded context
        context_parts = []
        
        # Database context
        db_context = get_database_context(user_message)
        if db_context:
            context_parts.append(db_context)
        
        # Web search context (if enabled and no database results)
        if use_web_search and not db_context:
            web_context = web_search(user_message + " Igbo culture")
            if web_context:
                context_parts.append(web_context)
        
        grounded_context = "\n\n".join(context_parts) if context_parts else ""
        
        # Choose provider based on task type
        if task_type == 'analysis':
            # Complex analysis: Gemini has better reasoning, use first
            # Falls back to Groq if Gemini unavailable
            if key_manager.has_gemini:
                result = self._gemini_chat(messages, grounded_context)
                if result['success']:
                    return result
            
            if key_manager.has_groq:
                result = self._groq_chat(messages, grounded_context)
                if result['success']:
                    return result
        else:
            # Simple chat/title: Groq is faster & good for Igbo
            # Falls back to Gemini if Groq exhausted
            if key_manager.has_groq:
                result = self._groq_chat(messages, grounded_context)
                if result['success']:
                    return result
            
            if key_manager.has_gemini:
                result = self._gemini_chat(messages, grounded_context)
                if result['success']:
                    return result
        
        return {
            'success': False,
            'content': 'AI is experiencing high demand. Please try again in a moment.',
        }
    
    def _groq_chat(self, messages: list, context: str) -> dict:
        """Chat with Groq using Igbo-tested model fallback chain."""
        
        for current_model in self.GROQ_FALLBACK_CHAIN:
            for _ in range(len(key_manager.groq_keys) if key_manager.has_groq else 0):
                api_key = key_manager.get_groq_key()
                if not api_key:
                    break
                
                client = self._get_groq_client(api_key)
                if not client:
                    continue
                
                try:
                    system_content = SYSTEM_PROMPT
                    if context:
                        system_content += f"\n\n**Context from Igbo Archives and Web:**\n{context}\n\nUse this information in your response with proper citations."
                    
                    full_messages = [{'role': 'system', 'content': system_content}]
                    full_messages.extend(messages[-10:])
                    
                    response = client.chat.completions.create(
                        model=current_model,
                        messages=full_messages,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                    )
                    
                    return {
                        'success': True,
                        'content': response.choices[0].message.content,
                        'model': current_model,
                    }
                    
                except Exception as e:
                    error_str = str(e).lower()
                    if any(x in error_str for x in ['rate', 'limit', '429', 'quota']):
                        key_manager.mark_rate_limited('groq', api_key, 3600)
                        continue
                    # Model not available, try next in chain
                    if 'model' in error_str or 'not found' in error_str:
                        logger.warning(f"Model {current_model} not available, trying fallback")
                        break
                    logger.error(f"Groq error: {e}")
                    break
        
        return {'success': False, 'content': ''}
    
    def _gemini_chat(self, messages: list, context: str) -> dict:
        """Chat with Gemini using fallback chain (2.5 Flash → 3 Flash)."""
        
        for model_name in self.GEMINI_FALLBACK_CHAIN:
            for _ in range(len(key_manager.gemini_keys) if key_manager.has_gemini else 0):
                api_key = key_manager.get_gemini_key()
                if not api_key:
                    break
                
                model = self._get_gemini_model(api_key, model_name)
                if not model:
                    continue
                
                try:
                    system_content = SYSTEM_PROMPT
                    if context:
                        system_content += f"\n\n**Context from Igbo Archives and Web:**\n{context}\n\nUse this information with proper citations."
                    
                    prompt_parts = [system_content, "\nConversation:"]
                    for msg in messages[-10:]:
                        role = "User" if msg['role'] == 'user' else "Assistant"
                        prompt_parts.append(f"\n{role}: {msg['content']}")
                    prompt_parts.append("\nAssistant:")
                    
                    response = model['client'].models.generate_content(
                        model=model['model'],
                        contents='\n'.join(prompt_parts)
                    )
                    
                    return {
                        'success': True,
                        'content': response.text,
                        'model': model_name,
                    }
                    
                except Exception as e:
                    error_str = str(e).lower()
                    if any(x in error_str for x in ['rate', 'limit', 'quota', '429']):
                        key_manager.mark_rate_limited('gemini', api_key, 3600)
                        continue
                    # Model not available, try next in chain
                    if 'model' in error_str or 'not found' in error_str:
                        logger.warning(f"Model {model_name} not available, trying fallback")
                        break
                    logger.error(f"Gemini error: {e}")
                    break
        
        return {'success': False, 'content': ''}
    
    def generate_title(self, first_message: str) -> str:
        """Generate a short title for a conversation."""
        result = self.chat(
            [{'role': 'user', 'content': f'Create a very short title (max 5 words, no quotes) for: "{first_message[:200]}"'}],
            use_web_search=False
        )
        
        if result['success']:
            title = result['content'].strip().strip('"\'')
            return title[:100]
        return first_message[:50] + '...' if len(first_message) > 50 else first_message


chat_service = ChatService()

