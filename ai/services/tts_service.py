"""
Text-to-Speech Service for Igbo Archives.
Uses YarnGPT for Igbo (primary), Gemini TTS as fallback.

YarnGPT: African language TTS - https://yarngpt.ai/api/v1/tts
- 80 requests/day limit
- 16 Nigerian voices available
- Max 2000 characters per request

Gemini TTS: High quality fallback (100/day)

Combined: 180 TTS/day capacity
"""
import logging
import os
import uuid
import requests
from pathlib import Path
from django.conf import settings
from .key_manager import key_manager

logger = logging.getLogger(__name__)


class TTSService:
    """
    Text-to-Speech service with YarnGPT primary (Igbo) and Gemini TTS fallback.
    
    Rate Limits:
    1. YarnGPT: 80 requests/day (Igbo-native)
    2. Gemini TTS: 10 RPM, ~100/day (high quality backup)
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
    
    # Gemini TTS model
    GEMINI_TTS_MODEL = "gemini-2.5-flash-tts"
    
    def __init__(self):
        pass
    
    @property
    def is_available(self):
        """Check if any TTS is available."""
        return self._has_yarngpt or self._has_gemini_tts
    
    @property
    def _has_yarngpt(self):
        """Check if YarnGPT API key is available."""
        return bool(getattr(settings, 'YARNGPT_API_KEY', None))
    
    @property
    def _has_gemini_tts(self):
        """Check if Gemini TTS is available."""
        return key_manager.has_gemini
    
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
        
        # YarnGPT max is 2000 characters
        text = text[:2000]
        
        # Resolve voice name
        voice_name = self.YARNGPT_VOICES.get(voice, voice)
        if voice_name not in self.YARNGPT_VOICES.values():
            voice_name = 'Chinenye'  # Default Igbo voice
        
        if self._has_yarngpt:
            # Try YarnGPT with a small retry on timeout
            max_retries = 2
            last_error = ""
            
            for attempt in range(max_retries):
                result = self._yarngpt_generate(text, voice_name)
                if result['success']:
                    return result
                
                last_error = result.get('error', 'Unknown error')
                if "timeout" in last_error.lower() and attempt < max_retries - 1:
                    logger.warning(f"YarnGPT timeout (attempt {attempt+1}), retrying...")
                    continue
                break
            
            return {
                'success': False,
                'audio_bytes': None,
                'content_type': '',
                'provider': 'yarngpt',
                'error': f"YarnGPT failed: {last_error}"
            }
        
        return {
            'success': False,
            'audio_bytes': None,
            'content_type': '',
            'provider': '',
            'error': 'YarnGPT service not configured'
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
            
            response = requests.post(
                self.YARNGPT_API_URL,
                headers=headers,
                json=payload,
                timeout=120
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
                
                logger.error(f"YarnGPT failed ({response.status_code}): {error_msg}")
                return {
                    'success': False,
                    'audio_bytes': None,
                    'content_type': '',
                    'provider': 'yarngpt',
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"YarnGPT TTS error: {e}")
            return {
                'success': False,
                'audio_bytes': None,
                'content_type': '',
                'provider': 'yarngpt',
                'error': str(e)
            }
    
# Singleton instance
tts_service = TTSService()
