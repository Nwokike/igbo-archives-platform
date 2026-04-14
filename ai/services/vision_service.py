"""
Vision Service for Igbo Archives.
Advanced image analysis using LiteLLM Router and models.yaml.
"""
import logging
import os
import yaml
import base64
from pathlib import Path
from litellm import Router
from .url_validators import is_safe_url

logger = logging.getLogger(__name__)


class VisionService:
    """Advanced vision analysis using LiteLLM."""
    
    ANALYSIS_PROMPTS = {
        'describe': """You are analyzing an image for the Igbo Archives.
Provide a comprehensive description including:
1. **Visual Elements**
2. **Cultural Significance**
3. **Historical Context**
4. **Text/Inscriptions**
5. **Preservation Value**

Format in Markdown with headers and bullet points.""",

        'historical': """Analyze this image for its historical significance within Igbo culture.
Discuss: Time period, historical events, cultural continuity.
Format in Markdown.""",

        'cultural': """Analyze the cultural significance for Igbo heritage.
Examine: Traditional practices, symbols (uli, nsibidi), worldview.
Format in Markdown.""",

        'translation': """Transcribe and translate any visible text.
Provide: Original text, English translation, cultural context.
Format in Markdown.""",

        'artifact': """Analyze this cultural artifact for documentation.
Document: Type, materials, craft, origin, ceremonial purpose.
Format in Markdown."""
    }
    
    def __init__(self):
        # Load models from YAML
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models.yaml')
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.router = Router(
                model_list=config.get('model_list', []),
                **(config.get('router_settings', {}))
            )
            logger.info("Vision Router initialized")
        except Exception as e:
            logger.error(f"Failed to load models.yaml in VisionService: {e}")
            self.router = None

    @property
    def is_available(self):
        return self.router is not None
    
    def analyze(self, image_path: str, analysis_type: str = 'describe', archive_context: dict = None) -> dict:
        """Analyze local image via LiteLLM with grounding."""
        if not self.is_available:
            return {'success': False, 'content': 'Vision service unavailable.'}
        
        try:
            path = Path(image_path)
            if not path.exists():
                return {'success': False, 'content': 'Image not found.'}
            
            with open(path, 'rb') as f:
                image_data = f.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            suffix = path.suffix.lower()
            mime_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
            mime_type = mime_types.get(suffix, 'image/jpeg')
            
            # Build grounding
            from .chat_service import web_search
            meta_str = f"Archive Metadata: {archive_context}" if archive_context else ""
            web_context = ""
            if archive_context and archive_context.get('title'):
                search_query = f"{archive_context['title']} Igbo cultural heritage"
                web_context = web_search(search_query, max_results=3)
            
            analysis_prompt = self.ANALYSIS_PROMPTS.get(analysis_type, self.ANALYSIS_PROMPTS['describe'])
            
            full_instructions = (
                f"### CONTEXT:\n{meta_str}\n{web_context}\n\n"
                f"### PROMPT:\n{analysis_prompt}\n"
            )
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_instructions},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                    ]
                }
            ]
            
            response = self.router.completion(
                model="vision-primary",
                messages=messages
            )
            
            return {'success': True, 'content': response.choices[0].message.content}
            
        except Exception as e:
            logger.error(f"LiteLLM Vision error: {e}")
            return {'success': False, 'content': 'Image analysis failed.'}

    def analyze_url(self, image_url: str, analysis_type: str = 'describe') -> dict:
        """Analyze image from URL via LiteLLM."""
        if not self.is_available or not is_safe_url(image_url):
            return {'success': False, 'content': 'Service unavailable or unsafe URL.'}
        
        try:
            prompt = self.ANALYSIS_PROMPTS.get(analysis_type, self.ANALYSIS_PROMPTS['describe'])
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
            
            response = self.router.completion(
                model="vision-primary",
                messages=messages
            )
            return {'success': True, 'content': response.choices[0].message.content}
        except Exception as e:
            logger.error(f"Vision URL error: {e}")
            return {'success': False, 'content': 'URL analysis failed.'}


vision_service = VisionService()
