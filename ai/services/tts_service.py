"""
Text-to-Speech Service for Igbo Archives.
Uses YarnGPT for Igbo (primary), Gemini TTS as fallback.

YarnGPT: African language TTS - https://yarngpt.ai/api/v1/tts
- 80 requests/day limit
- 16 Nigerian voices available
- Max 2000 characters per request

Gemini TTS: High quality fallback (Paid Tier)
- Uses Gemini 2.5 TTS models (Specialized)
- Falls back to Gemini 2.5/3 Flash (High Quota) if specialized limits are hit
"""
import logging
import os
import requests
from django.conf import settings
from .key_manager import key_manager

logger = logging.getLogger(__name__)


class TTSService:
    """
    Text-to-Speech service with YarnGPT primary (Igbo) and Gemini TTS fallback.
    
    Rate Limits:
    1. YarnGPT: 80 requests/day (Igbo-native)
    2. Gemini Specialized (TTS): ~150 requests/day
    3. Gemini Standard (Flash): 10,000+ requests/day (Fail-safe)
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
    
    # Fallback Models (Ordered by Quality -> Stability -> Quota)
    GEMINI_MODELS = [
        "gemini-2.5-flash-tts",
        "gemini-2.5-pro-tts",
        "gemini-2.5-flash",
        "gemini-3-flash", 
    ]
    
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
                if "timeout" in error_msg and attempt < max_retries - 1:
                    logger.warning(f"YarnGPT timeout (attempt {attempt+1}), retrying...")
                    continue
                break
            
            logger.warning(f"YarnGPT failed, failing over to Gemini: {result.get('error')}")

        # 2. Try Gemini (Fallback) - High availability
        if self._has_gemini_tts:
            return self._gemini_generate(text)
            
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
                timeout=30 
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

    def _gemini_generate(self, text: str) -> dict:
        """Generate speech using Gemini (with model fallback)."""
        try:
            import google.generativeai as genai
            
            api_key = key_manager.get_key()
            if not api_key:
                return {'success': False, 'error': 'No Gemini API key'}
                
            genai.configure(api_key=api_key)
            
            last_error = None
            
            # Loop through available models to find one that works
            for model_name in self.GEMINI_MODELS:
                try:
                    model = genai.GenerativeModel(model_name)
                    
                    response = model.generate_content(
                        f"Please read this text aloud naturally: {text}",
                        generation_config=genai.types.GenerationConfig(
                            response_mime_type="audio/mp3"
                        )
                    )
                    
                    # Extract audio data
                    audio_data = None
                    if response.parts:
                        part = response.parts[0]
                        if hasattr(part, 'inline_data'):
                            audio_data = part.inline_data.data
                        elif hasattr(part, 'blob'):
                             audio_data = part.blob.data
                    
                    if audio_data:
                        logger.info(f"Gemini TTS succeeded with model: {model_name}")
                        return {
                            'success': True,
                            'audio_bytes': audio_data,
                            'content_type': 'audio/mpeg',
                            'provider': 'gemini',
                            'error': ''
                        }
                        
                except Exception as e:
                    logger.warning(f"Gemini TTS attempt with {model_name} failed: {e}")
                    last_error = e
                    continue # Try next model

            return {
                'success': False, 
                'error': f"Gemini TTS failed after trying all models. Last error: {last_error}"
            }

        except Exception as e:
            logger.error(f"Gemini TTS Critical Error: {e}")
            return {
                'success': False,
                'audio_bytes': None,
                'content_type': '',
                'provider': 'gemini',
                'error': str(e)
            }
    
# Singleton instance
tts_service = TTSService()