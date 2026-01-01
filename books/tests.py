"""
Unit tests for the books app.
Tests book review CRUD operations and model functionality.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from books.models import BookReview

User = get_user_model()


class BookReviewModelTests(TestCase):
    """Tests for the BookReview model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123'
        )
    
    def test_create_book_review(self):
        """Test creating a book review."""
        review = BookReview.objects.create(
            book_title='Things Fall Apart',
            author='Chinua Achebe',
            review_title='A Masterpiece of Nigerian Literature',
            slug='things-fall-apart-review',
            rating=5,
            reviewer=self.user
        )
        
        self.assertEqual(review.book_title, 'Things Fall Apart')
        self.assertEqual(review.author, 'Chinua Achebe')
        self.assertEqual(review.rating, 5)
        self.assertIn('Things Fall Apart', str(review))
    
    def test_book_review_default_values(self):
        """Test book review default field values."""
        review = BookReview.objects.create(
            book_title='Test Book',
            author='Test Author',
            review_title='Test Review',
            slug='test-review',
            rating=3,
            reviewer=self.user
        )
        
        self.assertFalse(review.is_published)
        self.assertFalse(review.is_approved)
        self.assertFalse(review.pending_approval)
    
    def test_book_review_rating_choices(self):
        """Test rating is constrained to 1-5."""
        for rating in range(1, 6):
            review = BookReview.objects.create(
                book_title=f'Book {rating}',
                author='Author',
                review_title=f'Review {rating}',
                slug=f'review-{rating}',
                rating=rating,
                reviewer=self.user
            )
            self.assertEqual(review.rating, rating)
    
    def test_book_review_content_property(self):
        """Test content property returns content_json when available."""
        content_data = {'blocks': [{'type': 'paragraph', 'data': {'text': 'Great book!'}}]}
        review = BookReview.objects.create(
            book_title='Test',
            author='Author',
            review_title='Review',
            slug='test',
            rating=4,
            content_json=content_data,
            reviewer=self.user
        )
        
        self.assertEqual(review.content, content_data)
    
    def test_book_review_content_fallback(self):
        """Test content property falls back to legacy_content."""
        review = BookReview.objects.create(
            book_title='Test',
            author='Author',
            review_title='Review',
            slug='test',
            rating=4,
            content_json=None,
            legacy_content='<p>Legacy review</p>',
            reviewer=self.user
        )
        
        self.assertEqual(review.content, '<p>Legacy review</p>')
    
    def test_book_review_ordering(self):
        """Test reviews are ordered by created_at descending."""
        review1 = BookReview.objects.create(
            book_title='First', author='Author', review_title='First',
            slug='first', rating=3, reviewer=self.user
        )
        review2 = BookReview.objects.create(
            book_title='Second', author='Author', review_title='Second',
            slug='second', rating=4, reviewer=self.user
        )
        
        reviews = list(BookReview.objects.all())
        
        # Most recent first
        self.assertEqual(reviews[0], review2)
        self.assertEqual(reviews[1], review1)
    
    def test_book_review_optional_fields(self):
        """Test optional fields are handled correctly."""
        review = BookReview.objects.create(
            book_title='Test',
            author='Author',
            review_title='Review',
            slug='test',
            rating=3,
            reviewer=self.user,
            isbn='978-0123456789',
            publisher='Test Publisher',
            publication_year=2020
        )
        
        self.assertEqual(review.isbn, '978-0123456789')
        self.assertEqual(review.publisher, 'Test Publisher')
        self.assertEqual(review.publication_year, 2020)
    
    def test_book_review_published_filter(self):
        """Test filtering for published reviews."""
        published = BookReview.objects.create(
            book_title='Published', author='Author', review_title='Published Review',
            slug='published', rating=5, reviewer=self.user,
            is_published=True, is_approved=True
        )
        draft = BookReview.objects.create(
            book_title='Draft', author='Author', review_title='Draft Review',
            slug='draft', rating=3, reviewer=self.user,
            is_published=False
        )
        
        published_reviews = BookReview.objects.filter(is_published=True, is_approved=True)
        self.assertEqual(published_reviews.count(), 1)
        self.assertEqual(published_reviews.first(), published)
    
    def test_book_review_pending_approval(self):
        """Test pending approval workflow."""
        review = BookReview.objects.create(
            book_title='Pending', author='Author', review_title='Pending Review',
            slug='pending', rating=4, reviewer=self.user,
            pending_approval=True, submitted_at=timezone.now()
        )
        
        self.assertTrue(review.pending_approval)
        self.assertIsNotNone(review.submitted_at)
    
    def test_book_review_tags(self):
        """Test tags support."""
        review = BookReview.objects.create(
            book_title='Tagged', author='Author', review_title='Tagged Review',
            slug='tagged', rating=4, reviewer=self.user
        )
        
        review.tags.add('fiction', 'african-literature', 'classic')
        
        self.assertEqual(review.tags.count(), 3)
        self.assertTrue(review.tags.filter(name='fiction').exists())


class BookReviewViewAuthTests(TestCase):
    """Tests for book review view authentication."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123'
        )
    
    def test_create_requires_login(self):
        """Test that creating reviews requires authentication."""
        response = self.client.get('/books/create/', follow=True)
        
        # Should end up at login page
        self.assertIn('login', response.request['PATH_INFO'])
    
    def test_edit_requires_ownership(self):
        """Test that editing requires ownership."""
        review = BookReview.objects.create(
            book_title='Test', author='Author', review_title='Test Review',
            slug='test-review', rating=4, reviewer=self.user,
            is_published=True, is_approved=True
        )
        
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        self.client.login(username='other', password='testpass123')
        
        response = self.client.get(f'/books/{review.slug}/edit/', follow=True)
        self.assertEqual(response.status_code, 404)


class BookReviewRatingTests(TestCase):
    """Tests for book review rating functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='testpass123'
        )
    
    def test_rating_filter_gte(self):
        """Test filtering by minimum rating."""
        BookReview.objects.create(
            book_title='Low', author='Author', review_title='Low Rated',
            slug='low', rating=2, reviewer=self.user, is_published=True, is_approved=True
        )
        BookReview.objects.create(
            book_title='High', author='Author', review_title='High Rated',
            slug='high', rating=5, reviewer=self.user, is_published=True, is_approved=True
        )
        
        high_rated = BookReview.objects.filter(is_published=True, is_approved=True, rating__gte=4)
        self.assertEqual(high_rated.count(), 1)
        self.assertEqual(high_rated.first().book_title, 'High')
    
    def test_search_by_title(self):
        """Test searching reviews by book or review title."""
        BookReview.objects.create(
            book_title='Igbo Dictionary', author='Scholar',
            review_title='Comprehensive Language Resource',
            slug='igbo-dict', rating=5, reviewer=self.user,
            is_published=True, is_approved=True
        )
        
        from django.db.models import Q
        results = BookReview.objects.filter(
            Q(book_title__icontains='Dictionary') | Q(review_title__icontains='Dictionary'),
            is_published=True, is_approved=True
        )
        
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().book_title, 'Igbo Dictionary')
