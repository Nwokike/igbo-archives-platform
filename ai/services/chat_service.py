"""
Igbo Archives AI Chat Service.
Grounded AI with database access, web search, and citations.
Updated February 2026 — anti-hallucination overhaul.
"""
import logging
import re
from django.conf import settings
from django.core.cache import cache
from .key_manager import key_manager
from .constants import SYSTEM_PROMPT, SITE_URL

logger = logging.getLogger(__name__)


def extract_search_keywords(query: str, max_keywords: int = 5) -> list:
    """Extract meaningful search keywords from a user query.
    
    Strips common stop words and question phrases to get the actual
    search terms. Returns a list of keywords.
    """
    # Remove common question words and filler
    stop_phrases = [
        r'^(what|who|where|when|why|how|can you|could you|please|tell me|'
        r'i want to|i need|show me|find|search|look for|help me|'
        r'do you have|is there|are there|about|regarding)\s+',
    ]
    cleaned = query.lower().strip()
    for pattern in stop_phrases:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
        'and', 'or', 'but', 'not', 'this', 'that', 'it', 'its',
        'any', 'some', 'all', 'more', 'most', 'me', 'my', 'your',
        'our', 'their', 'them', 'they', 'we', 'you', 'i', 'do',
        'does', 'did', 'have', 'has', 'had', 'will', 'would',
        'can', 'could', 'should', 'shall', 'may', 'might',
    }
    
    words = [w for w in cleaned.split() if w not in stop_words and len(w) > 2]
    return words[:max_keywords] if words else [query.strip()[:50]]


def get_database_context(query: str, max_results: int = 5) -> str:
    """Search the database for relevant content using keyword matching.
    
    Uses extracted keywords to search across multiple fields, returning
    only REAL content with REAL URLs that the AI can safely cite.
    """
    from django.db.models import Q
    
    keywords = extract_search_keywords(query)
    context_parts = []
    
    try:
        # Build Q objects that match ANY keyword across multiple fields
        # Search archives
        from archives.models import Archive
        archive_q = Q()
        for kw in keywords:
            archive_q |= (
                Q(title__icontains=kw) |
                Q(description__icontains=kw) |
                Q(caption__icontains=kw)
            )
        archives = Archive.objects.filter(
            archive_q, is_approved=True
        ).distinct()[:max_results]
        
        if archives:
            context_parts.append("### Archives Found in Database:")
            for a in archives:
                full_url = f"{SITE_URL}/archives/{a.slug}/"
                desc = (a.description[:200] + '...') if a.description and len(a.description) > 200 else (a.description or '')
                context_parts.append(f"- 答 [{a.title}]({full_url}): {desc}")
        
        # Search insights
        from insights.models import InsightPost
        insight_q = Q()
        for kw in keywords:
            insight_q |= (
                Q(title__icontains=kw) |
                Q(excerpt__icontains=kw)
            )
        insights = InsightPost.objects.filter(
            insight_q, is_approved=True, is_published=True
        ).distinct()[:max_results]
        
        if insights:
            context_parts.append("\n### Insights Found in Database:")
            for i in insights:
                full_url = f"{SITE_URL}/insights/{i.slug}/"
                excerpt_text = i.excerpt[:200] if i.excerpt else ''
                context_parts.append(f"- 庁 [{i.title}]({full_url}): {excerpt_text}")
        
        # Search books
        from books.models import BookRecommendation
        book_q = Q()
        for kw in keywords:
            book_q |= (
                Q(book_title__icontains=kw) |
                Q(author__icontains=kw) |
                Q(title__icontains=kw)
            )
        books = BookRecommendation.objects.filter(
            book_q, is_approved=True, is_published=True
        ).distinct()[:max_results]
        
        if books:
            context_parts.append("\n### Books Found in Database:")
            for b in books:
                full_url = f"{SITE_URL}/books/{b.slug}/"
                context_parts.append(f"- 答 [{b.book_title}]({full_url}) by {b.author}")
    
    except Exception as e:
        logger.error(f"Database context error: {e}")
    
    return "\n".join(context_parts) if context_parts else ""


def web_search(query: str, max_results: int = 3) -> str:
    """Search the web using DuckDuckGo (unlimited free)."""
    try:
        from duckduckgo_search import DDGS
        
        # Try default backend (api) first
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
        except Exception as e:
            logger.warning(f"DDG search default backend failed: {e}. Retrying with 'html' backend.")
            # Fallback to 'html' backend which is more robust against API parsing errors
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results, backend='html'))
        
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
        # Final catch-all to ensure we never crash the chat
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
        self.max_tokens = 2500
        self.temperature = 0.4  # Lower = more factual, less hallucination
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
        
        # Build grounded context — ALWAYS search both DB and web
        context_parts = []
        
        # Database context — always search
        db_context = get_database_context(user_message)
        if db_context:
            context_parts.append(db_context)
        
        # Web search context — always search (not just when DB is empty)
        if use_web_search:
            search_query = user_message
            # Add Igbo context if not already present
            if 'igbo' not in user_message.lower():
                search_query += " Igbo culture"
            web_context = web_search(search_query)
            if web_context:
                context_parts.append(web_context)
        
        # If no context found at all, add an explicit note
        if not context_parts:
            grounded_context = "NO RELEVANT CONTENT FOUND in database or web search. Answer based on your general knowledge about Igbo culture, but clearly state that you are using general knowledge and NOT referencing specific archives."
        else:
            grounded_context = "\n\n".join(context_parts)
        
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
                        system_content += f"\n\n---\n## PROVIDED CONTEXT (cite ONLY from this):\n{context}\n---\n\nIMPORTANT: Only reference the links and titles shown above. Do NOT invent any URLs or titles not listed here. Format your entire response in Markdown."
                    else:
                        system_content += "\n\nNo database or web results were found for this query. Answer using your general knowledge but do NOT fabricate any archive links. Format your entire response in Markdown."
                    
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
        """Chat with Gemini using fallback chain (2.5 Flash 竊3 Flash)."""
        
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
                        system_content += f"\n\n---\n## PROVIDED CONTEXT (cite ONLY from this):\n{context}\n---\n\nIMPORTANT: Only reference the links and titles shown above. Do NOT invent any URLs or titles not listed here. Format your entire response in Markdown."
                    else:
                        system_content += "\n\nNo database or web results were found. Answer using general knowledge but do NOT fabricate any archive links. Format your response in Markdown."
                    
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