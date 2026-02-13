"""
AI Services for Igbo Archives.
Uses advanced language models with multi-key rotation for maximum free tier usage.
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
        blocked = cache.get('ai_gemini_blocked', [])
        # Normalize to list for JSON-safe cache serialization
        if isinstance(blocked, set):
            blocked = list(blocked)
        
        for i in range(len(self.gemini_keys)):
            key_idx = (idx + i) % len(self.gemini_keys)
            key = self.gemini_keys[key_idx]
            
            if key not in blocked:
                cache.set(cache_key, (key_idx + 1) % len(self.gemini_keys), 3600)
                return key
        
        # All keys blocked — add cooldown before retrying
        logger.warning("All Gemini keys are rate-limited. Adding 60s cooldown.")
        cache.set('ai_gemini_blocked', blocked, 60)  # Keep blocked for 60s cooldown
        return None
    
    def get_groq_key(self):
        """Get next available Groq API key."""
        if not self.groq_keys:
            return None
        
        cache_key = 'ai_groq_idx'
        idx = cache.get(cache_key, 0)
        blocked = cache.get('ai_groq_blocked', [])
        # Normalize to list for JSON-safe cache serialization
        if isinstance(blocked, set):
            blocked = list(blocked)
        
        for i in range(len(self.groq_keys)):
            key_idx = (idx + i) % len(self.groq_keys)
            key = self.groq_keys[key_idx]
            
            if key not in blocked:
                cache.set(cache_key, (key_idx + 1) % len(self.groq_keys), 3600)
                return key
        
        # All keys blocked — add cooldown before retrying
        logger.warning("All Groq keys are rate-limited. Adding 60s cooldown.")
        cache.set('ai_groq_blocked', blocked, 60)  # Keep blocked for 60s cooldown
        return None
    
    def mark_rate_limited(self, service: str, key: str, duration: int = 3600):
        """Mark a key as temporarily rate limited."""
        cache_key = f'ai_{service}_blocked'
        blocked = cache.get(cache_key, [])
        # Normalize to list for JSON-safe cache serialization
        if isinstance(blocked, set):
            blocked = list(blocked)
        if key not in blocked:
            blocked.append(key)
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
