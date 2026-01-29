"""
Groq AI Service for Igbo Archives.
Handles chat completions with multi-key rotation and fallback to Gemini.
"""
import logging
from django.conf import settings
from .key_manager import key_manager

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Igbo Archives AI, a knowledgeable and friendly assistant specialized in Igbo culture, history, language, and heritage. You help users:

1. Learn about Igbo traditions, customs, and cultural practices
2. Understand Igbo history and notable historical figures
3. Explore the Igbo language, including translations and explanations
4. Discover Igbo art, music, literature, and folklore
5. Navigate and contribute to the Igbo Archives platform

Guidelines:
- Be respectful and culturally sensitive
- Provide accurate, well-researched information
- When uncertain, acknowledge limitations and suggest further research
- Use Igbo words and phrases where appropriate, with explanations
- Encourage preservation and appreciation of Igbo heritage

Format responses in a clear, readable way using markdown when helpful."""


class GroqService:
    """Service for interacting with Groq API with key rotation."""
    
    CHAT_MODEL = 'moonshotai/kimi-k2-instruct'           
    FAST_MODEL = 'openai/gpt-oss-120b'  
    TITLE_MODEL = 'qwen/qwen3-32b'                       
    FALLBACK_MODEL = 'moonshotai/kimi-k2-instruct-0905'           
    WHISPER_MODEL = 'whisper-large-v3-turbo'             
    
    def __init__(self):
        self.max_tokens = 1024
        self.temperature = 0.7
        self._clients = {}  # Cache clients per key
    
    def _get_client(self, api_key):
        """Get or create Groq client for a key."""
        if api_key not in self._clients:
            try:
                from groq import Groq
                self._clients[api_key] = Groq(api_key=api_key)
            except ImportError:
                logger.error("Groq package not installed")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                return None
        return self._clients[api_key]
    
    @property
    def is_available(self):
        """Check if service is configured and available."""
        return key_manager.has_groq
    
    def chat(self, messages: list, session_context: str = '', use_fast: bool = False) -> dict:
        """
        Send a chat completion request with automatic key rotation.
        Falls back to Gemini if all Groq keys are exhausted.
        """
        if not self.is_available:
            # Fallback to Gemini
            return self._fallback_to_gemini(messages, session_context)
        
        model = self.FAST_MODEL if use_fast else self.CHAT_MODEL
        
        # Try each available key
        for _ in range(key_manager.groq_key_count):
            api_key = key_manager.get_groq_key()
            if not api_key:
                break
            
            client = self._get_client(api_key)
            if not client:
                continue
            
            try:
                full_messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
                if session_context:
                    full_messages[0]['content'] += f"\n\nCurrent context: {session_context}"
                full_messages.extend(messages[-10:])
                
                response = client.chat.completions.create(
                    model=model,
                    messages=full_messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                
                content = response.choices[0].message.content
                tokens = response.usage.total_tokens if response.usage else 0
                
                return {
                    'success': True,
                    'content': content,
                    'tokens_used': tokens,
                    'model': model,
                    'provider': 'groq'
                }
                
            except Exception as e:
                error_str = str(e).lower()
                if 'rate' in error_str or 'limit' in error_str or '429' in error_str:
                    key_manager.mark_key_rate_limited('groq', api_key, 3600)
                    logger.warning(f"Groq key rate limited, trying next...")
                    continue
                else:
                    logger.error(f"Groq chat error: {e}")
                    return {
                        'success': False,
                        'content': f'Sorry, I encountered an error: {str(e)}',
                        'tokens_used': 0,
                        'model': model,
                        'provider': 'groq'
                    }
        
        # All Groq keys exhausted, fallback to Gemini
        logger.info("All Groq keys exhausted, falling back to Gemini")
        return self._fallback_to_gemini(messages, session_context)
    
    def _fallback_to_gemini(self, messages: list, session_context: str = '') -> dict:
        """Fallback to Gemini when Groq is unavailable."""
        from .gemini_service import gemini_service
        
        if not gemini_service.is_available:
            return {
                'success': False,
                'content': 'AI service is temporarily unavailable. Please try again later.',
                'tokens_used': 0,
                'model': '',
                'provider': 'none'
            }
        
        return gemini_service.chat(messages, session_context)
    
    def transcribe(self, audio_file_path: str) -> dict:
        """Transcribe audio using Whisper-large-v3 (STT)."""
        if not self.is_available:
            return {'success': False, 'text': '', 'error': 'Groq not configured'}
        
        for _ in range(key_manager.groq_key_count):
            api_key = key_manager.get_groq_key()
            if not api_key:
                break
            
            client = self._get_client(api_key)
            if not client:
                continue
            
            try:
                with open(audio_file_path, 'rb') as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model=self.WHISPER_MODEL,
                        file=audio_file,
                        response_format='text'
                    )
                
                return {
                    'success': True,
                    'text': transcription,
                    'model': self.WHISPER_MODEL
                }
                
            except Exception as e:
                error_str = str(e).lower()
                if 'rate' in error_str or 'limit' in error_str:
                    key_manager.mark_key_rate_limited('groq', api_key, 3600)
                    continue
                else:
                    logger.error(f"Whisper transcription error: {e}")
                    return {'success': False, 'text': '', 'error': str(e)}
        
        return {'success': False, 'text': '', 'error': 'All API keys exhausted'}
    
    def generate_title(self, first_message: str) -> str:
        """Generate a short title for a chat session using title-optimized model."""
        if not self.is_available:
            return first_message[:50] + '...' if len(first_message) > 50 else first_message
        
        for _ in range(key_manager.groq_key_count):
            api_key = key_manager.get_groq_key()
            if not api_key:
                break
            
            client = self._get_client(api_key)
            if not client:
                continue
            
            try:
                response = client.chat.completions.create(
                    model=self.TITLE_MODEL,
                    messages=[
                        {'role': 'system', 'content': 'Generate a very short title (max 5 words) for this conversation. Return only the title.'},
                        {'role': 'user', 'content': first_message[:200]}
                    ],
                    max_tokens=50,
                    temperature=0.3,
                )
                return response.choices[0].message.content.strip()[:100]
            except Exception as e:
                error_str = str(e).lower()
                if 'rate' in error_str or 'limit' in error_str:
                    key_manager.mark_key_rate_limited('groq', api_key, 3600)
                    continue
                logger.error(f"Title generation error: {e}")
                break
        
        return first_message[:50] + '...' if len(first_message) > 50 else first_message


# Singleton instance
groq_service = GroqService()
