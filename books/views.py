import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import slugify
from .models import BookReview


def get_cached_book_tags():
    """Cache tags for 30 minutes"""
    tags = cache.get('book_tags')
    if tags is None:
        from taggit.models import Tag
        tags = list(Tag.objects.filter(bookreview__isnull=False).distinct()[:50])
        cache.set('book_tags', tags, 1800)
    return tags


def get_book_recommendations(review, count=9):
    """Efficient recommendation fetching"""
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
        reviews = reviews.filter(rating__gte=int(rating))
    
    sort = request.GET.get('sort', '-created_at')
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
    review = get_object_or_404(
        BookReview.objects.select_related('reviewer'),
        slug=slug, is_published=True, is_approved=True
    )
    
    previous_review = BookReview.objects.filter(
        is_published=True,
        is_approved=True,
        pk__lt=review.pk
    ).order_by('-pk').only('id', 'review_title', 'slug').first()
    
    next_review = BookReview.objects.filter(
        is_published=True,
        is_approved=True,
        pk__gt=review.pk
    ).order_by('pk').only('id', 'review_title', 'slug').first()
    
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
    if request.method == 'POST':
        book_title = request.POST.get('book_title')
        review_title = request.POST.get('review_title')
        content_json = request.POST.get('content_json')
        action = request.POST.get('action')
        
        if not book_title or not review_title or not content_json:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'books/create.html')
        
        base_slug = slugify(review_title)
        slug = base_slug
        counter = 1
        while BookReview.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
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
            content_data = json.loads(content_json) if isinstance(content_json, str) else content_json
        except json.JSONDecodeError:
            content_data = content_json
        
        review = BookReview.objects.create(
            book_title=book_title,
            author=request.POST.get('author'),
            isbn=request.POST.get('isbn', ''),
            publisher=request.POST.get('publisher', ''),
            publication_year=request.POST.get('publication_year') or None,
            review_title=review_title,
            slug=slug,
            content_json=content_data,
            rating=int(request.POST.get('rating')),
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
        if request.FILES.get('alternate_cover'):
            review.alternate_cover = request.FILES['alternate_cover']
        
        tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
        if tags:
            review.tags.add(*tags)
        
        review.save()
        
        cache.delete('book_tags')
        
        return redirect('users:dashboard')
    
    return render(request, 'books/create.html')


@login_required
def book_edit(request, slug):
    review = get_object_or_404(BookReview, slug=slug, reviewer=request.user)
    
    if request.method == 'POST':
        review.book_title = request.POST.get('book_title')
        review.author = request.POST.get('author')
        review.isbn = request.POST.get('isbn', '')
        review.publisher = request.POST.get('publisher', '')
        review.publication_year = request.POST.get('publication_year') or None
        review.review_title = request.POST.get('review_title')
        
        content_json = request.POST.get('content_json')
        if content_json:
            try:
                review.content_json = json.loads(content_json) if isinstance(content_json, str) else content_json
            except json.JSONDecodeError:
                review.content_json = content_json
        
        review.rating = int(request.POST.get('rating'))
        
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
        if request.FILES.get('alternate_cover'):
            review.alternate_cover = request.FILES['alternate_cover']
        
        review.tags.clear()
        tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
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
