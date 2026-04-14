"""
Unit tests for the AI app.
Tests AI views, service integration, and LiteLLM Router fallbacks.
"""
import json
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
import litellm

from archives.models import Archive
from ai.services.chat_service import ChatService
from ai.services.vision_service import VisionService
from ai.services.tts_service import TTSService

User = get_user_model()


class AIViewTests(TestCase):
    """Tests for stateless AI views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_chat_view_requires_login(self):
        """Test chat view requires authentication."""
        response = self.client.get(reverse('ai:chat'), follow=True)
        self.assertIn('login', response.request['PATH_INFO'])
    
    def test_authenticated_user_can_access_chat(self):
        """Test authenticated user can access the chat page."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ai:chat'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ai/chat.html')
    
    def test_chat_send_stateless(self):
        """Test chat_send returns response without saving to DB."""
        self.client.login(username='testuser', password='testpass123')
        
        with patch('ai.views.chat_service.chat') as mocked_chat:
            mocked_chat.return_value = {'success': True, 'content': 'Test response'}
            
            response = self.client.post(
                reverse('ai:chat_send'),
                data=json.dumps({'message': 'Hello AI'}),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])
            self.assertEqual(data['message'], 'Test response')
            self.assertEqual(data['session_id'], 0)

    def test_chat_send_with_history(self):
        """Test chat_send correctly passes history to the service."""
        self.client.login(username='testuser', password='testpass123')
        
        with patch('ai.views.chat_service.chat') as mocked_chat:
            mocked_chat.return_value = {'success': True, 'content': 'Response'}
            
            history = [
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'Hi there!'}
            ]
            
            response = self.client.post(
                reverse('ai:chat_send'),
                data=json.dumps({
                    'message': 'How is it going?',
                    'history': history
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Verify the service was called with the history + current message
            call_args = mocked_chat.call_args[0][0]
            self.assertEqual(len(call_args), 3)
            self.assertEqual(call_args[0]['content'], 'Hello')
            self.assertEqual(call_args[2]['content'], 'How is it going?')

    def test_analyze_archive_stateless(self):
        """Test archive analysis without saving results to DB."""
        self.client.login(username='testuser', password='testpass123')
        
        image_content = b"fake image data"
        uploaded_image = SimpleUploadedFile("test.jpg", image_content, content_type="image/jpeg")
        
        archive = Archive.objects.create(
            title='Test Item',
            is_approved=True,
            uploaded_by=self.user,
            image=uploaded_image
        )
        
        with patch('ai.views.vision_service.analyze') as mocked_vision:
            mocked_vision.return_value = {'success': True, 'content': 'Analysis results'}
            
            response = self.client.post(
                reverse('ai:analyze_archive'),
                data=json.dumps({'archive_id': archive.id, 'type': 'description'}),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])
            self.assertEqual(data['content'], 'Analysis results')


class TTSServiceTests(TestCase):
    """Tests for the TTS service."""
    
    def setUp(self):
        self.tts = TTSService()
    
    @patch('ai.services.tts_service.requests.post')
    def test_yarngpt_success(self, mock_post):
        """Test YarnGPT success path."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b"fake mp3 data"
        
        with self.settings(YARNGPT_API_KEY='test_key'):
            result = self.tts.generate_audio("Hello")
            
            self.assertTrue(result['success'])
            self.assertEqual(result['provider'], 'yarngpt')
            self.assertEqual(result['audio_bytes'], b"fake mp3 data")

    @patch('ai.services.tts_service.requests.post')
    def test_yarngpt_failure_no_fallback(self, mock_post):
        """Test that YarnGPT failure does not trigger Gemini fallback."""
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout("Operation timed out")
        
        with self.settings(YARNGPT_API_KEY='test_key'):
            result = self.tts.generate_audio("Hello world")
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error'], 'Operation timed out')


class RouterIntegrationTests(TestCase):
    """Tests for the LiteLLM Router configuration and behavior."""

    def setUp(self):
        self.chat_service = ChatService()
        self.vision_service = VisionService()

    def test_router_initialization(self):
        """Verify that the router loads models from YAML correctly."""
        self.assertTrue(self.chat_service.is_available)
        self.assertTrue(self.vision_service.is_available)
        
        # Check if chat-primary exists in the model list
        model_names = [m['model_name'] for m in self.chat_service.router.model_list]
        self.assertIn('kimi-k2', model_names)
        self.assertIn('gemma-4-31b-it', model_names)

    @patch('litellm.router.Router.completion')
    def test_chat_calls_primary_model(self, mock_completion):
        """Verify that ChatService calls the 'chat-primary' alias."""
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Hello!"))],
            model="kimi-k2"
        )
        
        messages = [{'role': 'user', 'content': 'Hi'}]
        result = self.chat_service.chat(messages, use_web_search=False)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['content'], "Hello!")
        
        # Verify the router was called with chat-primary
        called_model = mock_completion.call_args[1].get('model')
        self.assertEqual(called_model, 'chat-primary')

    @patch('litellm.router.Router.completion')
    def test_vision_calls_primary_model(self, mock_completion):
        """Verify that VisionService calls the 'vision-primary' alias."""
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="I see a cat."))],
            model="gemma-4-31b-it"
        )
        
        # Mock a small file for analysis
        with patch('ai.services.vision_service.Path.exists', return_value=True), \
             patch('ai.services.vision_service.open', MagicMock()), \
             patch('ai.services.vision_service.base64.b64encode', return_value=b"fake"):
            
            result = self.vision_service.analyze("fake_path.jpg")
            self.assertTrue(result['success'])
            
            # Verify the router was called with vision-primary
            called_model = mock_completion.call_args[1].get('model')
            self.assertEqual(called_model, 'vision-primary')

    def test_fallback_definitions_in_router(self):
        """Verify that fallbacks are correctly registered in the Router instance."""
        fallbacks_list = self.chat_service.router.fallbacks
        fallbacks = {}
        if fallbacks_list:
            for item in fallbacks_list:
                fallbacks.update(item)
        
        # The key is now correctly the alias: 'chat-primary'
        self.assertIn('chat-primary', fallbacks)
        self.assertEqual(fallbacks['chat-primary'][0], 'gemma-4-31b-it')
        
        v_fallbacks_list = self.vision_service.router.fallbacks
        v_fallbacks = {}
        if v_fallbacks_list:
            for item in v_fallbacks_list:
                v_fallbacks.update(item)
                
        # The key is now correctly the alias: 'vision-primary'
        self.assertIn('vision-primary', v_fallbacks)
        self.assertEqual(v_fallbacks['vision-primary'][0], 'gemma-4-26b-a4b-it')
        self.assertEqual(v_fallbacks['vision-primary'][1], 'llama-4-scout')
