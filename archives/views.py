import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from .models import Archive, Category


def get_cached_categories():
    """Cache categories for 1 hour - they rarely change"""
    categories = cache.get('archive_categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('archive_categories', categories, 3600)
    return categories


def get_random_recommendations(exclude_pk, category=None, tag_names=None, count=9):
    """Memory-efficient random archive selection"""
    cache_key = 'archive_ids_pool'
    archive_ids = cache.get(cache_key)
    
    if archive_ids is None:
        archive_ids = list(
            Archive.objects.filter(is_approved=True)
            .values_list('id', flat=True)[:500]
        )
        cache.set(cache_key, archive_ids, 300)
    
    available_ids = [aid for aid in archive_ids if aid != exclude_pk]
    
    if not available_ids:
        return Archive.objects.none()
    
    random_ids = random.sample(available_ids, min(count, len(available_ids)))
    return Archive.objects.filter(pk__in=random_ids).select_related('uploaded_by', 'category')


def archive_list(request):
    archives = Archive.objects.filter(is_approved=True).select_related(
        'uploaded_by', 'category'
    ).prefetch_related('tags').only(
        'id', 'title', 'archive_type', 'image', 'featured_image',
        'alt_text', 'created_at', 'uploaded_by_id', 'category_id',
        'uploaded_by__full_name', 'uploaded_by__username',
        'category__name', 'category__slug'
    )
    
    if category := request.GET.get('category'):
        archives = archives.filter(category__slug=category)
    
    if search := request.GET.get('search'):
        archives = archives.filter(title__icontains=search)
    
    if archive_type := request.GET.get('type'):
        archives = archives.filter(archive_type=archive_type)
    
    sort = request.GET.get('sort', '-created_at')
    archives = archives.order_by(sort)
    
    paginator = Paginator(archives, 12)
    archives = paginator.get_page(request.GET.get('page'))
    
    context = {
        'archives': archives,
        'categories': get_cached_categories(),
    }
    
    if request.htmx:
        return render(request, 'archives/partials/archive_grid.html', context)
    
    return render(request, 'archives/list.html', context)


def archive_detail(request, pk):
    archive = get_object_or_404(
        Archive.objects.select_related('uploaded_by', 'category'),
        pk=pk, is_approved=True
    )
    
    previous_archive = Archive.objects.filter(
        is_approved=True, pk__lt=archive.pk
    ).order_by('-pk').only('id', 'title').first()
    
    next_archive = Archive.objects.filter(
        is_approved=True, pk__gt=archive.pk
    ).order_by('pk').only('id', 'title').first()
    
    tag_names = list(archive.tags.values_list('name', flat=True))
    recommended = get_random_recommendations(
        archive.pk, 
        category=archive.category,
        tag_names=tag_names,
        count=9
    )
    
    context = {
        'archive': archive,
        'previous_archive': previous_archive,
        'next_archive': next_archive,
        'recommended': recommended,
    }
    
    return render(request, 'archives/detail.html', context)


@login_required
def archive_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        archive_type = request.POST.get('archive_type')
        category_id = request.POST.get('category')
        caption = request.POST.get('caption')
        alt_text = request.POST.get('alt_text', '')
        original_author = request.POST.get('original_author', '')
        location = request.POST.get('location', '')
        date_created = request.POST.get('date_created') or None
        circa_date = request.POST.get('circa_date', '')
        
        if not title or not description or not archive_type or not caption:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'archives/create.html', {'categories': get_cached_categories()})
        
        archive = Archive(
            title=title,
            description=description,
            archive_type=archive_type,
            category_id=category_id if category_id else None,
            caption=caption,
            alt_text=alt_text,
            original_author=original_author,
            location=location,
            date_created=date_created,
            circa_date=circa_date,
            uploaded_by=request.user,
            is_approved=False
        )
        
        if archive_type == 'image' and request.FILES.get('image'):
            archive.image = request.FILES['image']
        elif archive_type == 'video' and request.FILES.get('video'):
            archive.video = request.FILES['video']
            if request.FILES.get('featured_image'):
                archive.featured_image = request.FILES['featured_image']
        elif archive_type == 'document' and request.FILES.get('document'):
            archive.document = request.FILES['document']
        elif archive_type == 'audio' and request.FILES.get('audio'):
            archive.audio = request.FILES['audio']
            if request.FILES.get('featured_image'):
                archive.featured_image = request.FILES['featured_image']
        else:
            messages.error(request, f'Please upload a file for {archive_type} type.')
            return redirect('archives:create')
        
        try:
            archive.save()
            
            tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
            if tags:
                archive.tags.add(*tags)
            
            cache.delete('archive_ids_pool')
            cache.delete('featured_archive_ids')
            
            messages.success(request, 'Archive uploaded successfully!')
            return redirect('archives:detail', pk=archive.pk)
        except Exception as e:
            messages.error(request, f'Error uploading archive: {str(e)}')
            return redirect('archives:create')
    
    return render(request, 'archives/create.html', {'categories': get_cached_categories()})


@login_required
def archive_edit(request, pk):
    archive = get_object_or_404(Archive, pk=pk, uploaded_by=request.user)
    
    if request.method == 'POST':
        archive.title = request.POST.get('title')
        archive.description = request.POST.get('description')
        archive.archive_type = request.POST.get('archive_type')
        archive.category_id = request.POST.get('category') if request.POST.get('category') else None
        archive.caption = request.POST.get('caption')
        archive.alt_text = request.POST.get('alt_text', '')
        archive.original_author = request.POST.get('original_author', '')
        archive.location = request.POST.get('location', '')
        archive.date_created = request.POST.get('date_created') or None
        archive.circa_date = request.POST.get('circa_date', '')
        
        if request.FILES.get('image'):
            archive.image = request.FILES['image']
        if request.FILES.get('video'):
            archive.video = request.FILES['video']
        if request.FILES.get('document'):
            archive.document = request.FILES['document']
        if request.FILES.get('audio'):
            archive.audio = request.FILES['audio']
        if request.FILES.get('featured_image'):
            archive.featured_image = request.FILES['featured_image']
        
        archive.tags.clear()
        tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
        if tags:
            archive.tags.add(*tags)
        
        archive.save()
        
        cache.delete('archive_ids_pool')
        cache.delete('featured_archive_ids')
        
        messages.success(request, 'Archive updated successfully!')
        return redirect('archives:detail', pk=archive.pk)
    
    return render(request, 'archives/edit.html', {'archive': archive, 'categories': get_cached_categories()})
