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
        
        # Try YarnGPT first (works for Igbo)
        if self._has_yarngpt:
            result = self._yarngpt_generate(text, voice_name)
            if result['success']:
                return result
            logger.warning(f"YarnGPT failed, trying Gemini TTS: {result.get('error')}")
        
        # Fallback to Gemini TTS (high quality)
        if self._has_gemini_tts:
            result = self._gemini_tts_generate(text, voice_name)
            if result['success']:
                return result
        
        return {
            'success': False,
            'audio_bytes': None,
            'content_type': '',
            'provider': '',
            'error': 'All TTS providers failed'
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
    
    def _gemini_tts_generate(self, text: str, voice_name: str) -> dict:
        """Generate audio bytes using Gemini TTS."""
        try:
            from google import genai
            
            api_key = key_manager.get_gemini_key()
            if not api_key:
                return {
                    'success': False,
                    'audio_bytes': None,
                    'content_type': '',
                    'provider': 'gemini_tts',
                    'error': 'No Gemini API key available'
                }
            
            client = genai.Client(api_key=api_key)
            
            # Generate speech
            response = client.models.generate_content(
                model=self.GEMINI_TTS_MODEL,
                contents=text,
                config={
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": "Kore"
                            }
                        }
                    }
                }
            )
            
            if response.candidates and response.candidates[0].content.parts:
                audio_data = response.candidates[0].content.parts[0].inline_data.data
                
                return {
                    'success': True,
                    'audio_bytes': audio_data,
                    'content_type': 'audio/wav',
                    'provider': 'gemini_tts',
                    'error': ''
                }
            
            return {
                'success': False,
                'audio_bytes': None,
                'content_type': '',
                'provider': 'gemini_tts',
                'error': 'No audio in response'
            }
            
        except Exception as e:
            logger.error(f"Gemini TTS error: {e}")
            return {
                'success': False,
                'audio_bytes': None,
                'content_type': '',
                'provider': 'gemini_tts',
                'error': str(e)
            }
    
# Singleton instance
tts_service = TTSService()
