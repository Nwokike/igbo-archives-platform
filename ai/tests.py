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


class ChatSessionModelTests(TestCase):
    """Tests for the ChatSession model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_chat_session(self):
        """Test creating a chat session."""
        session = ChatSession.objects.create(
            user=self.user,
            title='Test Conversation'
        )
        
        self.assertEqual(session.title, 'Test Conversation')
        self.assertEqual(session.user, self.user)
        self.assertTrue(session.is_active)
        self.assertIn(self.user.username, str(session))
    
    def test_session_default_title(self):
        """Test session default title."""
        session = ChatSession.objects.create(user=self.user)
        
        self.assertEqual(session.title, 'New Conversation')
    
    def test_session_ordering(self):
        """Test sessions are ordered by updated_at descending."""
        session1 = ChatSession.objects.create(user=self.user, title='First')
        session2 = ChatSession.objects.create(user=self.user, title='Second')
        
        sessions = list(ChatSession.objects.filter(user=self.user))
        
        # Most recently updated first
        self.assertEqual(sessions[0], session2)
        self.assertEqual(sessions[1], session1)
    
    def test_get_context_messages(self):
        """Test getting context messages for AI."""
        session = ChatSession.objects.create(user=self.user)
        
        ChatMessage.objects.create(session=session, role='user', content='Hello')
        ChatMessage.objects.create(session=session, role='assistant', content='Hi there!')
        ChatMessage.objects.create(session=session, role='user', content='How are you?')
        
        context = session.get_context_messages(limit=2)
        
        # Should return last 2 messages in chronological order
        self.assertEqual(len(context), 2)
    
    def test_session_is_active_default(self):
        """Test session is_active defaults to True."""
        session = ChatSession.objects.create(user=self.user)
        
        self.assertTrue(session.is_active)
    
    def test_session_deactivation(self):
        """Test deactivating a session."""
        session = ChatSession.objects.create(user=self.user)
        
        session.is_active = False
        session.save()
        
        session.refresh_from_db()
        self.assertFalse(session.is_active)


class ChatMessageModelTests(TestCase):
    """Tests for the ChatMessage model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.session = ChatSession.objects.create(user=self.user)
    
    def test_create_user_message(self):
        """Test creating a user message."""
        message = ChatMessage.objects.create(
            session=self.session,
            role='user',
            content='What is the history of Igbo culture?'
        )
        
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.session, self.session)
        self.assertIn('user:', str(message))
    
    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        message = ChatMessage.objects.create(
            session=self.session,
            role='assistant',
            content='Igbo culture has a rich history...',
            model_used='gemini-pro'
        )
        
        self.assertEqual(message.role, 'assistant')
        self.assertEqual(message.model_used, 'gemini-pro')
    
    def test_message_ordering(self):
        """Test messages are ordered by created_at ascending."""
        msg1 = ChatMessage.objects.create(session=self.session, role='user', content='First')
        msg2 = ChatMessage.objects.create(session=self.session, role='assistant', content='Second')
        
        messages = list(self.session.messages.all())
        
        # Oldest first
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)
    
    def test_message_role_choices(self):
        """Test all valid role choices."""
        roles = ['user', 'assistant', 'system']
        for role in roles:
            message = ChatMessage.objects.create(
                session=self.session,
                role=role,
                content=f'{role} message'
            )
            self.assertEqual(message.role, role)
    
    def test_tokens_used_tracking(self):
        """Test tokens_used field."""
        message = ChatMessage.objects.create(
            session=self.session,
            role='assistant',
            content='Response',
            tokens_used=150
        )
        
        self.assertEqual(message.tokens_used, 150)


class ArchiveAnalysisModelTests(TestCase):
    """Tests for the ArchiveAnalysis model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.archive = Archive.objects.create(
            title='Historical Photo',
            description='An old photograph',
            archive_type='image',
            uploaded_by=self.user,
            is_approved=True
        )
    
    def test_create_analysis(self):
        """Test creating an archive analysis."""
        analysis = ArchiveAnalysis.objects.create(
            archive=self.archive,
            user=self.user,
            analysis_type='description',
            content='This image shows a traditional Igbo compound...',
            model_used='gemini-vision'
        )
        
        self.assertEqual(analysis.archive, self.archive)
        self.assertEqual(analysis.analysis_type, 'description')
        self.assertIn(self.archive.title, str(analysis))
    
    def test_analysis_types(self):
        """Test all analysis type choices."""
        types = ['description', 'historical', 'cultural', 'translation']
        for i, analysis_type in enumerate(types):
            analysis = ArchiveAnalysis.objects.create(
                archive=self.archive,
                user=self.user,
                analysis_type=analysis_type,
                content=f'{analysis_type} analysis',
                model_used='gemini-pro'
            )
            self.assertEqual(analysis.analysis_type, analysis_type)
    
    def test_analysis_ordering(self):
        """Test analyses are ordered by created_at descending."""
        analysis1 = ArchiveAnalysis.objects.create(
            archive=self.archive, user=self.user,
            analysis_type='description', content='First', model_used='model1'
        )
        analysis2 = ArchiveAnalysis.objects.create(
            archive=self.archive, user=self.user,
            analysis_type='historical', content='Second', model_used='model2'
        )
        
        analyses = list(ArchiveAnalysis.objects.all())
        
        # Most recent first
        self.assertEqual(analyses[0], analysis2)
        self.assertEqual(analyses[1], analysis1)
    
    def test_analysis_user_nullable(self):
        """Test analysis user can be null (deleted user)."""
        analysis = ArchiveAnalysis.objects.create(
            archive=self.archive,
            user=None,
            analysis_type='description',
            content='Analysis without user',
            model_used='model'
        )
        
        self.assertIsNone(analysis.user)


class AIViewAuthTests(TestCase):
    """Tests for AI view authentication."""
    
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
    
    def test_new_chat_requires_login(self):
        """Test chat session view requires authentication."""
        response = self.client.get('/ai/chat/', follow=True)
        
        # Should redirect to login
        self.assertIn('login', response.request['PATH_INFO'])
    
    def test_authenticated_user_can_create_session(self):
        """Test authenticated user can create a session."""
        self.client.login(username='testuser', password='testpass123')
        
        session = ChatSession.objects.create(user=self.user, title='Test Chat')
        
        self.assertEqual(session.user, self.user)
        self.assertTrue(ChatSession.objects.filter(user=self.user).exists())
    
    def test_user_can_only_see_own_sessions(self):
        """Test users can only see their own sessions."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        
        ChatSession.objects.create(user=self.user, title='My Session')
        ChatSession.objects.create(user=other_user, title='Other Session')
        
        my_sessions = ChatSession.objects.filter(user=self.user)
        other_sessions = ChatSession.objects.filter(user=other_user)
        
        self.assertEqual(my_sessions.count(), 1)
        self.assertEqual(my_sessions.first().title, 'My Session')
        self.assertEqual(other_sessions.count(), 1)
        self.assertEqual(other_sessions.first().title, 'Other Session')
