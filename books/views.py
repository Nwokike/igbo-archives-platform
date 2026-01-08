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
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import slugify
from .models import BookReview
from core.validators import ALLOWED_BOOK_SORTS, get_safe_sort


def get_cached_book_tags():
    """Cache tags for 30 minutes."""
    tags = cache.get('book_tags')
    if tags is None:
        from taggit.models import Tag
        tags = list(Tag.objects.filter(bookreview__isnull=False).distinct()[:50])
        cache.set('book_tags', tags, 1800)
    return tags


def get_book_recommendations(review, count=9):
    """Efficient recommendation fetching based on shared tags."""
    tag_names = list(review.tags.values_list('name', flat=True))
    
    recommendations = BookReview.objects.filter(
        is_published=True,
        is_approved=True
    ).exclude(pk=review.pk).select_related('reviewer').only(
        'id', 'book_title', 'review_title', 'slug', 'rating', 'cover_image',
        'created_at', 'reviewer__full_name', 'reviewer__username'
    )
    
    if tag_names:
        recommendations = recommendations.annotate(
            tag_matches=Count('tags', filter=Q(tags__name__in=tag_names))
        ).order_by('-tag_matches', '-created_at')
    else:
        recommendations = recommendations.order_by('-created_at')
    
    return recommendations[:count]


def book_list(request):
    """List all published book reviews with filtering and pagination."""
    reviews = BookReview.objects.filter(
        is_published=True, is_approved=True
    ).select_related('reviewer').prefetch_related('tags').only(
        'id', 'book_title', 'review_title', 'slug', 'rating', 'cover_image',
        'created_at', 'reviewer__full_name', 'reviewer__username'
    )
    
    if search := request.GET.get('search'):
        reviews = reviews.filter(
            Q(book_title__icontains=search) | Q(review_title__icontains=search)
        )
    
    if tag := request.GET.get('tag'):
        reviews = reviews.filter(tags__name=tag)
    
    if rating := request.GET.get('rating'):
        try:
            reviews = reviews.filter(rating__gte=int(rating))
        except ValueError:
            pass
    
    sort = get_safe_sort(request.GET.get('sort', '-created_at'), ALLOWED_BOOK_SORTS)
    reviews = reviews.order_by(sort)
    
    paginator = Paginator(reviews, 12)
    reviews = paginator.get_page(request.GET.get('page'))
    
    context = {
        'reviews': reviews,
        'tags': get_cached_book_tags()
    }
    
    if request.htmx:
        return render(request, 'books/partials/book_grid.html', context)
    
    return render(request, 'books/list.html', context)


def book_detail(request, slug):
    """Display a single book review with recommendations."""
    review = get_object_or_404(
        BookReview.objects.select_related('reviewer'),
        slug=slug, is_published=True, is_approved=True
    )
    
    previous_review = BookReview.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__lt=review.created_at
    ).order_by('-created_at').only('id', 'review_title', 'slug').first()
    
    next_review = BookReview.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__gt=review.created_at
    ).order_by('created_at').only('id', 'review_title', 'slug').first()
    
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
        while BookReview.objects.filter(slug=slug).exists():
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
            rating = int(request.POST.get('rating', 3))
            rating = max(1, min(5, rating))
        except (ValueError, TypeError):
            rating = 3
        
        try:
            publication_year = int(request.POST.get('publication_year'))
            if publication_year < 1000 or publication_year > timezone.now().year + 1:
                publication_year = None
        except (ValueError, TypeError):
            publication_year = None
        
        review = BookReview(
            book_title=book_title,
            author=request.POST.get('author', '').strip(),
            isbn=request.POST.get('isbn', '').strip()[:20],
            publisher=request.POST.get('publisher', '').strip(),
            publication_year=publication_year,
            review_title=review_title,
            slug=slug,
            content_json=content_data,
            rating=rating,
            reviewer=request.user,
            is_published=is_published,
            is_approved=is_approved,
            pending_approval=pending_approval,
            submitted_at=submitted_at
        )
        
        if request.FILES.get('cover_image'):
            review.cover_image = request.FILES['cover_image']
        if request.FILES.get('cover_image_back'):
            review.cover_image_back = request.FILES['cover_image_back']
        
        # Validate file uploads through model validators before saving
        from django.core.exceptions import ValidationError
        try:
            review.full_clean()
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return render(request, 'books/create.html')
        
        # Save after successful validation
        review.save()
        
        tags = [t.strip()[:50] for t in request.POST.get('tags', '').split(',') if t.strip()][:20]
        if tags:
            review.tags.add(*tags)
        
        cache.delete('book_tags')
        
        return redirect('users:dashboard')
    
    return render(request, 'books/create.html')


@login_required
def book_edit(request, slug):
    """Edit an existing book review."""
    review = get_object_or_404(BookReview, slug=slug, reviewer=request.user)
    
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
        
        review.review_title = request.POST.get('review_title', '').strip()
        
        content_json = request.POST.get('content_json')
        if content_json:
            try:
                review.content_json = json.loads(content_json) if isinstance(content_json, str) else content_json
            except json.JSONDecodeError:
                messages.error(request, 'Invalid content format. Please try again.')
                return render(request, 'books/edit.html', {
                    'review': review,
                    'initial_content': content_json
                })
        
        try:
            rating = int(request.POST.get('rating', review.rating))
            review.rating = max(1, min(5, rating))
        except (ValueError, TypeError):
            pass
        
        action = request.POST.get('action')
        if action == 'submit':
            review.pending_approval = True
            review.submitted_at = timezone.now()
            review.is_published = False
            review.is_approved = False
            messages.success(request, 'Your book review has been submitted for approval!')
        else:
            messages.success(request, 'Your book review has been saved!')
        
        if request.FILES.get('cover_image'):
            review.cover_image = request.FILES['cover_image']
        if request.FILES.get('cover_image_back'):
            review.cover_image_back = request.FILES['cover_image_back']
        
        review.tags.clear()
        tags = [t.strip()[:50] for t in request.POST.get('tags', '').split(',') if t.strip()][:20]
        if tags:
            review.tags.add(*tags)
        
        review.save()
        cache.delete('book_tags')
        
        return redirect('users:dashboard')
    
    initial_content = ''
    if review.content_json:
        initial_content = json.dumps(review.content_json) if isinstance(review.content_json, dict) else review.content_json
    
    return render(request, 'books/edit.html', {
        'review': review,
        'initial_content': initial_content
    })
