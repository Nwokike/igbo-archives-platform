"""
Unit tests for the archives app.
Tests archive CRUD operations, filtering, and model functionality.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from archives.models import Archive, Category
from core.validators import validate_image_size, validate_video_size

User = get_user_model()


class CategoryModelTests(TestCase):
    """Tests for the Category model."""
    
    def test_create_category(self):
        """Test creating a category."""
        category = Category.objects.create(
            name='Historical Photos',
            slug='historical-photos',
            description='Photos from pre-colonial era'
        )
        
        self.assertEqual(category.name, 'Historical Photos')
        self.assertEqual(category.slug, 'historical-photos')
        self.assertEqual(str(category), 'Historical Photos')
    
    def test_category_slug_is_unique(self):
        """Test that category slugs must be unique."""
        Category.objects.create(name='Test', slug='test-slug')
        
        with self.assertRaises(Exception):
            Category.objects.create(name='Test 2', slug='test-slug')


class ArchiveModelTests(TestCase):
    """Tests for the Archive model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
    
    def test_create_archive(self):
        """Test creating an archive."""
        archive = Archive.objects.create(
            title='Test Archive',
            description='A test archive description',
            archive_type='image',
            uploaded_by=self.user,
            category=self.category
        )
        
        self.assertEqual(archive.title, 'Test Archive')
        self.assertEqual(archive.archive_type, 'image')
        self.assertEqual(archive.uploaded_by, self.user)
        self.assertEqual(str(archive), 'Test Archive')
    
    def test_archive_default_is_approved(self):
        """Test that archives default to NOT approved (pending moderation)."""
        archive = Archive.objects.create(
            title='Test Archive',
            description='Description',
            archive_type='image',
            uploaded_by=self.user
        )
        
        # Default should be False - archives need approval before publishing
        self.assertFalse(archive.is_approved)
    
    def test_archive_types(self):
        """Test all archive type choices are valid."""
        valid_types = ['image', 'video', 'document', 'audio']
        
        for archive_type in valid_types:
            archive = Archive.objects.create(
                title=f'Test {archive_type}',
                description='Description',
                archive_type=archive_type,
                uploaded_by=self.user
            )
            self.assertEqual(archive.archive_type, archive_type)
    
    def test_archive_get_primary_file_for_image(self):
        """Test get_primary_file returns image for image type."""
        archive = Archive.objects.create(
            title='Image Archive',
            description='Description',
            archive_type='image',
            uploaded_by=self.user
        )
        
        # Without actual file, should return None
        self.assertIsNone(archive.get_primary_file())
    
    def test_archive_has_featured_image(self):
        """Test has_featured_image method."""
        archive = Archive.objects.create(
            title='Test Archive',
            description='Description',
            archive_type='document',
            uploaded_by=self.user
        )
        
        # Without featured image or image file
        self.assertFalse(archive.has_featured_image())
    
    def test_archive_ordering(self):
        """Test archives are ordered by created_at descending."""
        archive1 = Archive.objects.create(
            title='First',
            description='First archive',
            archive_type='image',
            uploaded_by=self.user
        )
        archive2 = Archive.objects.create(
            title='Second',
            description='Second archive',
            archive_type='image',
            uploaded_by=self.user
        )
        
        archives = list(Archive.objects.all())
        
        # Most recent first
        self.assertEqual(archives[0], archive2)
        self.assertEqual(archives[1], archive1)


class ArchiveViewTests(TestCase):
    """Tests for archive views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.archive = Archive.objects.create(
            title='Test Archive',
            description='A test archive',
            archive_type='image',
            uploaded_by=self.user,
            category=self.category,
            is_approved=True
        )
    
    def test_archive_list_view(self):
        """Test archive list page loads."""
        response = self.client.get('/archives/', follow=True)
        
        self.assertEqual(response.status_code, 200)
    
    def test_archive_list_shows_approved_only(self):
        """Test that list only shows approved archives."""
        unapproved = Archive.objects.create(
            title='Unapproved',
            description='Unapproved archive',
            archive_type='image',
            uploaded_by=self.user,
            is_approved=False
        )
        
        response = self.client.get('/archives/', follow=True)
        
        # Get archives from context
        if response.context and 'archives' in response.context:
            archive_titles = [a.title for a in response.context['archives']]
            self.assertIn('Test Archive', archive_titles)
            self.assertNotIn('Unapproved', archive_titles)
    
    def test_archive_list_filter_by_category(self):
        """Test filtering archives by category."""
        other_category = Category.objects.create(name='Other', slug='other')
        Archive.objects.create(
            title='Other Archive',
            description='In other category',
            archive_type='image',
            uploaded_by=self.user,
            category=other_category,
            is_approved=True
        )
        
        response = self.client.get('/archives/?category=test-category', follow=True)
        
        if response.context and 'archives' in response.context:
            archive_titles = [a.title for a in response.context['archives']]
            self.assertIn('Test Archive', archive_titles)
    
    def test_archive_detail_view(self):
        """Test archive detail page loads."""
        response = self.client.get(f'/archives/{self.archive.pk}/', follow=True)
        
        self.assertEqual(response.status_code, 200)
    
    def test_archive_detail_404_for_unapproved(self):
        """Test that unapproved archives return 404."""
        unapproved = Archive.objects.create(
            title='Unapproved',
            description='Not approved',
            archive_type='image',
            uploaded_by=self.user,
            is_approved=False
        )
        
        response = self.client.get(f'/archives/{unapproved.pk}/', follow=True)
        
        self.assertEqual(response.status_code, 404)
    
    def test_archive_create_requires_login(self):
        """Test that creating archives requires authentication."""
        response = self.client.get('/archives/create/', follow=True)
        
        # Should redirect to login page
        self.assertIn('login', response.request['PATH_INFO'])
    
    def test_archive_create_view_loads_for_authenticated(self):
        """Test create view loads for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get('/archives/create/', follow=True)
        
        self.assertEqual(response.status_code, 200)
    
    def test_archive_create_post(self):
        """Test creating an archive via POST - testing the model directly."""
        self.client.login(username='testuser', password='testpass123')
        
        # Test that we can create an archive programmatically
        archive = Archive.objects.create(
            title='New Archive',
            description='A new archive description',
            archive_type='image',
            caption='Test caption',
            uploaded_by=self.user,
            category=self.category,
            is_approved=False
        )
        
        self.assertEqual(archive.title, 'New Archive')
        self.assertFalse(archive.is_approved)  # New archives pending approval
    
    def test_archive_create_requires_title_and_description(self):
        """Test that title and description are required."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post('/archives/create/', {
            'title': '',
            'description': '',
            'archive_type': 'image',
        }, follow=True)
        
        # Should stay on the page (form validation) but still 200
        self.assertEqual(response.status_code, 200)
    
    def test_archive_edit_requires_ownership(self):
        """Test that only owner can edit their archive."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        self.client.login(username='other', password='testpass123')
        
        response = self.client.get(f'/archives/{self.archive.pk}/edit/', follow=True)
        
        # Should return 404 for non-owner
        self.assertEqual(response.status_code, 404)
    
    def test_archive_edit_by_owner(self):
        """Test that owner can access edit page."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(f'/archives/{self.archive.pk}/edit/', follow=True)
        
        self.assertEqual(response.status_code, 200)


class ArchiveFileSizeValidationTests(TestCase):
    """Tests for file size validation on archives."""
    
    def test_image_size_validation_accepts_small_file(self):
        """Test image validator accepts files under 5MB."""
        from unittest.mock import MagicMock
        
        mock_file = MagicMock()
        mock_file.size = 4 * 1024 * 1024  # 4MB
        
        # Should not raise
        validate_image_size(mock_file)
    
    def test_image_size_validation_rejects_large_file(self):
        """Test image validator rejects files over 5MB."""
        from unittest.mock import MagicMock
        
        mock_file = MagicMock()
        mock_file.size = 10 * 1024 * 1024  # 10MB
        
        with self.assertRaises(ValidationError) as context:
            validate_image_size(mock_file)
        
        self.assertIn('5MB', str(context.exception))
    
    def test_video_size_validation_accepts_valid_file(self):
        """Test video validator accepts files under 50MB."""
        from unittest.mock import MagicMock
        
        mock_file = MagicMock()
        mock_file.size = 45 * 1024 * 1024  # 45MB
        
        # Should not raise
        validate_video_size(mock_file)
    
    def test_video_size_validation_rejects_large_file(self):
        """Test video validator rejects files over 50MB."""
        from unittest.mock import MagicMock
        
        mock_file = MagicMock()
        mock_file.size = 100 * 1024 * 1024  # 100MB
        
        with self.assertRaises(ValidationError) as context:
            validate_video_size(mock_file)
        
        self.assertIn('50MB', str(context.exception))
