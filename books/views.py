"""
Book recommendation views for browsing and managing recommended Igbo books.
Users can rate and review books - the app is for listing/recommending, not reviewing.
"""
import json
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import slugify
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

from .models import BookRecommendation, UserBookRating
from core.validators import ALLOWED_BOOK_SORTS, get_safe_sort
from core.editorjs_helpers import parse_editorjs_content, generate_unique_slug, get_workflow_flags

logger = logging.getLogger(__name__)
User = get_user_model()


def get_related_books(book, count=9):
    """
    Get related book recommendations.
    """
    related = BookRecommendation.objects.filter(
        is_published=True,
        is_approved=True
    ).exclude(pk=book.pk).select_related('added_by').only(
        'id', 'book_title', 'title', 'slug', 'cover_image',
        'created_at', 'added_by__full_name', 'added_by__username'
    ).order_by('-created_at')
    
    return related[:count]


def book_list(request):
    """List all published book recommendations with filtering and pagination."""
    books = BookRecommendation.objects.filter(
        is_published=True, is_approved=True
    ).select_related('added_by').only(
        'id', 'book_title', 'title', 'slug', 'cover_image', 'author',
        'created_at', 'added_by__full_name', 'added_by__username'
    )
    
    if search := request.GET.get('search'):
        books = books.filter(
            Q(book_title__icontains=search) | 
            Q(title__icontains=search) |
            Q(author__icontains=search)
        )
    
    sort = get_safe_sort(request.GET.get('sort', '-created_at'), ALLOWED_BOOK_SORTS)
    books = books.order_by(sort)
    
    paginator = Paginator(books, 12)
    books_page = paginator.get_page(request.GET.get('page'))
    
    context = {
        'books': books_page,
    }
    
    if request.htmx:
        return render(request, 'books/partials/book_grid.html', context)
    
    return render(request, 'books/list.html', context)


def book_detail(request, slug):
    """Display a single book recommendation with user ratings."""
    book = get_object_or_404(
        BookRecommendation.objects.select_related('added_by'),
        slug=slug, is_published=True, is_approved=True
    )
    
    previous_book = BookRecommendation.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__lt=book.created_at
    ).order_by('-created_at').only('id', 'title', 'slug').first()
    
    next_book = BookRecommendation.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__gt=book.created_at
    ).order_by('created_at').only('id', 'title', 'slug').first()
    
    related_books = get_related_books(book, 9)
    
    # Get user's existing rating if logged in
    user_rating = None
    if request.user.is_authenticated:
        user_rating = UserBookRating.objects.filter(book=book, user=request.user).first()
    
    context = {
        'book': book,
        'previous_book': previous_book,
        'next_book': next_book,
        'related_books': related_books,
        'user_rating': user_rating,
    }
    
    return render(request, 'books/detail.html', context)


@login_required
def book_create(request):
    """Create a new book recommendation."""
    if request.method == 'POST':
        book_title = request.POST.get('book_title', '').strip()
        recommendation_title = request.POST.get('recommendation_title', '').strip()
        content_json = request.POST.get('content_json')
        action = request.POST.get('action')
        
        if not book_title or not recommendation_title or not content_json:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'books/create.html')
        
        try:
            content_data = json.loads(content_json) if isinstance(content_json, str) else content_json
        except json.JSONDecodeError:
            messages.error(request, 'Invalid content format. Please try again.')
            return render(request, 'books/create.html')
        
        base_slug = slugify(recommendation_title)[:200]
        slug = base_slug
        counter = 1
        while BookRecommendation.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            if counter > 100:
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                break
        
        # Check for duplicate ISBN
        isbn = request.POST.get('isbn', '').strip()[:20]
        if isbn:
            existing_book = BookRecommendation.objects.filter(isbn__iexact=isbn).first()
            if existing_book:
                messages.error(
                    request, 
                    f'A book with ISBN/ASIN "{isbn}" already exists. Search for "{existing_book.book_title}" to view it.'
                )
                return render(request, 'books/create.html')
        
        is_published = False
        is_approved = False
        pending_approval = False
        submitted_at = None
        
        if action == 'submit':
            pending_approval = True
            submitted_at = timezone.now()
            messages.success(request, 'Your book recommendation has been submitted for approval!')
        else:
            messages.success(request, 'Your book recommendation has been saved as a draft!')
        
        try:
            publication_year = int(request.POST.get('publication_year'))
            if publication_year < 1000 or publication_year > timezone.now().year + 1:
                publication_year = None
        except (ValueError, TypeError):
            publication_year = None
        
        book = BookRecommendation(
            book_title=book_title,
            author=request.POST.get('author', '').strip(),
            isbn=isbn,
            external_url=request.POST.get('external_url', '').strip(),
            publisher=request.POST.get('publisher', '').strip(),
            publication_year=publication_year,
            title=recommendation_title[:200],
            slug=slug,
            content_json=content_data,
            added_by=request.user,
            is_published=is_published,
            is_approved=is_approved,
            pending_approval=pending_approval,
            submitted_at=submitted_at,
        )
        
        if request.FILES.get('cover_image'):
            book.cover_image = request.FILES['cover_image']
        
        try:
            book.full_clean()
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return render(request, 'books/create.html')
        
        book.save()
        
        # Email notification
        if action == 'submit':
            try:
                staff_emails = list(User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True))
                if staff_emails:
                    send_mail(
                        subject=f"New Book Recommendation: {book.book_title}",
                        message=f"""
                        A new book recommendation has been submitted by {request.user.get_full_name() or request.user.username}.
                        
                        Book: {book.book_title}
                        Title: {book.title}
                        
                        Review it here: {request.scheme}://{request.get_host()}/users/admin/moderation/
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=staff_emails,
                        fail_silently=True
                    )
            except Exception as e:
                logger.warning(f"Failed to send notification email: {e}")
        
        return redirect('users:dashboard')
    
    return render(request, 'books/create.html')


@login_required
def book_edit(request, slug):
    """Edit an existing book recommendation."""
    book = get_object_or_404(BookRecommendation, slug=slug, added_by=request.user)
    
    if request.method == 'POST':
        book.book_title = request.POST.get('book_title', '').strip()
        book.author = request.POST.get('author', '').strip()
        
        # Check for duplicate ISBN (excluding current book)
        new_isbn = request.POST.get('isbn', '').strip()[:20]
        if new_isbn and new_isbn != book.isbn:
            existing_book = BookRecommendation.objects.filter(isbn__iexact=new_isbn).exclude(pk=book.pk).first()
            if existing_book:
                messages.error(
                    request, 
                    f'A book with ISBN/ASIN "{new_isbn}" already exists. '
                    f'<a href="{existing_book.get_absolute_url()}" target="_blank" class="text-accent underline">View existing book</a>'
                )
                initial_content = ''
                if book.content_json:
                    initial_content = json.dumps(book.content_json) if isinstance(book.content_json, dict) else book.content_json
                return render(request, 'books/edit.html', {'book': book, 'initial_content': initial_content})
        
        book.isbn = new_isbn
        book.external_url = request.POST.get('external_url', '').strip()
        book.publisher = request.POST.get('publisher', '').strip()
        
        try:
            publication_year = int(request.POST.get('publication_year'))
            if publication_year < 1000 or publication_year > timezone.now().year + 1:
                publication_year = None
        except (ValueError, TypeError):
            publication_year = None
        book.publication_year = publication_year
        
        book.title = request.POST.get('recommendation_title', '').strip()
        
        content_json = request.POST.get('content_json')
        if content_json:
            try:
                book.content_json = parse_editorjs_content(content_json)
            except ValidationError as e:
                messages.error(request, str(e))
                return render(request, 'books/edit.html', {
                    'book': book,
                    'initial_content': content_json
                })
        
        action = request.POST.get('action')
        if action == 'submit':
            workflow_flags = get_workflow_flags(action, is_submit=True)
            book.pending_approval = workflow_flags['pending_approval']
            book.submitted_at = workflow_flags['submitted_at']
            book.is_published = workflow_flags['is_published']
            book.is_approved = workflow_flags['is_approved']
            messages.success(request, 'Your book recommendation has been submitted for approval!')
        else:
            if book.is_published and book.is_approved:
                book.pending_approval = True
                book.is_published = False
                book.is_approved = False
            messages.success(request, 'Your book recommendation has been saved!')
        
        if request.FILES.get('cover_image'):
            book.cover_image = request.FILES['cover_image']
        
        book.save()
        
        # Email notification on resubmit
        if action == 'submit':
            try:
                staff_emails = list(User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True))
                if staff_emails:
                    send_mail(
                        subject=f"Book Recommendation Updated: {book.book_title}",
                        message=f"User {request.user.username} updated a book recommendation. Please review.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=staff_emails,
                        fail_silently=True
                    )
            except Exception as e:
                logger.warning(f"Failed to send notification email: {e}")
        
        return redirect('users:dashboard')
    
    initial_content = ''
    if book.content_json:
        initial_content = json.dumps(book.content_json) if isinstance(book.content_json, dict) else book.content_json
    
    return render(request, 'books/edit.html', {
        'book': book,
        'initial_content': initial_content
    })


@login_required
def book_delete(request, slug):
    """Delete a book recommendation (only for drafts/pending, or owner)."""
    book = get_object_or_404(BookRecommendation, slug=slug, added_by=request.user)
    
    if book.is_published and book.is_approved and not request.user.is_staff:
        messages.error(request, 'Published book recommendations cannot be deleted. Please contact an administrator.')
        return redirect('books:detail', slug=slug)
    
    if request.method == 'POST':
        book_title = book.book_title
        book.delete()
        messages.success(request, f'Book recommendation "{book_title}" has been deleted.')
        return redirect('users:dashboard')
    
    return render(request, 'books/delete.html', {'book': book})


@login_required
def book_rate(request, slug):
    """Rate a book (HTMX endpoint)."""
    book = get_object_or_404(BookRecommendation, slug=slug, is_published=True, is_approved=True)
    
    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 0))
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be 1-5")
            
            review_text = request.POST.get('review_text', '').strip()
            
            user_rating, created = UserBookRating.objects.update_or_create(
                book=book,
                user=request.user,
                defaults={'rating': rating, 'review_text': review_text}
            )
            
            if created:
                messages.success(request, 'Thank you for rating this book!')
            else:
                messages.success(request, 'Your rating has been updated!')
                
        except (ValueError, TypeError) as e:
            messages.error(request, str(e))
    
    return redirect('books:detail', slug=slug)