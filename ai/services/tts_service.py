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
        self._output_dir = None
    
    @property
    def output_dir(self):
        """Lazily create output directory (settings may not be ready at import time)."""
        if self._output_dir is None:
            self._output_dir = Path(settings.MEDIA_ROOT) / 'tts'
            self._output_dir.mkdir(parents=True, exist_ok=True)
        return self._output_dir
    
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
        Generate audio file from text.
        
        Args:
            text: Text to convert to speech (max 2000 chars)
            voice: Voice key from YARNGPT_VOICES or voice name directly
            
        Returns:
            dict with 'success', 'url', 'filename', 'provider'
        """
        if not self.is_available:
            return {
                'success': False,
                'url': '',
                'filename': '',
                'provider': '',
                'error': 'TTS service not available'
            }
        
        if not text or len(text.strip()) < 2:
            return {
                'success': False,
                'url': '',
                'filename': '',
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
            'url': '',
            'filename': '',
            'provider': '',
            'error': 'All TTS providers failed'
        }
    
    def _yarngpt_generate(self, text: str, voice: str) -> dict:
        """
        Generate audio using official YarnGPT API.
        
        API: https://yarngpt.ai/api/v1/tts
        Limit: 80 requests/day
        """
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
                stream=True,
                timeout=60  # May take time for longer text
            )
            
            if response.status_code == 200:
                # Stream and save audio content
                filename = f"tts_{uuid.uuid4().hex[:12]}.mp3"
                filepath = self.output_dir / filename
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                url = f"{settings.MEDIA_URL}tts/{filename}"
                
                return {
                    'success': True,
                    'url': url,
                    'filename': filename,
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
                    'url': '',
                    'filename': '',
                    'provider': 'yarngpt',
                    'error': error_msg
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'url': '',
                'filename': '',
                'provider': 'yarngpt',
                'error': 'Request timed out'
            }
        except Exception as e:
            logger.error(f"YarnGPT TTS error: {e}")
            return {
                'success': False,
                'url': '',
                'filename': '',
                'provider': 'yarngpt',
                'error': str(e)
            }
    
    def _gemini_tts_generate(self, text: str, language: str) -> dict:
        """Generate audio using Gemini TTS (high quality fallback)."""
        try:
            from google import genai
            
            api_key = key_manager.get_gemini_key()
            if not api_key:
                return {
                    'success': False,
                    'url': '',
                    'filename': '',
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
                                "voice_name": "Kore"  # Natural sounding voice
                            }
                        }
                    }
                }
            )
            
            # Save audio
            if response.candidates and response.candidates[0].content.parts:
                audio_data = response.candidates[0].content.parts[0].inline_data.data
                
                filename = f"tts_{uuid.uuid4().hex[:12]}.wav"
                filepath = self.output_dir / filename
                
                with open(filepath, 'wb') as f:
                    f.write(audio_data)
                
                url = f"{settings.MEDIA_URL}tts/{filename}"
                
                return {
                    'success': True,
                    'url': url,
                    'filename': filename,
                    'provider': 'gemini_tts',
                    'error': ''
                }
            
            return {
                'success': False,
                'url': '',
                'filename': '',
                'provider': 'gemini_tts',
                'error': 'No audio in response'
            }
            
        except Exception as e:
            logger.error(f"Gemini TTS error: {e}")
            return {
                'success': False,
                'url': '',
                'filename': '',
                'provider': 'gemini_tts',
                'error': str(e)
            }
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Remove TTS files older than max_age_hours."""
        import time
        
        try:
            now = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filepath in self.output_dir.glob('*.*'):
                if filepath.suffix in ('.mp3', '.wav') and now - filepath.stat().st_mtime > max_age_seconds:
                    filepath.unlink()
                    logger.info(f"Cleaned up old TTS file: {filepath.name}")
        except Exception as e:
            logger.error(f"TTS cleanup error: {e}")


# Singleton instance
tts_service = TTSService()
