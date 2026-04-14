"""
Igbo Archives AI Chat Service.
Grounded AI with database access, web search, and citations.
Uses LiteLLM Router for declarative model routing and fallbacks.
"""
import logging
import re
import os
import yaml
import json
import requests
from django.conf import settings
from django.core.cache import cache
from litellm import Router

from .constants import SYSTEM_PROMPT
from .url_validators import is_safe_url
from archives.models import Archive
from lore.models import LorePost

logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = 5) -> str:
    """Perform a web search for grounding using DuckDuckGo."""
    try:
        from ddgs import DDGS
        
        context_parts = []
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
        if not results:
            return ""
            
        context_parts.append("### WEB SEARCH RESULTS:")
        for r in results:
            title = r.get('title', 'No title')
            url = r.get('href', r.get('url', ''))
            body = r.get('body', r.get('snippet', ''))
            if not url or not body:
                continue
            context_parts.append(f"🌐 **Source:** [{title}]({url}) — {body[:500]}")
        
        return "\n".join(context_parts)
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return ""


def extract_search_keywords(query: str, max_keywords: int = 5) -> list:
    """Extract meaningful search keywords from a user query."""
    clean_query = re.sub(r'[^\w\s]', '', query).lower()
    words = clean_query.split()
    
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'and', 'or', 'but', 'how', 'what', 'where', 'who', 'why'}
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords[:max_keywords]


def get_database_context(query: str) -> str:
    """Search the database for relevant cultural context."""
    from django.db.models import Q
    
    keywords = extract_search_keywords(query)
    if not keywords:
        return ""
    
    # Search Archives
    archive_query = Q()
    for kw in keywords:
        archive_query |= Q(title__icontains=kw) | Q(description__icontains=kw)
        
    archives = Archive.objects.filter(archive_query, is_approved=True).distinct()[:3]
    
    # Search Lore
    lore_query = Q()
    for kw in keywords:
        lore_query |= Q(title__icontains=kw) | Q(legacy_content__icontains=kw)
        
    lores = LorePost.objects.filter(lore_query, is_approved=True).distinct()[:2]
    
    context_parts = []
    
    if archives:
        context_parts.append("### RELEVANT ARCHIVES:")
        for a in archives:
            url = f"/archives/{a.id}/"
            context_parts.append(f"📦 **Archive:** [{a.title}]({url}) — {a.description[:300]}...")
            
    if lores:
        context_parts.append("### CULTURAL LORE:")
        for l in lores:
            url = f"/lore/{l.slug}/"
            context_parts.append(f"📝 **Lore:** [{l.title}]({url}) — {l.content[:300]}...")
            
    return "\n".join(context_parts)


class ChatService:
    """
    AI chat service with LiteLLM routing, database grounding, and web search.
    """
    
    def __init__(self):
        self.max_tokens = 2500
        self.temperature = 0.4
        
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models.yaml')
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.router = Router(
                model_list=config.get('model_list', []),
                **(config.get('router_settings', {}))
            )
            logger.info("LiteLLM Router initialized with models.yaml")
        except Exception as e:
            logger.error(f"Failed to load models.yaml: {e}")
            self.router = None

    @property
    def is_available(self):
        return self.router is not None
    
    def chat(self, messages: list, use_web_search: bool = True) -> dict:
        """Send a chat message with grounding."""
        if not self.is_available:
            return {'success': False, 'content': 'AI unavailable.'}
        
        user_message = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), "")
        
        context_parts = []
        db_context = get_database_context(user_message)
        if db_context:
            context_parts.append(db_context)
        
        if use_web_search and user_message:
            search_query = user_message
            if any(t in user_message.lower() for t in ['igbo', 'ala', 'nri', 'culture']) and 'igbo' not in user_message.lower():
                search_query += ' Igbo'
            
            web_context = web_search(search_query, max_results=5)
            if web_context:
                context_parts.append(web_context)
        
        grounded_context = "\n\n".join(context_parts) if context_parts else "Use general knowledge."
        return self._litellm_chat(messages, grounded_context, "chat-primary")

    def _litellm_chat(self, messages: list, context: str, model_name: str) -> dict:
        """Unified chat call via LiteLLM Router."""
        try:
            system_content = f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context}\n\nAnswer using provided context or general knowledge."
            full_messages = [{'role': 'system', 'content': system_content}]
            full_messages.extend(messages[-5:])
            
            response = self.router.completion(
                model=model_name,
                messages=full_messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return {'success': True, 'content': response.choices[0].message.content, 'model': response.model}
        except Exception as e:
            logger.error(f"LiteLLM error: {e}")
            return {'success': False, 'content': 'AI request failed.'}
    
    def generate_title(self, first_message: str) -> str:
        """Generate a title."""
        result = self.chat([{'role': 'user', 'content': f'Short title for: "{first_message[:200]}"'}], False)
        if result['success']:
            return result['content'].strip().strip('"\'')[:100]
        return first_message[:50]


chat_service = ChatService()
