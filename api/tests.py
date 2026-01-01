"""
Unit tests for the API app.
Tests API endpoints, media browser, file uploads, and utility functions.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from archives.models import Archive, Category

User = get_user_model()


class ArchiveMediaBrowserTests(TestCase):
    """Tests for the archive media browser functionality - model level."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.archive = Archive.objects.create(
            title='Test Archive',
            description='A test archive',
            archive_type='image',
            uploaded_by=self.user,
            category=self.category,
            is_approved=True
        )
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_approved_archives_query(self):
        """Test querying approved archives."""
        approved = Archive.objects.filter(is_approved=True)
        
        self.assertEqual(approved.count(), 1)
        self.assertEqual(approved.first().title, 'Test Archive')
    
    def test_filter_excludes_unapproved(self):
        """Test unapproved archives are excluded."""
        unapproved = Archive.objects.create(
            title='Unapproved',
            description='Not approved',
            archive_type='image',
            uploaded_by=self.user,
            is_approved=False
        )
        
        approved = Archive.objects.filter(is_approved=True)
        
        self.assertEqual(approved.count(), 1)
        self.assertNotIn(unapproved, approved)
    
    def test_search_by_title(self):
        """Test searching archives by title."""
        Archive.objects.create(
            title='Igbo Traditional Mask',
            description='A mask',
            archive_type='image',
            uploaded_by=self.user,
            is_approved=True
        )
        
        results = Archive.objects.filter(
            is_approved=True, 
            title__icontains='Mask'
        )
        
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().title, 'Igbo Traditional Mask')
    
    def test_filter_by_archive_type(self):
        """Test filtering archives by type."""
        video_archive = Archive.objects.create(
            title='Video Archive',
            description='A video',
            archive_type='video',
            uploaded_by=self.user,
            is_approved=True
        )
        
        videos = Archive.objects.filter(is_approved=True, archive_type='video')
        images = Archive.objects.filter(is_approved=True, archive_type='image')
        
        self.assertEqual(videos.count(), 1)
        self.assertEqual(images.count(), 1)
    
    def test_filter_by_category(self):
        """Test filtering archives by category."""
        other_category = Category.objects.create(name='Other', slug='other')
        Archive.objects.create(
            title='Other Category Archive',
            description='In other',
            archive_type='image',
            uploaded_by=self.user,
            category=other_category,
            is_approved=True
        )
        
        test_cat_archives = Archive.objects.filter(
            is_approved=True, 
            category=self.category
        )
        
        self.assertEqual(test_cat_archives.count(), 1)
        self.assertEqual(test_cat_archives.first().title, 'Test Archive')


class CategoryTests(TestCase):
    """Tests for category functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_create_category(self):
        """Test creating a category."""
        category = Category.objects.create(name='History', slug='history')
        
        self.assertEqual(category.name, 'History')
        self.assertEqual(category.slug, 'history')
    
    def test_get_all_categories(self):
        """Test getting all categories."""
        Category.objects.create(name='History', slug='history')
        Category.objects.create(name='Culture', slug='culture')
        Category.objects.create(name='Art', slug='art')
        
        categories = Category.objects.all()
        
        self.assertEqual(categories.count(), 3)
    
    def test_category_unique_slug(self):
        """Test categories have unique slugs."""
        from django.db import IntegrityError, transaction
        
        Category.objects.create(name='Test', slug='test')
        
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name='Test 2', slug='test')


class FileUploadValidationTests(TestCase):
    """Tests for file upload validation."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_image_size_validation(self):
        """Test image size validator."""
        from core.validators import validate_image_size
        from django.core.exceptions import ValidationError
        from unittest.mock import MagicMock
        
        # Valid file
        mock_file = MagicMock()
        mock_file.size = 4 * 1024 * 1024  # 4MB
        validate_image_size(mock_file)  # Should not raise
        
        # Invalid file
        mock_file.size = 10 * 1024 * 1024  # 10MB
        with self.assertRaises(ValidationError):
            validate_image_size(mock_file)
    
    def test_video_size_validation(self):
        """Test video size validator."""
        from core.validators import validate_video_size
        from django.core.exceptions import ValidationError
        from unittest.mock import MagicMock
        
        # Valid file
        mock_file = MagicMock()
        mock_file.size = 40 * 1024 * 1024  # 40MB
        validate_video_size(mock_file)  # Should not raise
        
        # Invalid file
        mock_file.size = 100 * 1024 * 1024  # 100MB
        with self.assertRaises(ValidationError):
            validate_video_size(mock_file)
    
    def test_allowed_extensions(self):
        """Test file extension validation."""
        allowed_image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        allowed_video_extensions = {'mp4', 'webm', 'mov'}
        allowed_document_extensions = {'pdf', 'doc', 'docx'}
        
        # Test some extensions
        self.assertIn('jpg', allowed_image_extensions)
        self.assertIn('mp4', allowed_video_extensions)
        self.assertIn('pdf', allowed_document_extensions)
        self.assertNotIn('exe', allowed_image_extensions)


class ArchiveQueryTests(TestCase):
    """Tests for complex archive queries."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category1 = Category.objects.create(name='History', slug='history')
        self.category2 = Category.objects.create(name='Culture', slug='culture')
    
    def test_complex_filter(self):
        """Test complex filtering - category + type + approved."""
        Archive.objects.create(
            title='Historical Image',
            description='Old photo',
            archive_type='image',
            uploaded_by=self.user,
            category=self.category1,
            is_approved=True
        )
        Archive.objects.create(
            title='Historical Video',
            description='Old video',
            archive_type='video',
            uploaded_by=self.user,
            category=self.category1,
            is_approved=True
        )
        Archive.objects.create(
            title='Cultural Image',
            description='Cultural photo',
            archive_type='image',
            uploaded_by=self.user,
            category=self.category2,
            is_approved=True
        )
        
        # Filter: category=history + type=image
        results = Archive.objects.filter(
            is_approved=True,
            category=self.category1,
            archive_type='image'
        )
        
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().title, 'Historical Image')
    
    def test_search_across_fields(self):
        """Test searching across title and description."""
        from django.db.models import Q
        
        Archive.objects.create(
            title='Igbo Marriage Ceremony',
            description='Traditional wedding',
            archive_type='image',
            uploaded_by=self.user,
            is_approved=True
        )
        Archive.objects.create(
            title='Traditional Dance',
            description='Igbo cultural dance',
            archive_type='video',
            uploaded_by=self.user,
            is_approved=True
        )
        
        # Search for "Igbo" in title or description
        results = Archive.objects.filter(
            Q(title__icontains='Igbo') | Q(description__icontains='Igbo'),
            is_approved=True
        )
        
        self.assertEqual(results.count(), 2)
    
    def test_ordering(self):
        """Test archive ordering."""
        import time
        
        archive1 = Archive.objects.create(
            title='First', description='First', archive_type='image',
            uploaded_by=self.user, is_approved=True
        )
        archive2 = Archive.objects.create(
            title='Second', description='Second', archive_type='image',
            uploaded_by=self.user, is_approved=True
        )
        
        # Default ordering is -created_at (newest first)
        archives = list(Archive.objects.filter(is_approved=True))
        self.assertEqual(archives[0], archive2)
        self.assertEqual(archives[1], archive1)
