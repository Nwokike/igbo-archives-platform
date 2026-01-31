"""
Unit tests for the core app.
Tests homepage, static pages, contact form, and utility functions.
"""
from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
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
    
    @patch('core.turnstile.verify_turnstile', return_value={'success': True})
    def test_contact_form_submission(self, mock_turnstile):
        """Test contact form submission with mocked Turnstile."""
        response = self.client.post('/contact/', {
            'name': 'Test User',
            'email': 'user@example.com',
            'subject': 'Test Subject',
            'message': 'Test message content that is long enough to pass validation'
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


class MediaCleanupTests(TestCase):
    """Tests for automatic media deletion using django-cleanup."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testcleanupuser', password='password')
        # Create a small image file
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x03\x02\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )

    def test_archive_deletion_cleans_media(self):
        """Test that deleting an Archive record deletes its files from storage."""
        # Dynamically patch whatever storage backend is configured (likely FileSystemStorage in tests)
        backend = settings.STORAGES['default']['BACKEND']
        with patch(f"{backend}.delete") as mock_delete:
            archive = Archive.objects.create(
                title='Test Archive',
                description='Test description',
                archive_type='image',
                image=self.test_image,
                uploaded_by=self.user
            )
            file_name = archive.image.name
            
            # Delete the archive within a commit capture block
            with self.captureOnCommitCallbacks(execute=True):
                archive.delete()
            
            # Verify storage.delete was called
            self.assertTrue(mock_delete.called, f"storage.delete not called for {file_name}")
            mock_delete.assert_called_with(file_name)

    def test_profile_picture_update_cleans_old_media(self):
        """Test that updating a profile picture deletes the old one."""
        backend = settings.STORAGES['default']['BACKEND']
        with patch(f"{backend}.delete") as mock_delete:
            user = User.objects.create_user(username='testcleanupuser2', password='password')
            
            # Set initial profile picture
            user.profile_picture = SimpleUploadedFile(
                name='old_pfp.jpg',
                content=b'old_content',
                content_type='image/jpeg'
            )
            user.save()
            old_file_name = user.profile_picture.name
            
            # Update profile picture within a commit capture block
            with self.captureOnCommitCallbacks(execute=True):
                user.profile_picture = SimpleUploadedFile(
                    name='new_pfp.jpg',
                    content=b'new_content',
                    content_type='image/jpeg'
                )
                user.save()
            
            # Verify old file was deleted
            self.assertTrue(mock_delete.called, f"storage.delete not called for old pfp: {old_file_name}")
            mock_delete.assert_called_with(old_file_name)

    def test_bulk_deletion_cleans_media(self):
        """Test that bulk deletion also triggers cleanup."""
        backend = settings.STORAGES['default']['BACKEND']
        with patch(f"{backend}.delete") as mock_delete:
            # Create multiple archives
            a1 = Archive.objects.create(
                title='A1', description='D', archive_type='image',
                image=SimpleUploadedFile('a1.jpg', b'c'), uploaded_by=self.user
            )
            a2 = Archive.objects.create(
                title='A2', description='D', archive_type='image',
                image=SimpleUploadedFile('a2.jpg', b'c'), uploaded_by=self.user
            )
            
            names = [a1.image.name, a2.image.name]
            
            # Bulk delete within a commit capture block
            with self.captureOnCommitCallbacks(execute=True):
                Archive.objects.filter(title__in=['A1', 'A2']).delete()
            
            # Verify all were deleted
            self.assertEqual(mock_delete.call_count, 2)
            for name in names:
                mock_delete.assert_any_call(name)


class HueyTaskTests(TestCase):
    """Tests for Huey background tasks."""

    @patch('core.tasks.send_mail')
    def test_send_email_async(self, mock_send_mail):
        """Test the send_email_async task."""
        from core.tasks import send_email_async
        
        # Test calling directly using .call_local() to bypass Huey queue
        result = send_email_async.call_local(
            subject='Test Subject',
            message='Test Message',
            recipient_list=['test@example.com']
        )
        
        self.assertTrue(result)
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertEqual(kwargs['subject'], 'Test Subject')
        self.assertEqual(kwargs['recipient_list'], ['test@example.com'])
    
    @patch('webpush.send_user_notification')
    def test_send_push_notification_async(self, mock_send_push):
        """Test the send_push_notification_async task."""
        from core.tasks import send_push_notification_async
        
        user = User.objects.create_user(username='pushtest', password='password')
        
        # Test calling directly using .call_local() to bypass Huey queue
        result = send_push_notification_async.call_local(
            user_id=user.id,
            title='Test Push',
            body='Test Body',
            url='/test/'
        )
        
        self.assertTrue(result)
        mock_send_push.assert_called_once()