"""
AI Services for Igbo Archives.
Uses advanced language models with multi-key rotation for maximum free tier usage.

Best Free Models (December 2025):
- Gemini 2.5 Flash: Best balance of speed/quality for free tier
- Groq Llama 3.3 70B Versatile: Best open-source LLM
- Groq Llama 4 Scout: Newest, most advanced (free tier $0.00)
- Groq Whisper Large V3: Best free STT
"""
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    Manages multiple API keys with intelligent rotation.
    Maximizes free tier usage across multiple accounts.
    """
    
    def __init__(self):
        gemini_keys_str = getattr(settings, 'GEMINI_API_KEYS', '') or ''
        groq_keys_str = getattr(settings, 'GROQ_API_KEYS', '') or ''
        
        self.gemini_keys = [k.strip() for k in gemini_keys_str.split(',') if k.strip()]
        self.groq_keys = [k.strip() for k in groq_keys_str.split(',') if k.strip()]
        
        if not self.gemini_keys:
            single_key = getattr(settings, 'GEMINI_API_KEY', '')
            if single_key:
                self.gemini_keys = [single_key]
        
        if not self.groq_keys:
            single_key = getattr(settings, 'GROQ_API_KEY', '')
            if single_key:
                self.groq_keys = [single_key]
    
    def get_gemini_key(self):
        """Get next available Gemini API key."""
        if not self.gemini_keys:
            return None
        
        cache_key = 'ai_gemini_idx'
        idx = cache.get(cache_key, 0)
        blocked = cache.get('ai_gemini_blocked', set())
        
        for i in range(len(self.gemini_keys)):
            key_idx = (idx + i) % len(self.gemini_keys)
            key = self.gemini_keys[key_idx]
            
            if key not in blocked:
                cache.set(cache_key, (key_idx + 1) % len(self.gemini_keys), 3600)
                return key
        
        cache.delete('ai_gemini_blocked')
        return self.gemini_keys[0]
    
    def get_groq_key(self):
        """Get next available Groq API key."""
        if not self.groq_keys:
            return None
        
        cache_key = 'ai_groq_idx'
        idx = cache.get(cache_key, 0)
        blocked = cache.get('ai_groq_blocked', set())
        
        for i in range(len(self.groq_keys)):
            key_idx = (idx + i) % len(self.groq_keys)
            key = self.groq_keys[key_idx]
            
            if key not in blocked:
                cache.set(cache_key, (key_idx + 1) % len(self.groq_keys), 3600)
                return key
        
        cache.delete('ai_groq_blocked')
        return self.groq_keys[0]
    
    def mark_rate_limited(self, service: str, key: str, duration: int = 3600):
        """Mark a key as temporarily rate limited."""
        cache_key = f'ai_{service}_blocked'
        blocked = cache.get(cache_key, set())
        blocked.add(key)
        cache.set(cache_key, blocked, duration)
        logger.info(f"AI key rotated due to rate limit")
    
    @property
    def has_gemini(self):
        return len(self.gemini_keys) > 0
    
    @property
    def has_groq(self):
        return len(self.groq_keys) > 0
    
    @property
    def total_keys(self):
        return len(self.gemini_keys) + len(self.groq_keys)


key_manager = APIKeyManager()
