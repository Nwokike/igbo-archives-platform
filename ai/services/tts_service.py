"""
Text-to-Speech Service for Igbo Archives.
Uses YarnGPT for Igbo (Nigerian languages).

YarnGPT: African language TTS - https://yarngpt.ai/api/v1/tts
- 80 requests/day limit
- 16 Nigerian voices available
- Max 2000 characters per request
"""
import logging
import os
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TTSService:
    """
    Text-to-Speech service using YarnGPT (Nigerian-native voices).
    
    Rate Limits:
    1. YarnGPT: 80 requests/day
    """
    
    # Official YarnGPT API
    YARNGPT_API_URL = "https://yarngpt.ai/api/v1/tts"
    
    # Nigerian voices available in YarnGPT
    YARNGPT_VOICES = {
        'default': 'Adaora',   
        'female_igbo': 'Chinenye',
        'female_warm': 'Adaora', 
        'female_melodic': 'Idera',
        'female_mature': 'Regina',
        'female_soothing': 'Zainab',
        'female_young': 'Wura',
        'female_energetic': 'Mary',
        'male_calm': 'Osagie',
        'male_confident': 'Jude',
        'male_bold': 'Nonso',
        'male_deep': 'Adam',
        'male_smooth': 'Umar',
        'male_upbeat': 'Tayo',
        'male_rich': 'Femi',
    }
    
    def __init__(self):
        pass
    
    @property
    def is_available(self):
        """Check if any TTS is available."""
        return self._has_yarngpt
    
    @property
    def _has_yarngpt(self):
        """Check if YarnGPT API key is available."""
        return bool(getattr(settings, 'YARNGPT_API_KEY', None))
    
    def generate_audio(self, text: str, voice: str = 'default') -> dict:
        """
        Generate audio bytes from text.
        
        Args:
            text: Text to convert to speech (max 2000 chars)
            voice: Voice key from YARNGPT_VOICES or voice name directly
            
        Returns:
            dict with 'success', 'audio_bytes', 'content_type', 'provider'
        """
        if not self.is_available:
            return {
                'success': False,
                'audio_bytes': None,
                'content_type': '',
                'provider': '',
                'error': 'TTS service not available'
            }
        
        if not text or len(text.strip()) < 2:
            return {
                'success': False,
                'audio_bytes': None,
                'content_type': '',
                'provider': '',
                'error': 'Text is too short'
            }
        
        # 1. Try YarnGPT (Primary) - Best for Igbo pronunciation
        if self._has_yarngpt:
            # YarnGPT max is 2000 characters
            yg_text = text[:2000]
            
            # Resolve voice name
            voice_name = self.YARNGPT_VOICES.get(voice, voice)
            if voice_name not in self.YARNGPT_VOICES.values():
                voice_name = 'Chinenye'  # Default Igbo voice
            
            # Try YarnGPT with a small retry on timeout
            max_retries = 2
            for attempt in range(max_retries):
                result = self._yarngpt_generate(yg_text, voice_name)
                if result['success']:
                    return result
                
                # If it's a timeout, retry once. Otherwise break to fallback.
                error_msg = result.get('error', '').lower()
                if ("timeout" in error_msg or "timed out" in error_msg) and attempt < max_retries - 1:
                    logger.warning(f"YarnGPT timeout (attempt {attempt+1}), retrying...")
                    continue
                break
            
            # Handle failure
            return {
                'success': False,
                'audio_bytes': None,
                'content_type': '',
                'provider': 'yarngpt',
                'error': result.get('error', 'YarnGPT failed')
            }
        
        return {
            'success': False,
            'audio_bytes': None,
            'content_type': '',
            'provider': '',
            'error': 'No TTS provider active'
        }
    
    def _yarngpt_generate(self, text: str, voice: str) -> dict:
        """Generate audio bytes using YarnGPT API."""
        try:
            api_key = getattr(settings, 'YARNGPT_API_KEY', '')
            
            headers = {
                "Authorization": f"Bearer {api_key}",
            }
            
            payload = {
                "text": text,
                "voice": voice,
                "response_format": "mp3"
            }
            
            # Increased timeout to 60s as YarnGPT can be slow on large texts
            response = requests.post(
                self.YARNGPT_API_URL,
                headers=headers,
                json=payload,
                timeout=60 
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'audio_bytes': response.content,
                    'content_type': 'audio/mpeg',
                    'provider': 'yarngpt',
                    'voice': voice,
                    'error': ''
                }
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f"HTTP {response.status_code}")
                except Exception:
                    error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
                
                return {
                    'success': False,
                    'audio_bytes': None,
                    'content_type': '',
                    'provider': 'yarngpt',
                    'error': error_msg
                }
                
        except Exception as e:
            return {
                'success': False,
                'audio_bytes': None,
                'content_type': '',
                'provider': 'yarngpt',
                'error': str(e)
            }

# Singleton instance
tts_service = TTSService()