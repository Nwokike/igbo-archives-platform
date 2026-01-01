"""
Unit tests for the core app.
Tests homepage, static pages, contact form, and utility functions.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.conf import settings
from unittest.mock import patch, MagicMock
from archives.models import Archive, Category

User = get_user_model()


class HomePageTests(TestCase):
    """Tests for the homepage view."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', slug='test-category')
    
    def test_homepage_loads(self):
        """Test that homepage loads successfully."""
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_homepage_shows_approved_archives(self):
        """Test that only approved archives are fetched for homepage."""
        from core.views import get_all_approved_archive_ids
        from django.core.cache import cache
        
        cache.clear()
        
        approved = Archive.objects.create(
            title='Approved Archive',
            description='Test description',
            archive_type='image',
            uploaded_by=self.user,
            is_approved=True
        )
        unapproved = Archive.objects.create(
            title='Unapproved Archive',
            description='Test description',
            archive_type='image',
            uploaded_by=self.user,
            is_approved=False
        )
        
        # Test the helper function directly
        approved_ids = get_all_approved_archive_ids()
        
        self.assertIn(approved.id, approved_ids)
        self.assertNotIn(unapproved.id, approved_ids)


class StaticPageTests(TestCase):
    """Tests for static informational pages."""
    
    def setUp(self):
        self.client = Client()
    
    def test_about_page_loads(self):
        """Test that about page loads successfully."""
        response = self.client.get('/about/', follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_terms_page_loads(self):
        """Test that terms of service page loads successfully."""
        response = self.client.get('/terms/', follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_privacy_page_loads(self):
        """Test that privacy policy page loads successfully."""
        response = self.client.get('/privacy/', follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_copyright_page_loads(self):
        """Test that copyright policy page loads successfully."""
        response = self.client.get('/copyright/', follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_donate_page_loads(self):
        """Test that donate page loads successfully."""
        response = self.client.get('/donate/', follow=True)
        self.assertEqual(response.status_code, 200)


class ContactFormTests(TestCase):
    """Tests for the contact form functionality."""
    
    def setUp(self):
        self.client = Client()
    
    def test_contact_page_loads(self):
        """Test that contact page loads successfully."""
        response = self.client.get('/contact/', follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_contact_form_submission(self):
        """Test contact form submission."""
        response = self.client.post('/contact/', {
            'name': 'Test User',
            'email': 'user@example.com',
            'subject': 'Test Subject',
            'message': 'Test message content'
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)


class ValidatorsTests(TestCase):
    """Tests for file size validators."""
    
    def test_validate_image_size_accepts_small_file(self):
        """Test that validator accepts files under 5MB."""
        from core.validators import validate_image_size
        from unittest.mock import MagicMock
        
        mock_file = MagicMock()
        mock_file.size = 4 * 1024 * 1024  # 4MB
        
        # Should not raise exception
        validate_image_size(mock_file)
    
    def test_validate_image_size_rejects_large_file(self):
        """Test that validator rejects files over 5MB."""
        from core.validators import validate_image_size
        from django.core.exceptions import ValidationError
        
        mock_file = MagicMock()
        mock_file.size = 6 * 1024 * 1024  # 6MB
        
        with self.assertRaises(ValidationError):
            validate_image_size(mock_file)
    
    def test_validate_video_size_accepts_valid_file(self):
        """Test that validator accepts files under 50MB."""
        from core.validators import validate_video_size
        
        mock_file = MagicMock()
        mock_file.size = 40 * 1024 * 1024  # 40MB
        
        # Should not raise exception
        validate_video_size(mock_file)
    
    def test_validate_video_size_rejects_large_file(self):
        """Test that validator rejects files over 50MB."""
        from core.validators import validate_video_size
        from django.core.exceptions import ValidationError
        
        mock_file = MagicMock()
        mock_file.size = 60 * 1024 * 1024  # 60MB
        
        with self.assertRaises(ValidationError):
            validate_video_size(mock_file)
    
    def test_get_safe_sort_returns_valid_sort(self):
        """Test that get_safe_sort returns whitelisted sorts."""
        from core.validators import get_safe_sort, ALLOWED_ARCHIVE_SORTS
        
        result = get_safe_sort('newest', ALLOWED_ARCHIVE_SORTS)
        self.assertEqual(result, '-created_at')
    
    def test_get_safe_sort_returns_default_for_invalid(self):
        """Test that get_safe_sort returns default for invalid input."""
        from core.validators import get_safe_sort, ALLOWED_ARCHIVE_SORTS
        
        result = get_safe_sort('invalid_sort; DROP TABLE;', ALLOWED_ARCHIVE_SORTS)
        self.assertEqual(result, '-created_at')
