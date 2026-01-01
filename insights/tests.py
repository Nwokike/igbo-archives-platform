"""
Unit tests for the insights app.
Tests insight CRUD operations, edit suggestions, and model functionality.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from insights.models import InsightPost, EditSuggestion

User = get_user_model()


class InsightPostModelTests(TestCase):
    """Tests for the InsightPost model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
    
    def test_create_insight(self):
        """Test creating an insight post."""
        insight = InsightPost.objects.create(
            title='Test Insight',
            slug='test-insight',
            content_json={'blocks': []},
            author=self.user
        )
        
        self.assertEqual(insight.title, 'Test Insight')
        self.assertEqual(insight.slug, 'test-insight')
        self.assertEqual(insight.author, self.user)
        self.assertEqual(str(insight), 'Test Insight')
    
    def test_insight_default_values(self):
        """Test insight default field values."""
        insight = InsightPost.objects.create(
            title='Test',
            slug='test',
            author=self.user
        )
        
        self.assertFalse(insight.is_published)
        self.assertFalse(insight.is_approved)
        self.assertFalse(insight.pending_approval)
        self.assertFalse(insight.posted_to_social)
    
    def test_insight_content_property(self):
        """Test content property returns content_json when available."""
        content_data = {'blocks': [{'type': 'paragraph', 'data': {'text': 'Hello'}}]}
        insight = InsightPost.objects.create(
            title='Test',
            slug='test',
            content_json=content_data,
            author=self.user
        )
        
        self.assertEqual(insight.content, content_data)
    
    def test_insight_content_fallback_to_legacy(self):
        """Test content property falls back to legacy_content."""
        insight = InsightPost.objects.create(
            title='Test',
            slug='test',
            content_json=None,
            legacy_content='<p>Legacy HTML content</p>',
            author=self.user
        )
        
        self.assertEqual(insight.content, '<p>Legacy HTML content</p>')
    
    def test_insight_ordering(self):
        """Test insights are ordered by created_at descending."""
        insight1 = InsightPost.objects.create(
            title='First',
            slug='first',
            author=self.user
        )
        insight2 = InsightPost.objects.create(
            title='Second',
            slug='second',
            author=self.user
        )
        
        insights = list(InsightPost.objects.all())
        
        # Most recent first
        self.assertEqual(insights[0], insight2)
        self.assertEqual(insights[1], insight1)
    
    def test_insight_published_filter(self):
        """Test filtering for published insights."""
        published = InsightPost.objects.create(
            title='Published',
            slug='published',
            author=self.user,
            is_published=True,
            is_approved=True
        )
        draft = InsightPost.objects.create(
            title='Draft',
            slug='draft',
            author=self.user,
            is_published=False
        )
        
        published_insights = InsightPost.objects.filter(is_published=True, is_approved=True)
        self.assertEqual(published_insights.count(), 1)
        self.assertEqual(published_insights.first(), published)
    
    def test_insight_pending_approval(self):
        """Test pending approval workflow."""
        insight = InsightPost.objects.create(
            title='Pending',
            slug='pending',
            author=self.user,
            pending_approval=True,
            submitted_at=timezone.now()
        )
        
        self.assertTrue(insight.pending_approval)
        self.assertIsNotNone(insight.submitted_at)


class EditSuggestionModelTests(TestCase):
    """Tests for the EditSuggestion model."""
    
    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
        self.suggester = User.objects.create_user(
            username='suggester',
            email='suggester@example.com',
            password='testpass123'
        )
        self.insight = InsightPost.objects.create(
            title='Test Insight',
            slug='test-insight',
            author=self.author
        )
    
    def test_create_suggestion(self):
        """Test creating an edit suggestion."""
        suggestion = EditSuggestion.objects.create(
            post=self.insight,
            suggested_by=self.suggester,
            suggestion_text='Please fix the typo in paragraph 2.'
        )
        
        self.assertEqual(suggestion.post, self.insight)
        self.assertEqual(suggestion.suggested_by, self.suggester)
        self.assertFalse(suggestion.is_approved)
        self.assertFalse(suggestion.is_rejected)
    
    def test_suggestion_str(self):
        """Test suggestion string representation."""
        suggestion = EditSuggestion.objects.create(
            post=self.insight,
            suggested_by=self.suggester,
            suggestion_text='Some suggestion'
        )
        
        self.assertIn(self.insight.title, str(suggestion))
    
    def test_suggestion_approval_workflow(self):
        """Test suggestion approval workflow."""
        suggestion = EditSuggestion.objects.create(
            post=self.insight,
            suggested_by=self.suggester,
            suggestion_text='Fix typo'
        )
        
        suggestion.is_approved = True
        suggestion.save()
        
        suggestion.refresh_from_db()
        self.assertTrue(suggestion.is_approved)
    
    def test_suggestion_rejection_workflow(self):
        """Test suggestion rejection workflow."""
        suggestion = EditSuggestion.objects.create(
            post=self.insight,
            suggested_by=self.suggester,
            suggestion_text='Not a good suggestion'
        )
        
        suggestion.is_rejected = True
        suggestion.save()
        
        suggestion.refresh_from_db()
        self.assertTrue(suggestion.is_rejected)


class InsightViewAuthTests(TestCase):
    """Tests for insight view authentication."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_requires_login(self):
        """Test that creating insights requires authentication."""
        response = self.client.get('/insights/create/', follow=True)
        
        # Should end up at login page
        self.assertIn('login', response.request['PATH_INFO'])
    
    def test_edit_requires_ownership(self):
        """Test that editing requires ownership."""
        insight = InsightPost.objects.create(
            title='Test',
            slug='test',
            author=self.user,
            is_published=True,
            is_approved=True
        )
        
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        self.client.login(username='other', password='testpass123')
        
        response = self.client.get(f'/insights/{insight.slug}/edit/', follow=True)
        self.assertEqual(response.status_code, 404)


class InsightContentTests(TestCase):
    """Tests for insight content handling."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
    
    def test_json_content_storage(self):
        """Test that JSON content is stored correctly."""
        content = {
            'blocks': [
                {'type': 'paragraph', 'data': {'text': 'Hello World'}},
                {'type': 'header', 'data': {'text': 'A Header', 'level': 2}}
            ]
        }
        
        insight = InsightPost.objects.create(
            title='Content Test',
            slug='content-test',
            content_json=content,
            author=self.user
        )
        
        insight.refresh_from_db()
        self.assertEqual(insight.content_json, content)
    
    def test_tags_support(self):
        """Test that tags work correctly."""
        insight = InsightPost.objects.create(
            title='Tagged',
            slug='tagged',
            author=self.user
        )
        
        insight.tags.add('igbo', 'culture', 'history')
        
        self.assertEqual(insight.tags.count(), 3)
        self.assertTrue(insight.tags.filter(name='igbo').exists())
