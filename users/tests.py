"""
Unit tests for the users app.
Tests user model, notifications, profile functionality, and authentication.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Notification, Thread, Message

User = get_user_model()


class CustomUserModelTests(TestCase):
    """Tests for the CustomUser model."""
    
    def test_create_user(self):
        """Test creating a user with email and password."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
    
    def test_user_str_with_full_name(self):
        """Test user string representation with full name."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Test User Full Name'
        )
        
        self.assertEqual(str(user), 'Test User Full Name')
    
    def test_user_str_without_full_name(self):
        """Test user string representation without full name."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Should fallback to email
        self.assertEqual(str(user), 'test@example.com')
    
    def test_get_display_name_with_full_name(self):
        """Test get_display_name returns full name when set."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            full_name='Display Name'
        )
        
        self.assertEqual(user.get_display_name(), 'Display Name')
    
    def test_get_display_name_fallback_to_email(self):
        """Test get_display_name falls back to email prefix."""
        user = User.objects.create_user(
            username='testuser',
            email='john.doe@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.get_display_name(), 'john.doe')
    
    def test_user_can_have_bio(self):
        """Test user bio field."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            bio='This is my bio'
        )
        
        self.assertEqual(user.bio, 'This is my bio')
    
    def test_user_social_links_default(self):
        """Test user social_links defaults to empty dict."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.social_links, {})


class NotificationModelTests(TestCase):
    """Tests for the Notification model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='recipient',
            email='recipient@example.com',
            password='testpass123'
        )
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@example.com',
            password='testpass123'
        )
    
    def test_create_notification(self):
        """Test creating a notification."""
        notification = Notification.objects.create(
            recipient=self.user,
            sender=self.sender,
            verb='liked your archive'
        )
        
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.sender, self.sender)
        self.assertEqual(notification.verb, 'liked your archive')
        self.assertTrue(notification.unread)
    
    def test_notification_mark_as_read(self):
        """Test marking a notification as read."""
        notification = Notification.objects.create(
            recipient=self.user,
            sender=self.sender,
            verb='commented on your post'
        )
        
        self.assertTrue(notification.unread)
        
        notification.mark_as_read()
        
        notification.refresh_from_db()
        self.assertFalse(notification.unread)
    
    def test_notification_str(self):
        """Test notification string representation."""
        notification = Notification.objects.create(
            recipient=self.user,
            verb='test verb'
        )
        
        self.assertIn(self.user.username, str(notification))
        self.assertIn('test verb', str(notification))
    
    def test_notification_ordering(self):
        """Test notifications are ordered by timestamp descending."""
        notif1 = Notification.objects.create(recipient=self.user, verb='first')
        notif2 = Notification.objects.create(recipient=self.user, verb='second')
        
        notifications = list(Notification.objects.filter(recipient=self.user))
        
        # Most recent should be first
        self.assertEqual(notifications[0], notif2)
        self.assertEqual(notifications[1], notif1)
    
    def test_unread_notification_count(self):
        """Test counting unread notifications."""
        Notification.objects.create(recipient=self.user, verb='unread1')
        Notification.objects.create(recipient=self.user, verb='unread2')
        read_notif = Notification.objects.create(recipient=self.user, verb='read')
        read_notif.mark_as_read()
        
        unread_count = self.user.notifications.filter(unread=True).count()
        
        self.assertEqual(unread_count, 2)


class ThreadAndMessageTests(TestCase):
    """Tests for Thread and Message models."""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
    
    def test_create_thread(self):
        """Test creating a message thread."""
        thread = Thread.objects.create(subject='Test Thread')
        thread.participants.add(self.user1, self.user2)
        
        self.assertEqual(thread.subject, 'Test Thread')
        self.assertEqual(thread.participants.count(), 2)
    
    def test_thread_str(self):
        """Test thread string representation."""
        thread = Thread.objects.create(subject='My Subject')
        
        self.assertEqual(str(thread), 'My Subject')
    
    def test_create_message(self):
        """Test creating a message in a thread."""
        thread = Thread.objects.create(subject='Test Thread')
        thread.participants.add(self.user1, self.user2)
        
        message = Message.objects.create(
            thread=thread,
            sender=self.user1,
            content='Hello, this is a test message'
        )
        
        self.assertEqual(message.thread, thread)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, 'Hello, this is a test message')
        self.assertFalse(message.is_read)
    
    def test_message_ordering(self):
        """Test messages are ordered by created_at ascending."""
        thread = Thread.objects.create(subject='Test Thread')
        
        msg1 = Message.objects.create(thread=thread, sender=self.user1, content='First')
        msg2 = Message.objects.create(thread=thread, sender=self.user2, content='Second')
        
        messages = list(thread.messages.all())
        
        # Oldest first
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)


class UserAuthenticationTests(TestCase):
    """Tests for user authentication flows."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_can_login(self):
        """Test that user can log in with valid credentials."""
        logged_in = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(logged_in)
    
    def test_user_cannot_login_with_wrong_password(self):
        """Test that user cannot log in with wrong password."""
        logged_in = self.client.login(username='testuser', password='wrongpassword')
        self.assertFalse(logged_in)
    
    def test_authenticated_user_can_access_protected_pages(self):
        """Test authenticated user can access login-required pages."""
        self.client.login(username='testuser', password='testpass123')
        
        # Accessing archives create (login required)
        response = self.client.get(reverse('archives:create'), follow=True)
        self.assertEqual(response.status_code, 200)
    
    def test_unauthenticated_user_redirected_from_protected_pages(self):
        """Test unauthenticated user is redirected from login-required pages."""
        response = self.client.get(reverse('archives:create'), follow=True)
        
        # Should end up at login page
        self.assertIn('login', response.request['PATH_INFO'])

