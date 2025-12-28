"""
Igbo Archives AI Chat Service.
Grounded AI with database access, web search, and citations.
"""
import logging
import re
from django.conf import settings
from django.core.cache import cache
from .key_manager import key_manager

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Igbo Archives AI, an intelligent assistant specialized in Igbo culture, history, language, and heritage.

IMPORTANT GUIDELINES:
1. Always be accurate - if you're not sure, say so
2. When you reference information from the archives, include the citation URL provided
3. When you use web search results, cite the source
4. Use Igbo words naturally with translations (e.g., "Ndewo (Welcome)")
5. Be culturally sensitive and encourage preservation of Igbo heritage

You have access to:
- The Igbo Archives database (archives, insights, book reviews)
- Web search for current information

When citing sources, use this format:
- For archives: [Title](/archives/ID/)
- For insights: [Title](/insights/slug/)
- For books: [Title](/books/slug/)
- For web: [Source](URL)

Be helpful, accurate, and celebrate Igbo culture."""


def get_database_context(query: str, max_results: int = 5) -> str:
    """Search the database for relevant content to provide context."""
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
                url = f"/archives/{a.pk}/"
                context_parts.append(f"- [{a.title}]({url}): {a.description[:200]}..." if len(a.description) > 200 else f"- [{a.title}]({url}): {a.description}")
        
        # Search insights
        from insights.models import Insight
        insights = Insight.objects.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query),
            is_approved=True
        )[:max_results]
        
        if insights:
            context_parts.append("\n**Relevant Insights:**")
            for i in insights:
                url = f"/insights/{i.slug}/"
                context_parts.append(f"- [{i.title}]({url}): {i.summary[:200]}..." if len(i.summary) > 200 else f"- [{i.title}]({url}): {i.summary}")
        
        # Search books
        from books.models import Book
        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(summary__icontains=query),
            is_approved=True
        )[:max_results]
        
        if books:
            context_parts.append("\n**Relevant Books:**")
            for b in books:
                url = f"/books/{b.slug}/"
                context_parts.append(f"- [{b.title}]({url}) by {b.author}: {b.summary[:150]}...")
    
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
    """AI chat service with database grounding and web search."""
    
    MODELS = {
        'groq': 'llama-3.3-70b-versatile',
        'gemini': 'gemini-2.5-flash',
    }
    
    STT_MODEL = 'whisper-large-v3'
    
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
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._gemini_models[cache_key] = genai.GenerativeModel(model_name)
            except Exception as e:
                logger.error(f"Gemini model error: {e}")
                return None
        return self._gemini_models[cache_key]
    
    @property
    def is_available(self):
        return key_manager.has_groq or key_manager.has_gemini
    
    def chat(self, messages: list, use_web_search: bool = True) -> dict:
        """
        Send a chat message with database and web grounding.
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
        
        # Try Groq first, then Gemini
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
        model = self.MODELS['groq']
        
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
                    model=model,
                    messages=full_messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                
                return {
                    'success': True,
                    'content': response.choices[0].message.content,
                }
                
            except Exception as e:
                error_str = str(e).lower()
                if any(x in error_str for x in ['rate', 'limit', '429', 'quota']):
                    key_manager.mark_rate_limited('groq', api_key, 3600)
                    continue
                logger.error(f"Groq error: {e}")
                break
        
        return {'success': False, 'content': ''}
    
    def _gemini_chat(self, messages: list, context: str) -> dict:
        model_name = self.MODELS['gemini']
        
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
                
                response = model.generate_content('\n'.join(prompt_parts))
                
                return {
                    'success': True,
                    'content': response.text,
                }
                
            except Exception as e:
                error_str = str(e).lower()
                if any(x in error_str for x in ['rate', 'limit', 'quota', '429']):
                    key_manager.mark_rate_limited('gemini', api_key, 3600)
                    continue
                logger.error(f"Gemini error: {e}")
                break
        
        return {'success': False, 'content': ''}
    
    def transcribe(self, audio_file_path: str) -> dict:
        """Transcribe audio using Whisper."""
        if not key_manager.has_groq:
            return {'success': False, 'text': '', 'error': 'Speech recognition not available'}
        
        for _ in range(len(key_manager.groq_keys)):
            api_key = key_manager.get_groq_key()
            if not api_key:
                break
            
            client = self._get_groq_client(api_key)
            if not client:
                continue
            
            try:
                with open(audio_file_path, 'rb') as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model=self.STT_MODEL,
                        file=audio_file,
                        response_format='text'
                    )
                
                return {'success': True, 'text': transcription}
                
            except Exception as e:
                error_str = str(e).lower()
                if 'rate' in error_str or 'limit' in error_str:
                    key_manager.mark_rate_limited('groq', api_key, 3600)
                    continue
                return {'success': False, 'text': '', 'error': str(e)}
        
        return {'success': False, 'text': '', 'error': 'Service unavailable'}
    
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
