"""
Book review views for browsing and managing book reviews.
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
from django.core.mail import send_mail  # Added
from django.conf import settings        # Added
from django.contrib.auth import get_user_model # Added

from .models import BookRecommendation, UserBookRating
from core.validators import ALLOWED_BOOK_SORTS, get_safe_sort
from core.editorjs_helpers import parse_editorjs_content, generate_unique_slug, get_workflow_flags

User = get_user_model()

def get_book_recommendations(review, count=9):
    """
    Recommendation strategy: Recent books.
    """
    recommendations = BookRecommendation.objects.filter(
        is_published=True,
        is_approved=True
    ).exclude(pk=review.pk).select_related('added_by').only(
        'id', 'book_title', 'title', 'slug', 'cover_image',
        'created_at', 'added_by__full_name', 'added_by__username'
    ).order_by('-created_at')
    
    return recommendations[:count]


def book_list(request):
    """List all published book reviews with filtering and pagination."""
    reviews = BookRecommendation.objects.filter(
        is_published=True, is_approved=True
    ).select_related('added_by').only(
        'id', 'book_title', 'title', 'slug', 'cover_image',
        'created_at', 'added_by__full_name', 'added_by__username'
    )
    
    if search := request.GET.get('search'):
        reviews = reviews.filter(
            Q(book_title__icontains=search) | Q(title__icontains=search)
        )
    
    sort = get_safe_sort(request.GET.get('sort', '-created_at'), ALLOWED_BOOK_SORTS)
    reviews = reviews.order_by(sort)
    
    paginator = Paginator(reviews, 12)
    reviews_page = paginator.get_page(request.GET.get('page'))
    
    context = {
        'reviews': reviews_page,
    }
    
    if request.htmx:
        return render(request, 'books/partials/book_grid.html', context)
    
    return render(request, 'books/list.html', context)


def book_detail(request, slug):
    """Display a single book review with recommendations."""
    review = get_object_or_404(
        BookRecommendation.objects.select_related('added_by'),
        slug=slug, is_published=True, is_approved=True
    )
    
    previous_review = BookRecommendation.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__lt=review.created_at
    ).order_by('-created_at').only('id', 'title', 'slug').first()
    
    next_review = BookRecommendation.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__gt=review.created_at
    ).order_by('created_at').only('id', 'title', 'slug').first()
    
    recommended = get_book_recommendations(review, 9)
    
    context = {
        'review': review,
        'previous_review': previous_review,
        'next_review': next_review,
        'recommended': recommended,
    }
    
    return render(request, 'books/detail.html', context)


@login_required
def book_create(request):
    """Create a new book review."""
    if request.method == 'POST':
        book_title = request.POST.get('book_title', '').strip()
        review_title = request.POST.get('review_title', '').strip()
        content_json = request.POST.get('content_json')
        action = request.POST.get('action')
        
        if not book_title or not review_title or not content_json:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'books/create.html')
        
        try:
            content_data = json.loads(content_json) if isinstance(content_json, str) else content_json
        except json.JSONDecodeError:
            messages.error(request, 'Invalid content format. Please try again.')
            return render(request, 'books/create.html')
        
        base_slug = slugify(review_title)[:200]
        slug = base_slug
        counter = 1
        while BookRecommendation.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            if counter > 100:
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                break
        
        is_published = False
        is_approved = False
        pending_approval = False
        submitted_at = None
        
        if action == 'submit':
            pending_approval = True
            submitted_at = timezone.now()
            messages.success(request, 'Your book review has been submitted for approval!')
        else:
            messages.success(request, 'Your book review has been saved as a draft!')
        
        try:
            publication_year = int(request.POST.get('publication_year'))
            if publication_year < 1000 or publication_year > timezone.now().year + 1:
                publication_year = None
        except (ValueError, TypeError):
            publication_year = None
        
        review = BookRecommendation(
            book_title=book_title,
            author=request.POST.get('author', '').strip(),
            isbn=request.POST.get('isbn', '').strip()[:20],
            publisher=request.POST.get('publisher', '').strip(),
            publication_year=publication_year,
            title=review_title[:200],
            slug=slug,
            content_json=content_data,
            added_by=request.user,
            is_published=is_published,
            is_approved=is_approved,
            pending_approval=pending_approval,
            submitted_at=submitted_at,
        )
        
        if request.FILES.get('cover_image'):
            review.cover_image = request.FILES['cover_image']
        if request.FILES.get('cover_image_back'):
            review.cover_image_back = request.FILES['cover_image_back']
        if request.FILES.get('alternate_cover'):
            review.alternate_cover = request.FILES['alternate_cover']
        
        # Validate file uploads through model validators
        try:
            review.full_clean()
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return render(request, 'books/create.html')
        
        review.save()
        
        # --- PHASE 4: EMAIL NOTIFICATION ---
        if action == 'submit':
            try:
                staff_emails = list(User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True))
                if staff_emails:
                    send_mail(
                        subject=f"New Book Review Submitted: {review.title}",
                        message=f"""
                        A new book review has been submitted by {request.user.get_full_name() or request.user.username}.
                        
                        Book: {review.book_title}
                        Title: {review.title}
                        
                        Review it here: {request.scheme}://{request.get_host()}/users/admin/moderation/
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=staff_emails,
                        fail_silently=True
                    )
            except Exception as e:
                logger.warning(f"Failed to send notification email: {e}")
        # -----------------------------------
        
        return redirect('users:dashboard')
    
    return render(request, 'books/create.html')


@login_required
def book_edit(request, slug):
    """Edit an existing book review."""
    review = get_object_or_404(BookRecommendation, slug=slug, added_by=request.user)
    
    if request.method == 'POST':
        review.book_title = request.POST.get('book_title', '').strip()
        review.author = request.POST.get('author', '').strip()
        review.isbn = request.POST.get('isbn', '').strip()[:20]
        review.publisher = request.POST.get('publisher', '').strip()
        
        try:
            publication_year = int(request.POST.get('publication_year'))
            if publication_year < 1000 or publication_year > timezone.now().year + 1:
                publication_year = None
        except (ValueError, TypeError):
            publication_year = None
        review.publication_year = publication_year
        
        review.title = request.POST.get('review_title', '').strip()
        
        content_json = request.POST.get('content_json')
        if content_json:
            try:
                review.content_json = parse_editorjs_content(content_json)
            except ValidationError as e:
                messages.error(request, str(e))
                return render(request, 'books/edit.html', {
                    'review': review,
                    'initial_content': content_json
                })
        
        action = request.POST.get('action')
        if action == 'submit':
            workflow_flags = get_workflow_flags(action, is_submit=True)
            review.pending_approval = workflow_flags['pending_approval']
            review.submitted_at = workflow_flags['submitted_at']
            review.is_published = workflow_flags['is_published']
            review.is_approved = workflow_flags['is_approved']
            messages.success(request, 'Your book review has been submitted for approval!')
        else:
            if review.is_published and review.is_approved:
                review.pending_approval = True
                review.is_published = False
                review.is_approved = False
            messages.success(request, 'Your book review has been saved!')
        
        if request.FILES.get('cover_image'):
            review.cover_image = request.FILES['cover_image']
        if request.FILES.get('cover_image_back'):
            review.cover_image_back = request.FILES['cover_image_back']
        if request.FILES.get('alternate_cover'):
            review.alternate_cover = request.FILES['alternate_cover']
        
        review.save()
        
        # --- PHASE 4: EMAIL NOTIFICATION ON RESUBMIT ---
        if action == 'submit':
            try:
                staff_emails = list(User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True))
                if staff_emails:
                    send_mail(
                        subject=f"Book Review Updated (Review Needed): {review.title}",
                        message=f"User {request.user.username} updated a book review. Please re-review.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=staff_emails,
                        fail_silently=True
                    )
            except Exception:
                pass
        # -----------------------------------------------
        
        return redirect('users:dashboard')
    
    initial_content = ''
    if review.content_json:
        initial_content = json.dumps(review.content_json) if isinstance(review.content_json, dict) else review.content_json
    
    return render(request, 'books/edit.html', {
        'review': review,
        'initial_content': initial_content
    })


@login_required
def book_delete(request, slug):
    """Delete a book review (only for drafts/pending, or owner)."""
    review = get_object_or_404(BookRecommendation, slug=slug, added_by=request.user)
    
    if review.is_published and review.is_approved and not request.user.is_staff:
        messages.error(request, 'Published book reviews cannot be deleted. Please contact an administrator.')
        return redirect('books:detail', slug=slug)
    
    if request.method == 'POST':
        review_title = review.title
        review.delete()
        messages.success(request, f'Book review "{review_title}" has been deleted.')
        return redirect('users:dashboard')
    
    return render(request, 'books/delete.html', {'review': review})