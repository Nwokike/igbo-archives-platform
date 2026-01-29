"""
Speech-to-Text Service for Igbo Archives.
Uses NaijaLingo ASR for Nigerian languages (Igbo, Yoruba, Hausa, Nigerian English).

NaijaLingo ASR: https://pypi.org/project/naijalingo-asr/
- Specifically trained for Nigerian languages
- Uses faster-whisper (CTranslate2 backend) - efficient
- No external API needed - runs locally
- Supports: ig (Igbo), yo (Yoruba), ha (Hausa), en (Nigerian English)

Install: pip install naijalingo-asr[audio]
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class STTService:
    """
    Speech-to-Text service using NaijaLingo ASR.
    
    Specifically designed for Nigerian languages:
    - ig: Igbo
    - yo: Yoruba  
    - ha: Hausa
    - en: Nigerian-accented English
    
    Runs locally - no API key needed, no rate limits.
    """
    
    SUPPORTED_LANGUAGES = {
        'ig': 'Igbo',
        'yo': 'Yoruba',
        'ha': 'Hausa',
        'en': 'Nigerian English',
    }
    
    def __init__(self):
        self._transcribe_fn = None
        self._is_available = None
    
    @property
    def is_available(self) -> bool:
        """Check if NaijaLingo ASR is installed and available."""
        if self._is_available is None:
            try:
                from naijalingo_asr import transcribe
                self._transcribe_fn = transcribe
                self._is_available = True
                logger.info("NaijaLingo ASR available for Nigerian language STT")
            except ImportError:
                self._is_available = False
                logger.warning(
                    "NaijaLingo ASR not installed. "
                    "Install with: pip install naijalingo-asr[audio]"
                )
        return self._is_available
    
    def transcribe(
        self, 
        audio_file_path: str, 
        language: str = 'ig',
        device: str = 'auto'
    ) -> dict:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Language code - 'ig' (Igbo), 'yo' (Yoruba), 
                     'ha' (Hausa), 'en' (Nigerian English)
            device: 'auto' (default), 'cpu', or 'cuda'
            
        Returns:
            dict with 'success', 'text', 'language', 'error'
        """
        if not self.is_available:
            return {
                'success': False,
                'text': '',
                'language': language,
                'error': 'STT not available. Install: pip install naijalingo-asr[audio]'
            }
        
        # Validate language
        if language not in self.SUPPORTED_LANGUAGES:
            return {
                'success': False,
                'text': '',
                'language': language,
                'error': f"Unsupported language. Use: {', '.join(self.SUPPORTED_LANGUAGES.keys())}"
            }
        
        # Validate file exists
        if not os.path.exists(audio_file_path):
            return {
                'success': False,
                'text': '',
                'language': language,
                'error': 'Audio file not found'
            }
        
        try:
            # Transcribe using NaijaLingo ASR
            text = self._transcribe_fn(
                audio_file_path,
                language=language,
                device=device
            )
            
            if text:
                return {
                    'success': True,
                    'text': text.strip(),
                    'language': language,
                    'language_name': self.SUPPORTED_LANGUAGES[language],
                    'error': ''
                }
            else:
                return {
                    'success': False,
                    'text': '',
                    'language': language,
                    'error': 'No speech detected in audio'
                }
                
        except Exception as e:
            logger.error(f"NaijaLingo ASR transcription error: {e}")
            return {
                'success': False,
                'text': '',
                'language': language,
                'error': str(e)
            }
    
    def get_supported_languages(self) -> dict:
        """Get dict of supported language codes and names."""
        return self.SUPPORTED_LANGUAGES.copy()


# Singleton instance
stt_service = STTService()
