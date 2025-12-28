"""
Text-to-Speech Service for Igbo Archives.
Uses gTTS for generating audio from text.
"""
import logging
import os
import uuid
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Service for text-to-speech generation using gTTS."""
    
    def __init__(self):
        self.output_dir = Path(settings.MEDIA_ROOT) / 'tts'
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_available(self):
        """Check if gTTS is available."""
        try:
            from gtts import gTTS
            return True
        except ImportError:
            return False
    
    def generate_audio(self, text: str, language: str = 'en') -> dict:
        """
        Generate audio file from text.
        
        Args:
            text: Text to convert to speech
            language: Language code ('en' for English, 'ig' for Igbo if supported)
            
        Returns:
            dict with 'success', 'url', 'filename'
        """
        if not self.is_available:
            return {
                'success': False,
                'url': '',
                'filename': '',
                'error': 'TTS service not available. Install gTTS: pip install gTTS'
            }
        
        if not text or len(text.strip()) < 2:
            return {
                'success': False,
                'url': '',
                'filename': '',
                'error': 'Text is too short'
            }
        
        # Limit text length to prevent abuse
        text = text[:5000]
        
        try:
            from gtts import gTTS
            
            # Generate unique filename
            filename = f"tts_{uuid.uuid4().hex[:12]}.mp3"
            filepath = self.output_dir / filename
            
            # gTTS doesn't officially support Igbo, fall back to English
            lang = 'en' if language not in ['en', 'fr', 'es', 'de', 'pt'] else language
            
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(str(filepath))
            
            url = f"{settings.MEDIA_URL}tts/{filename}"
            
            return {
                'success': True,
                'url': url,
                'filename': filename,
                'error': ''
            }
            
        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            return {
                'success': False,
                'url': '',
                'filename': '',
                'error': str(e)
            }
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Remove TTS files older than max_age_hours."""
        import time
        
        try:
            now = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filepath in self.output_dir.glob('*.mp3'):
                if now - filepath.stat().st_mtime > max_age_seconds:
                    filepath.unlink()
                    logger.info(f"Cleaned up old TTS file: {filepath.name}")
        except Exception as e:
            logger.error(f"TTS cleanup error: {e}")


# Singleton instance
tts_service = TTSService()
