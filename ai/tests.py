"""
Unit tests for the AI app.
Tests AI models, chat functionality, and archive analysis.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from ai.models import ChatSession, ChatMessage, ArchiveAnalysis
from archives.models import Archive

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
        
        # Mock chat_service.chat to avoid API calls during tests
        from unittest.mock import patch
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
            self.assertEqual(data['session_id'], 0) # Should be dummy 0
            
            # Verify no models were created
            self.assertEqual(ChatSession.objects.count(), 0)
            self.assertEqual(ChatMessage.objects.count(), 0)

    def test_chat_send_with_history(self):
        """Test chat_send correctly passes history to the service."""
        self.client.login(username='testuser', password='testpass123')
        
        from unittest.mock import patch
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
        from django.core.files.uploadedfile import SimpleUploadedFile
        from unittest.mock import patch
        
        self.client.login(username='testuser', password='testpass123')
        
        # Create archive with a real SimpleUploadedFile
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
            
            # Verify no ArchiveAnalysis record was created
            # Verify no ArchiveAnalysis record was created
            self.assertEqual(ArchiveAnalysis.objects.count(), 0)


from unittest.mock import patch
class TTSServiceTests(TestCase):
    """Tests for the TTS service and fallback logic."""
    
    def setUp(self):
        from ai.services.tts_service import TTSService
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
    @patch('ai.services.tts_service.TTSService._gemini_generate')
    def test_yarngpt_timeout_fallback(self, mock_gemini, mock_post):
        """Test that YarnGPT timeout triggers Gemini fallback."""
        # Mock YarnGPT timeout error
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout("Operation timed out")
        
        # Mock Gemini success
        mock_gemini.return_value = {
            'success': True, 
            'audio_bytes': b"gemini audio", 
            'provider': 'gemini'
        }
        
        with self.settings(YARNGPT_API_KEY='test_key'):
            # Trigger audio generation
            result = self.tts.generate_audio("Hello world")
            
            # Verify fallback happened
            self.assertTrue(result['success'])
            self.assertEqual(result['provider'], 'gemini')
            self.assertEqual(mock_post.call_count, 2) # Should retry once before failing over
            mock_gemini.assert_called_once()

