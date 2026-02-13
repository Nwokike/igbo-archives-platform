"""
Vision Service for Igbo Archives.
Advanced image analysis for cultural artifacts and documents.

Migrated to google-genai SDK (2026).
"""
import logging
from pathlib import Path
from .key_manager import key_manager
from .url_validators import is_safe_url

logger = logging.getLogger(__name__)


class VisionService:
    """Advanced vision analysis for cultural heritage content."""
    
    MODEL = 'gemini-2.5-flash' 
    
    ANALYSIS_PROMPTS = {
        'describe': """You are analyzing an image for the Igbo Archives, a platform dedicated to preserving Igbo cultural heritage.

Provide a comprehensive description including:
1. **Visual Elements**: What is depicted, colors, composition, condition
2. **Cultural Significance**: Any Igbo cultural elements, symbols, or traditions visible
3. **Historical Context**: Estimated era, historical significance if apparent
4. **Text/Inscriptions**: Transcribe any visible text, translate if in Igbo
5. **Preservation Value**: Why this image matters for cultural preservation

Be detailed but concise. **Always format your response in Markdown** (use ## headers, **bold**, and bullet points where appropriate). Use Igbo terms where relevant with English explanations.""",

        'historical': """Analyze this image for its historical significance within Igbo culture and Nigerian history.

Discuss:
1. The apparent time period and historical context
2. Connections to known historical events or periods
3. How this relates to pre-colonial, colonial, or post-independence Igbo history
4. Changes or continuities this represents
5. Historical figures or events it might relate to

Provide scholarly analysis suitable for an archives platform. **Format your response in Markdown**.""",

        'cultural': """Analyze the cultural significance of this image for Igbo heritage.

Examine:
1. Traditional practices, customs, or ceremonies depicted
2. Symbolic meanings of elements shown (uli patterns, masquerade designs, etc.)
3. Connections to Igbo worldview, beliefs, and values
4. Regional variations if identifiable (Anambra, Enugu, Imo, etc.)
5. How this contributes to understanding and preserving Igbo culture

Use Igbo terminology where appropriate with explanations. **Format your response in Markdown**.""",

        'translation': """Analyze any text visible in this image.

Provide:
1. Exact transcription of all visible text
2. If in Igbo: Full English translation
3. If in English or other languages: Note the language
4. Cultural context and significance of the text
5. Any proverbs, sayings, or notable phrases

If no text is visible, describe what is shown instead. **Format your response in Markdown**.""",

        'artifact': """Analyze this cultural artifact for documentation purposes.

Document:
1. Type of artifact (pottery, textile, metalwork, carving, etc.)
2. Materials and craftsmanship techniques visible
3. Decorative elements and their meanings
4. Probable origin, age, and regional style
5. Cultural/ceremonial purpose
6. Condition and preservation considerations

This analysis is for archival documentation. **Format your response in Markdown**."""
    }
    
    def __init__(self):
        self._clients = {}
    
    def _get_client(self, api_key):
        """Get or create vision client."""
        if api_key not in self._clients:
            try:
                from google import genai
                self._clients[api_key] = genai.Client(api_key=api_key)
            except ImportError:
                logger.error("google-genai not installed. Run: pip install google-genai")
                return None
            except Exception as e:
                logger.error(f"Vision client error: {e}")
                return None
        return self._clients[api_key]
    
    @property
    def is_available(self):
        return key_manager.has_gemini
    
    def analyze(self, image_path: str, analysis_type: str = 'describe') -> dict:
        """
        Analyze an image with advanced AI vision and web grounding.
        
        Args:
            image_path: Path to image file
            analysis_type: 'describe', 'historical', 'cultural', 'translation', 'artifact'
        
        Returns:
            {'success': bool, 'content': str}
        """
        if not self.is_available:
            return {
                'success': False,
                'content': 'Image analysis is being configured. Please check back soon!'
            }
        
        # Try each available key
        for _ in range(len(key_manager.gemini_keys)):
            api_key = key_manager.get_gemini_key()
            if not api_key:
                break
            
            client = self._get_client(api_key)
            if not client:
                continue
            
            try:
                from google.genai import types
                
                path = Path(image_path)
                if not path.exists():
                    return {'success': False, 'content': 'Image not found.'}
                
                with open(path, 'rb') as f:
                    image_data = f.read()
                
                # Determine MIME type
                suffix = path.suffix.lower()
                mime_types = {
                    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                    '.png': 'image/png', '.gif': 'image/gif',
                    '.webp': 'image/webp', '.heic': 'image/heic',
                }
                mime_type = mime_types.get(suffix, 'image/jpeg')
                
                # STEP 1: Identification (Observation)
                # Ask the model to identify the main subject and keywords for search
                id_prompt = "Identify the main Igbo cultural artifact, person, or scene in this image. Return ONLY 3-5 keywords separated by commas that would be effective for a web search to find more context about this item."
                
                id_response = client.models.generate_content(
                    model=self.MODEL,
                    contents=[
                        types.Part.from_bytes(data=image_data, mime_type=mime_type),
                        id_prompt
                    ]
                )
                
                keywords = id_response.text.strip().strip('.')
                logger.info(f"Vision ID keywords: {keywords}")
                
                # STEP 2: Web Search Grounding
                from .chat_service import web_search
                web_context = ""
                if keywords and len(keywords) > 3:
                    search_query = f"{keywords} Igbo culture history"
                    web_context = web_search(search_query, max_results=3)
                
                # STEP 3: Final Grounded Analysis
                prompt = self.ANALYSIS_PROMPTS.get(analysis_type, self.ANALYSIS_PROMPTS['describe'])
                
                final_parts = [
                    types.Part.from_bytes(data=image_data, mime_type=mime_type),
                    f"PROMPT: {prompt}"
                ]
                
                if web_context:
                    grounding_instruction = (
                        f"\n\n---\n## WEB SEARCH CONTEXT (Use this to avoid hallucination):\n{web_context}\n---\n\n"
                        "IMPORTANT: Use the information above to provide factual context about the item depicted. "
                        "If the web search contradicts your visual observation, prioritize the web search for facts like dates, names, and regional origins."
                    )
                    final_parts.append(grounding_instruction)
                
                response = client.models.generate_content(
                    model=self.MODEL,
                    contents=final_parts
                )
                
                return {
                    'success': True,
                    'content': response.text
                }
                
            except Exception as e:
                error_str = str(e).lower()
                if any(x in error_str for x in ['rate', 'limit', 'quota', '429']):
                    key_manager.mark_rate_limited('gemini', api_key, 3600)
                    continue
                logger.error(f"Vision error: {e}")
                return {'success': False, 'content': 'Image analysis failed. Please try again.'}
        
        return {
            'success': False,
            'content': 'Image analysis is experiencing high demand. Please try again shortly.'
        }
    
    def analyze_url(self, image_url: str, analysis_type: str = 'describe') -> dict:
        """Analyze image from URL (with SSRF protection)."""
        if not self.is_available:
            return {'success': False, 'content': 'Vision not available.'}
        
        # SSRF protection — block private IPs, metadata endpoints, non-HTTP schemes
        if not is_safe_url(image_url):
            return {'success': False, 'content': 'Invalid or blocked URL.'}
        
        prompt = self.ANALYSIS_PROMPTS.get(analysis_type, self.ANALYSIS_PROMPTS['describe'])
        
        for _ in range(len(key_manager.gemini_keys)):
            api_key = key_manager.get_gemini_key()
            if not api_key:
                break
            
            client = self._get_client(api_key)
            if not client:
                continue
            
            try:
                import requests
                from google.genai import types
                
                response = requests.get(image_url, timeout=15)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', 'image/jpeg')
                
                result = client.models.generate_content(
                    model=self.MODEL,
                    contents=[
                        types.Part.from_bytes(data=response.content, mime_type=content_type.split(';')[0]),
                        prompt
                    ]
                )
                return {'success': True, 'content': result.text}
                
            except Exception as e:
                error_str = str(e).lower()
                if 'rate' in error_str or 'limit' in error_str:
                    key_manager.mark_rate_limited('gemini', api_key, 3600)
                    continue
                logger.error(f"Vision URL analysis error: {e}")
                return {'success': False, 'content': 'URL image analysis failed.'}
        
        return {'success': False, 'content': 'Service temporarily unavailable.'}


# Singleton
vision_service = VisionService()

