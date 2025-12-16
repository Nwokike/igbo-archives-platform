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


def get_all_approved_archive_ids():
    """Cache all approved archive IDs using chunked iteration.
    
    Memory estimate: 100,000 IDs * 8 bytes = ~800KB, well within 1GB constraint.
    Uses iterator() for memory-efficient fetching.
    """
    cache_key = 'all_approved_archive_ids'
    archive_ids = cache.get(cache_key)
    
    if archive_ids is None:
        archive_ids = tuple(
            Archive.objects.filter(is_approved=True)
            .values_list('id', flat=True)
            .iterator(chunk_size=1000)
        )
        cache.set(cache_key, archive_ids, 300)
    
    return archive_ids


def get_random_recommendations(exclude_pk, count=9):
    """Memory-efficient random archive selection.
    
    Caches all approved archive IDs, excludes current, samples randomly.
    Single query to fetch selected archives.
    """
    archive_ids = get_all_approved_archive_ids()
    
    available_ids = [aid for aid in archive_ids if aid != exclude_pk]
    
    if not available_ids:
        return Archive.objects.none()
    
    sample_size = min(count, len(available_ids))
    random_ids = random.sample(available_ids, sample_size)
    
    return Archive.objects.filter(pk__in=random_ids).select_related('uploaded_by', 'category')


def archive_list(request):
    archives = Archive.objects.filter(is_approved=True).select_related(
        'uploaded_by', 'category'
    ).prefetch_related('tags').only(
        'id', 'title', 'archive_type', 'image', 'featured_image',
        'alt_text', 'description', 'created_at', 'uploaded_by_id', 'category_id',
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
    
    recommended = get_random_recommendations(archive.pk, count=9)
    
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
        tags_str = request.POST.get('tags', '')
        
        archive = Archive(
            title=title,
            description=description,
            archive_type=archive_type,
            caption=caption,
            alt_text=alt_text,
            original_author=original_author,
            location=location,
            date_created=date_created,
            circa_date=circa_date,
            uploaded_by=request.user,
            is_approved=False
        )
        
        if category_id:
            archive.category_id = category_id
        
        if archive_type == 'image' and 'image' in request.FILES:
            archive.image = request.FILES['image']
        elif archive_type == 'video' and 'video' in request.FILES:
            archive.video = request.FILES['video']
        elif archive_type == 'audio' and 'audio' in request.FILES:
            archive.audio = request.FILES['audio']
        elif archive_type == 'document' and 'document' in request.FILES:
            archive.document = request.FILES['document']
        
        if 'featured_image' in request.FILES:
            archive.featured_image = request.FILES['featured_image']
        
        archive.save()
        
        if tags_str:
            tag_list = [t.strip() for t in tags_str.split(',') if t.strip()]
            archive.tags.add(*tag_list)
        
        cache.delete('all_approved_archive_ids')
        
        messages.success(request, 'Archive uploaded successfully! It will be reviewed by our team.')
        return redirect('archives:list')
    
    context = {
        'categories': get_cached_categories(),
    }
    return render(request, 'archives/create.html', context)


@login_required
def archive_edit(request, pk):
    archive = get_object_or_404(Archive, pk=pk, uploaded_by=request.user)
    
    if request.method == 'POST':
        archive.title = request.POST.get('title')
        archive.description = request.POST.get('description')
        archive.caption = request.POST.get('caption')
        archive.alt_text = request.POST.get('alt_text', '')
        archive.original_author = request.POST.get('original_author', '')
        archive.location = request.POST.get('location', '')
        archive.date_created = request.POST.get('date_created') or None
        archive.circa_date = request.POST.get('circa_date', '')
        
        category_id = request.POST.get('category')
        if category_id:
            archive.category_id = category_id
        else:
            archive.category = None
        
        if 'image' in request.FILES:
            archive.image = request.FILES['image']
        if 'video' in request.FILES:
            archive.video = request.FILES['video']
        if 'audio' in request.FILES:
            archive.audio = request.FILES['audio']
        if 'document' in request.FILES:
            archive.document = request.FILES['document']
        if 'featured_image' in request.FILES:
            archive.featured_image = request.FILES['featured_image']
        
        archive.save()
        
        tags_str = request.POST.get('tags', '')
        archive.tags.clear()
        if tags_str:
            tag_list = [t.strip() for t in tags_str.split(',') if t.strip()]
            archive.tags.add(*tag_list)
        
        messages.success(request, 'Archive updated successfully!')
        return redirect('archives:detail', pk=archive.pk)
    
    context = {
        'archive': archive,
        'categories': get_cached_categories(),
    }
    return render(request, 'archives/edit.html', context)
