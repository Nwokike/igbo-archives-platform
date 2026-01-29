"""
Unit tests for the books app.
Tests book recommendation CRUD operations and model functionality.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from books.models import BookRecommendation, UserBookRating

User = get_user_model()


class BookRecommendationModelTests(TestCase):
    """Tests for the BookRecommendation model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='added_by',
            email='added_by@example.com',
            password='testpass123'
        )
    
    def test_create_book_recommendation(self):
        """Test creating a book recommendation."""
        recommendation = BookRecommendation.objects.create(
            book_title='Things Fall Apart',
            author='Chinua Achebe',
            title='A Masterpiece of Nigerian Literature',
            slug='things-fall-apart-review',
            added_by=self.user
        )
        
        self.assertEqual(recommendation.book_title, 'Things Fall Apart')
        self.assertEqual(recommendation.author, 'Chinua Achebe')
        self.assertEqual(recommendation.title, 'A Masterpiece of Nigerian Literature')
        self.assertIn('Things Fall Apart', str(recommendation))
    
    def test_book_recommendation_default_values(self):
        """Test book recommendation default field values."""
        recommendation = BookRecommendation.objects.create(
            book_title='Test Book',
            author='Test Author',
            title='Test Recommendation',
            slug='test-review',
            added_by=self.user
        )
        
        self.assertFalse(recommendation.is_published)
        self.assertFalse(recommendation.is_approved)
        self.assertFalse(recommendation.pending_approval)
    
    def test_book_recommendation_content_property(self):
        """Test content property returns content_json when available."""
        content_data = {'blocks': [{'type': 'paragraph', 'data': {'text': 'Great book!'}}]}
        recommendation = BookRecommendation.objects.create(
            book_title='Test',
            author='Author',
            title='Review',
            slug='test',
            content_json=content_data,
            added_by=self.user
        )
        
        self.assertEqual(recommendation.content, content_data)
    
    def test_book_recommendation_content_fallback(self):
        """Test content property falls back to legacy_content."""
        recommendation = BookRecommendation.objects.create(
            book_title='Test',
            author='Author',
            title='Review',
            slug='test',
            content_json=None,
            legacy_content='<p>Legacy review</p>',
            added_by=self.user
        )
        
        self.assertEqual(recommendation.content, '<p>Legacy review</p>')
    
    def test_book_recommendation_ordering(self):
        """Test recommendations are ordered by created_at descending."""
        recommendation1 = BookRecommendation.objects.create(
            book_title='First', author='Author', title='First',
            slug='first', added_by=self.user
        )
        recommendation2 = BookRecommendation.objects.create(
            book_title='Second', author='Author', title='Second',
            slug='second', added_by=self.user
        )
        
        recommendations = list(BookRecommendation.objects.all())
        
        # Most recent first
        self.assertEqual(recommendations[0], recommendation2)
        self.assertEqual(recommendations[1], recommendation1)
    
    def test_book_recommendation_optional_fields(self):
        """Test optional fields are handled correctly."""
        recommendation = BookRecommendation.objects.create(
            book_title='Test',
            author='Author',
            title='Review',
            slug='test',
            added_by=self.user,
            isbn='978-0123456789',
            publisher='Test Publisher',
            publication_year=2020
        )
        
        self.assertEqual(recommendation.isbn, '978-0123456789')
        self.assertEqual(recommendation.publisher, 'Test Publisher')
        self.assertEqual(recommendation.publication_year, 2020)
    
    def test_book_recommendation_published_filter(self):
        """Test filtering for published recommendations."""
        published = BookRecommendation.objects.create(
            book_title='Published', author='Author', title='Published Recommendation',
            slug='published', added_by=self.user,
            is_published=True, is_approved=True
        )
        draft = BookRecommendation.objects.create(
            book_title='Draft', author='Author', title='Draft Recommendation',
            slug='draft', added_by=self.user,
            is_published=False
        )
        
        published_recs = BookRecommendation.objects.filter(is_published=True, is_approved=True)
        self.assertEqual(published_recs.count(), 1)
        self.assertEqual(published_recs.first(), published)
    
    def test_book_recommendation_pending_approval(self):
        """Test pending approval workflow."""
        recommendation = BookRecommendation.objects.create(
            book_title='Pending', author='Author', title='Pending Recommendation',
            slug='pending', added_by=self.user,
            pending_approval=True, submitted_at=timezone.now()
        )
        
        self.assertTrue(recommendation.pending_approval)
        self.assertIsNotNone(recommendation.submitted_at)
    
    def test_book_recommendation_tags(self):
        """Test tags support."""
        recommendation = BookRecommendation.objects.create(
            book_title='Tagged', author='Author', title='Tagged Recommendation',
            slug='tagged', added_by=self.user
        )
        
        recommendation.tags.add('fiction', 'african-literature', 'classic')
        
        self.assertEqual(recommendation.tags.count(), 3)
        self.assertTrue(recommendation.tags.filter(name='fiction').exists())


class UserBookRatingTests(TestCase):
    """Tests for the UserBookRating model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='rater',
            email='rater@example.com',
            password='testpass123'
        )
        self.recommendation = BookRecommendation.objects.create(
            book_title='Test Book',
            author='Author',
            title='Test Recommendation',
            slug='test-book',
            added_by=self.user,
            is_published=True,
            is_approved=True
        )
    
    def test_create_rating(self):
        """Test creating a user rating."""
        rating = UserBookRating.objects.create(
            book=self.recommendation,
            user=self.user,
            rating=5,
            review_text='Excellent book!'
        )
        
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.review_text, 'Excellent book!')
    
    def test_rating_range(self):
        """Test ratings are constrained to 1-5."""
        for r in range(1, 6):
            user = User.objects.create_user(
                username=f'rater{r}',
                email=f'rater{r}@example.com',
                password='testpass123'
            )
            rating = UserBookRating.objects.create(
                book=self.recommendation,
                user=user,
                rating=r
            )
            self.assertEqual(rating.rating, r)
    
    def test_average_rating(self):
        """Test average_rating property on BookRecommendation."""
        users = []
        for i in range(3):
            users.append(User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            ))
        
        UserBookRating.objects.create(book=self.recommendation, user=users[0], rating=4)
        UserBookRating.objects.create(book=self.recommendation, user=users[1], rating=5)
        UserBookRating.objects.create(book=self.recommendation, user=users[2], rating=3)
        
        self.assertEqual(self.recommendation.average_rating, 4.0)
        self.assertEqual(self.recommendation.rating_count, 3)
    
    def test_unique_user_book_rating(self):
        """Test a user can only rate a book once."""
        UserBookRating.objects.create(
            book=self.recommendation,
            user=self.user,
            rating=4
        )
        
        with self.assertRaises(Exception):
            UserBookRating.objects.create(
                book=self.recommendation,
                user=self.user,
                rating=5
            )


class BookRecommendationViewAuthTests(TestCase):
    """Tests for book recommendation view authentication."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='added_by',
            email='added_by@example.com',
            password='testpass123'
        )
    
    def test_create_requires_login(self):
        """Test that creating recommendations requires authentication."""
        response = self.client.get('/books/create/', follow=True)
        
        # Should end up at login page
        self.assertIn('login', response.request['PATH_INFO'])
    
    def test_edit_requires_ownership(self):
        """Test that editing requires ownership."""
        recommendation = BookRecommendation.objects.create(
            book_title='Test', author='Author', title='Test Recommendation',
            slug='test-review', added_by=self.user,
            is_published=True, is_approved=True
        )
        
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        self.client.login(username='other', password='testpass123')
        
        response = self.client.get(f'/books/{recommendation.slug}/edit/', follow=True)
        self.assertEqual(response.status_code, 404)


class BookRecommendationSearchTests(TestCase):
    """Tests for book recommendation search functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='added_by',
            email='added_by@example.com',
            password='testpass123'
        )
    
    def test_search_by_title(self):
        """Test searching recommendations by book or title."""
        BookRecommendation.objects.create(
            book_title='Igbo Dictionary', author='Scholar',
            title='Comprehensive Language Resource',
            slug='igbo-dict', added_by=self.user,
            is_published=True, is_approved=True
        )
        
        from django.db.models import Q
        results = BookRecommendation.objects.filter(
            Q(book_title__icontains='Dictionary') | Q(title__icontains='Dictionary'),
            is_published=True, is_approved=True
        )
        
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().book_title, 'Igbo Dictionary')
