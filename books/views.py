from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import BookReview
from django.core.paginator import Paginator
from django.utils.text import slugify
import json

def book_list(request):
    from taggit.models import Tag
    
    reviews = BookReview.objects.filter(is_published=True, is_approved=True)
    
    search = request.GET.get('search')
    if search:
        reviews = reviews.filter(book_title__icontains=search) | reviews.filter(review_title__icontains=search)
    
    tag = request.GET.get('tag')
    if tag:
        reviews = reviews.filter(tags__name=tag)
    
    rating = request.GET.get('rating')
    if rating:
        reviews = reviews.filter(rating__gte=int(rating))
    
    sort = request.GET.get('sort', '-created_at')
    reviews = reviews.order_by(sort)
    
    paginator = Paginator(reviews, 12)
    page = request.GET.get('page')
    reviews = paginator.get_page(page)
    
    tags = Tag.objects.filter(bookreview__isnull=False).distinct()
    
    context = {
        'reviews': reviews,
        'tags': tags
    }
    
    if request.htmx:
        return render(request, 'books/partials/book_grid.html', context)
    
    return render(request, 'books/list.html', context)

def book_detail(request, slug):
    review = get_object_or_404(BookReview, slug=slug, is_published=True, is_approved=True)
    
    # Get previous and next reviews
    previous_review = BookReview.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__lt=review.created_at
    ).order_by('-created_at').first()
    
    next_review = BookReview.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__gt=review.created_at
    ).order_by('created_at').first()
    
    # Get recommended reviews (9 total: same tags, same rating, or recent)
    recommended = BookReview.objects.filter(
        is_published=True,
        is_approved=True
    ).exclude(slug=review.slug)
    
    tag_names = review.tags.values_list('name', flat=True)
    if tag_names:
        recommended = recommended.filter(tags__name__in=tag_names).distinct()
    
    # If we need more, add by rating
    if recommended.count() < 9:
        recommended = BookReview.objects.filter(
            is_published=True,
            is_approved=True,
            rating=review.rating
        ).exclude(slug=review.slug)
    
    # If still need more, add recent
    if recommended.count() < 9:
        recommended = BookReview.objects.filter(
            is_published=True,
            is_approved=True
        ).exclude(slug=review.slug).order_by('-created_at')
    
    recommended = recommended[:9]
    
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
        action = request.POST.get('action')  # 'save' or 'submit'
        
        if not book_title or not review_title or not content_json:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'books/create.html')
        
        # Generate unique slug
        base_slug = slugify(review_title)
        slug = base_slug
        counter = 1
        while BookReview.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Determine publishing status
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
        
        review = BookReview.objects.create(
            book_title=book_title,
            author=request.POST.get('author'),
            isbn=request.POST.get('isbn', ''),
            publisher=request.POST.get('publisher', ''),
            publication_year=request.POST.get('publication_year') or None,
            review_title=review_title,
            slug=slug,
            content_json=content_json,
            rating=int(request.POST.get('rating')),
            reviewer=request.user,
            is_published=is_published,
            is_approved=is_approved,
            pending_approval=pending_approval,
            submitted_at=submitted_at
        )
        
        # Handle multiple cover images
        if request.FILES.get('cover_image'):
            review.cover_image = request.FILES['cover_image']
        if request.FILES.get('cover_image_back'):
            review.cover_image_back = request.FILES['cover_image_back']
        if request.FILES.get('alternate_cover'):
            review.alternate_cover = request.FILES['alternate_cover']
        
        tags = request.POST.get('tags', '').split(',')
        for tag in tags:
            if tag.strip():
                review.tags.add(tag.strip())
        
        review.save()
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
        tags = request.POST.get('tags', '').split(',')
        for tag in tags:
            if tag.strip():
                review.tags.add(tag.strip())
        
        review.save()
        return redirect('users:dashboard')
    
    initial_content = ''
    if review.content_json:
        initial_content = review.content_json
    
    return render(request, 'books/edit.html', {
        'review': review,
        'initial_content': initial_content
    })
