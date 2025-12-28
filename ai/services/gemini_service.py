"""
Gemini AI Service for Igbo Archives.
Handles image analysis, chat, and multimodal tasks with multi-key rotation.
Uses Gemini 2.0 Flash (best free model).
"""
import logging
from django.conf import settings
from .key_manager import key_manager

logger = logging.getLogger(__name__)

# System prompt for chat (same as Groq for consistency)
SYSTEM_PROMPT = """You are Igbo Archives AI, a knowledgeable and friendly assistant specialized in Igbo culture, history, language, and heritage. Be respectful, accurate, and encourage cultural preservation. Use Igbo words where appropriate with explanations."""


class GeminiService:
    """Service for interacting with Google Gemini API with key rotation."""
    
    # Best free Gemini models
    FLASH_MODEL = 'gemini-2.0-flash'  # Best speed/quality ratio
    PRO_MODEL = 'gemini-1.5-pro'       # Best quality (higher limits)
    
    def __init__(self):
        self._models = {}  # Cache models per key
    
    def _get_model(self, api_key, model_name=None):
        """Get or create Gemini model for a key."""
        model_name = model_name or self.FLASH_MODEL
        cache_key = f"{api_key}:{model_name}"
        
        if cache_key not in self._models:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._models[cache_key] = genai.GenerativeModel(model_name)
            except ImportError:
                logger.error("google-generativeai package not installed")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Gemini model: {e}")
                return None
        return self._models[cache_key]
    
    @property
    def is_available(self):
        """Check if service is configured and available."""
        return key_manager.has_gemini
    
    def chat(self, messages: list, session_context: str = '') -> dict:
        """
        Chat completion using Gemini Flash with key rotation.
        """
        if not self.is_available:
            return {
                'success': False,
                'content': 'AI service is not configured.',
                'tokens_used': 0,
                'model': '',
                'provider': 'gemini'
            }
        
        # Build prompt from messages
        prompt_parts = [SYSTEM_PROMPT]
        if session_context:
            prompt_parts.append(f"Context: {session_context}")
        
        for msg in messages[-10:]:
            role = "User" if msg['role'] == 'user' else "Assistant"
            prompt_parts.append(f"{role}: {msg['content']}")
        
        prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
        
        # Try each available key
        for _ in range(key_manager.gemini_key_count):
            api_key = key_manager.get_gemini_key()
            if not api_key:
                break
            
            model = self._get_model(api_key)
            if not model:
                continue
            
            try:
                response = model.generate_content(prompt)
                
                return {
                    'success': True,
                    'content': response.text,
                    'tokens_used': 0,  # Gemini doesn't expose this easily
                    'model': self.FLASH_MODEL,
                    'provider': 'gemini'
                }
                
            except Exception as e:
                error_str = str(e).lower()
                if 'quota' in error_str or 'rate' in error_str or 'limit' in error_str:
                    key_manager.mark_key_rate_limited('gemini', api_key, 3600)
                    logger.warning(f"Gemini key rate limited, trying next...")
                    continue
                else:
                    logger.error(f"Gemini chat error: {e}")
                    return {
                        'success': False,
                        'content': f'Sorry, I encountered an error: {str(e)}',
                        'tokens_used': 0,
                        'model': self.FLASH_MODEL,
                        'provider': 'gemini'
                    }
        
        return {
            'success': False,
            'content': 'All AI services are currently rate limited. Please try again later.',
            'tokens_used': 0,
            'model': '',
            'provider': 'gemini'
        }
    
    def analyze_image(self, image_path: str, analysis_type: str = 'description') -> dict:
        """
        Analyze an image using Gemini Vision with key rotation.
        """
        if not self.is_available:
            return {
                'success': False,
                'content': 'Image analysis service is not configured.',
                'model': ''
            }
        
        prompts = {
            'description': """Analyze this image and provide a detailed description. Include:
1. What is depicted in the image
2. Notable visual elements, colors, and composition
3. Any text visible in the image
4. The apparent age or era of the content
5. Cultural or historical significance if apparent

Focus on details that would help preserve and understand this piece of Igbo heritage.""",
            
            'historical': """Analyze this image for its historical context within Igbo culture. Discuss:
1. The apparent time period
2. Historical events or practices it might relate to
3. How it fits into Igbo history
4. Changes this might represent compared to modern times""",
            
            'cultural': """Analyze the cultural significance of this image for Igbo heritage:
1. Cultural practices, traditions, or customs depicted
2. Symbolic meanings of elements shown
3. Connections to Igbo beliefs, values, or worldview
4. How this contributes to understanding Igbo culture""",
            
            'translation': """If there is any text visible in this image:
1. Transcribe the text exactly as shown
2. If in Igbo, provide the English translation
3. Explain any cultural context for the text"""
        }
        
        prompt = prompts.get(analysis_type, prompts['description'])
        
        # Try each available key
        for _ in range(key_manager.gemini_key_count):
            api_key = key_manager.get_gemini_key()
            if not api_key:
                break
            
            model = self._get_model(api_key)
            if not model:
                continue
            
            try:
                from pathlib import Path
                import google.generativeai as genai
                
                path = Path(image_path)
                if not path.exists():
                    return {
                        'success': False,
                        'content': 'Image file not found.',
                        'model': self.FLASH_MODEL
                    }
                
                with open(path, 'rb') as f:
                    image_data = f.read()
                
                suffix = path.suffix.lower()
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp',
                }
                mime_type = mime_types.get(suffix, 'image/jpeg')
                
                image_part = {'mime_type': mime_type, 'data': image_data}
                response = model.generate_content([prompt, image_part])
                
                return {
                    'success': True,
                    'content': response.text,
                    'model': self.FLASH_MODEL
                }
                
            except Exception as e:
                error_str = str(e).lower()
                if 'quota' in error_str or 'rate' in error_str or 'limit' in error_str:
                    key_manager.mark_key_rate_limited('gemini', api_key, 3600)
                    continue
                else:
                    logger.error(f"Gemini image analysis error: {e}")
                    return {
                        'success': False,
                        'content': f'Error analyzing image: {str(e)}',
                        'model': self.FLASH_MODEL
                    }
        
        return {
            'success': False,
            'content': 'All AI services are currently rate limited.',
            'model': ''
        }
    
    def analyze_image_url(self, image_url: str, analysis_type: str = 'description') -> dict:
        """Analyze an image from URL."""
        if not self.is_available:
            return {'success': False, 'content': 'Not configured.', 'model': ''}
        
        prompt = f"Analyze this image for {analysis_type} focusing on Igbo cultural heritage."
        
        for _ in range(key_manager.gemini_key_count):
            api_key = key_manager.get_gemini_key()
            if not api_key:
                break
            
            model = self._get_model(api_key)
            if not model:
                continue
            
            try:
                import requests
                
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', 'image/jpeg')
                image_part = {
                    'mime_type': content_type.split(';')[0],
                    'data': response.content
                }
                
                result = model.generate_content([prompt, image_part])
                
                return {
                    'success': True,
                    'content': result.text,
                    'model': self.FLASH_MODEL
                }
                
            except Exception as e:
                error_str = str(e).lower()
                if 'quota' in error_str or 'rate' in error_str:
                    key_manager.mark_key_rate_limited('gemini', api_key, 3600)
                    continue
                else:
                    logger.error(f"Gemini URL analysis error: {e}")
                    return {'success': False, 'content': str(e), 'model': ''}
        
        return {'success': False, 'content': 'All keys rate limited.', 'model': ''}


# Singleton instance
gemini_service = GeminiService()
