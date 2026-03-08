"""
Book recommendation views for browsing and managing recommended Igbo books.
Users can rate and review books - the app is for listing/recommending, not reviewing.
"""
import json
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Q, Avg, Count
from django.http import Http404
from django.utils import timezone
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

from .models import BookRecommendation, UserBookRating
from core.validators import ALLOWED_BOOK_SORTS, get_safe_sort
from core.editorjs_helpers import parse_editorjs_content, get_workflow_flags, generate_unique_slug
from core.image_utils import compress_image
from core.turnstile import verify_turnstile
from core.notifications_utils import send_new_review_notification

logger = logging.getLogger(__name__)
User = get_user_model()


def get_latest_books(book, count=9):
    """
    Get latest book recommendations (excluding current book).
    """
    related = BookRecommendation.objects.filter(
        is_published=True,
        is_approved=True
    ).exclude(pk=book.pk).select_related('added_by').only(
        'id', 'book_title', 'title', 'slug', 'cover_image',
        'created_at', 'added_by__full_name', 'added_by__username'
    ).annotate(
        avg_rating=Avg('ratings__rating'),
        review_count=Count('ratings'),
    ).order_by('-created_at')
    
    return related[:count]


def book_list(request):
    """List all published book recommendations with filtering and pagination."""
    books = BookRecommendation.objects.filter(
        is_published=True, is_approved=True
    ).select_related('added_by').only(
        'id', 'book_title', 'title', 'slug', 'cover_image', 'author',
        'publication_year', 'created_at', 'added_by__full_name', 'added_by__username'
    ).annotate(
        avg_rating=Avg('ratings__rating'),
        review_count=Count('ratings'),
    )
    
    if search := request.GET.get('search'):
        books = books.filter(
            Q(book_title__icontains=search) | 
            Q(title__icontains=search) |
            Q(author__icontains=search)
        )
    
    if author := request.GET.get('author'):
        books = books.filter(author__icontains=author)
    
    if year := request.GET.get('year'):
        # Validate and use integer comparison instead of icontains on IntegerField
        try:
            books = books.filter(publication_year=int(year))
        except (ValueError, TypeError):
            pass  # Ignore invalid year strings
    
    sort = get_safe_sort(request.GET.get('sort', '-created_at'), ALLOWED_BOOK_SORTS)
    books = books.order_by(sort, '-created_at')
    
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
        slug=slug
    )
    
    # Allow owners and staff to see unapproved books, 404 for everyone else
    if not book.is_published or not book.is_approved:
        if not request.user.is_authenticated or (request.user != book.added_by and not request.user.is_staff):
            raise Http404("Book not found")
    
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
    
    related_books = get_latest_books(book, 9)
    
    # Get user's existing rating if logged in
    user_rating = None
    if request.user.is_authenticated:
        user_rating = UserBookRating.objects.filter(book=book, user=request.user).first()
    
    # Get all reviews for this book
    reviews = UserBookRating.objects.filter(book=book).select_related('user').order_by('-created_at')

    # Extract plain text excerpt from EditorJS content for SEO meta tags
    content_excerpt = ''
    if book.content_json and isinstance(book.content_json, dict):
        blocks = book.content_json.get('blocks', [])
        text_parts = []
        for block in blocks:
            text = block.get('data', {}).get('text', '')
            if text:

                clean = re.sub(r'<[^>]+>', '', text)
                text_parts.append(clean)
                if len(' '.join(text_parts)) > 200:
                    break
        content_excerpt = ' '.join(text_parts)[:300]
    elif book.legacy_content:
        content_excerpt = book.legacy_content[:300]

    context = {
        'book': book,
        'content_excerpt': content_excerpt,
        'previous_book': previous_book,
        'next_book': next_book,
        'related_books': related_books,
        'user_rating': user_rating,
        'reviews': reviews,
        'turnstile_site_key': getattr(settings, 'TURNSTILE_SITE_KEY', ''),
    }
    
    # Author profile lookup for bio/description
    if book.author:
        from archives.models import Author
        context['author_profile'] = Author.objects.filter(name__iexact=book.author).first()
    
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
        
        # Use parse_editorjs_content for consistent sanitization
        try:
            content_data = parse_editorjs_content(content_json)
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'books/create.html')
        
        slug = generate_unique_slug(recommendation_title, BookRecommendation)
        
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
        
        try:
            publication_year = int(request.POST.get('publication_year'))
            if publication_year < 1000 or publication_year > timezone.now().year + 1:
                publication_year = None
        except (ValueError, TypeError):
            publication_year = None
        
        author_name = request.POST.get('author', '').strip()
        author_about_text = request.POST.get('author_about', '').strip()
        
        book = BookRecommendation(
            book_title=book_title,
            author=author_name,
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
        
        # Link author to central database profile
        if author_name:
            from archives.models import Author
            author_obj = Author.objects.filter(name__iexact=author_name).first()
            if not author_obj:
                author_obj = Author.objects.create(name=author_name)
            if author_about_text and not author_obj.description:
                author_obj.description = author_about_text
                author_obj.save()
        
        if request.FILES.get('cover_image'):
            book.cover_image = compress_image(request.FILES['cover_image'])
        
        try:
            book.full_clean()
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return render(request, 'books/create.html')
        
        book.save()
        
        # Notifications — AFTER book.save() to avoid NameError
        if action == 'submit':
            messages.success(request, 'Your book recommendation has been submitted for approval!')
            # Bell Notification
            try:
                from core.notifications_utils import send_post_submitted_notification
                send_post_submitted_notification(book, post_type='book recommendation')
            except Exception as e:
                logger.warning(f"Failed to send in-app notification: {e}")
            
            # Email notification (async)
            try:
                from core.notifications_utils import send_admin_notification
                send_admin_notification(
                    subject=f"New Book Recommendation: {book.book_title}",
                    description=f"A new book recommendation has been submitted by {request.user.get_display_name()}.\n\nBook: {book.book_title}\nTitle: {book.title}",
                    target_url="/users/admin/moderation/"
                )
            except Exception as e:
                logger.warning(f"Failed to send notification email: {e}")
        else:
            messages.success(request, 'Your book recommendation has been saved as a draft!')
        
        return redirect('users:dashboard')
    
    return render(request, 'books/create.html')


@login_required
def book_edit(request, slug):
    """Edit an existing book recommendation."""
    book = get_object_or_404(BookRecommendation, slug=slug, added_by=request.user)
    
    if request.method == 'POST':
        author_name = request.POST.get('author', '').strip()
        author_about_text = request.POST.get('author_about', '').strip()
        
        book.book_title = request.POST.get('book_title', '').strip()
        book.author = author_name
        
        if author_name:
            from archives.models import Author
            author_obj = Author.objects.filter(name__iexact=author_name).first()
            if not author_obj:
                author_obj = Author.objects.create(name=author_name)
            if author_about_text and not author_obj.description:
                author_obj.description = author_about_text
                author_obj.save()
        
        # Check for duplicate ISBN (excluding current book)
        new_isbn = request.POST.get('isbn', '').strip()[:20]
        if new_isbn and new_isbn != book.isbn:
            existing_book = BookRecommendation.objects.filter(isbn__iexact=new_isbn).exclude(pk=book.pk).first()
            if existing_book:
                messages.error(
                    request, 
                    f'A book with ISBN/ASIN "{new_isbn}" already exists. Search for "{existing_book.book_title}" to view it.'
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
            # Bell Notification
            try:
                from core.notifications_utils import send_post_submitted_notification
                send_post_submitted_notification(book, post_type='book recommendation')
            except Exception as e:
                logger.warning(f"Failed to send in-app notification: {e}")
        else:
            if book.is_published and book.is_approved:
                book.pending_approval = True
                book.is_approved = False
            messages.success(request, 'Your book recommendation has been saved!')
        
        if request.FILES.get('cover_image'):
            book.cover_image = compress_image(request.FILES['cover_image'])
        
        book.save()
        
        # Email notification on resubmit (async)
        if action == 'submit':
            try:
                from core.notifications_utils import send_admin_notification
                send_admin_notification(
                    subject=f"Book Recommendation Updated: {book.book_title}",
                    description=f"User {request.user.username} updated a book recommendation. Please review.",
                    target_url="/users/admin/moderation/"
                )
            except Exception:
                pass
        
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
    turnstile_site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
    
    if request.method == 'POST':
        # Verify Turnstile
        token = request.POST.get('cf-turnstile-response')
        turnstile_result = verify_turnstile(token)
        
        if not turnstile_result.get('success', False):
            messages.error(request, 'Security check failed. Please refresh and try again.')
            if request.htmx:
                # Return the sidebar partial even on error so messages show
                user_rating = UserBookRating.objects.filter(book=book, user=request.user).first()
                reviews = UserBookRating.objects.filter(book=book).select_related('user').order_by('-created_at')
                return render(request, 'books/partials/reviews_sidebar.html', {
                    'book': book, 
                    'user_rating': user_rating, 
                    'reviews': reviews,
                    'turnstile_site_key': turnstile_site_key
                })
            return redirect('books:detail', slug=slug)

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
                # Bell Notification
                try:
                    from core.notifications_utils import send_review_posted_notification
                    send_review_posted_notification(request.user, book)
                except Exception as e:
                    logger.warning(f"Failed to send review notification: {e}")
                
                # Also notify the book owner
                try:
                    send_new_review_notification(user_rating, book)
                except Exception as e:
                    logger.warning(f"Failed to send new review notification to owner: {e}")

                
        except (ValueError, TypeError) as e:
            messages.error(request, str(e))
            
    # HTMX Response: Re-render ONLY the sidebar
    if request.htmx:
        # Refresh the context data
        user_rating = UserBookRating.objects.filter(book=book, user=request.user).first()
        reviews = UserBookRating.objects.filter(book=book).select_related('user').order_by('-created_at')
        
        return render(request, 'books/partials/reviews_sidebar.html', {
            'book': book,
            'user_rating': user_rating,
            'reviews': reviews,
            'turnstile_site_key': turnstile_site_key,
        })
    
    return redirect('books:detail', slug=slug)
