"""
Archive views for browsing and managing cultural archives.
"""
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from .models import Archive, Category
from core.validators import ALLOWED_ARCHIVE_SORTS, get_safe_sort
from core.views import get_all_approved_archive_ids


def get_cached_categories():
    """Cache categories for 1 hour."""
    categories = cache.get('archive_categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('archive_categories', categories, 3600)
    return categories


def get_random_recommendations(exclude_pk, count=9):
    """Memory-efficient random archive selection."""
    archive_ids = get_all_approved_archive_ids()
    available_ids = [aid for aid in archive_ids if aid != exclude_pk]
    
    if not available_ids:
        return Archive.objects.none()
    
    sample_size = min(count, len(available_ids))
    random_ids = random.sample(available_ids, sample_size)
    
    return Archive.objects.filter(pk__in=random_ids).select_related('uploaded_by', 'category')


def archive_list(request):
    """List all approved archives with filtering and pagination."""
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
    
    sort = get_safe_sort(request.GET.get('sort', '-created_at'), ALLOWED_ARCHIVE_SORTS)
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
    """Display a single archive with recommendations."""
    archive = get_object_or_404(
        Archive.objects.select_related('uploaded_by', 'category'),
        pk=pk, is_approved=True
    )
    
    previous_archive = Archive.objects.filter(
        is_approved=True, created_at__lt=archive.created_at
    ).order_by('-created_at').only('id', 'title').first()
    
    next_archive = Archive.objects.filter(
        is_approved=True, created_at__gt=archive.created_at
    ).order_by('created_at').only('id', 'title').first()
    
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
    """Create a new archive."""
    from .forms import ArchiveForm
    import bleach
    
    if request.method == 'POST':
        form = ArchiveForm(request.POST, request.FILES)
        
        if form.is_valid():
            archive = form.save(commit=False)
            archive.uploaded_by = request.user
            archive.is_approved = False
            
            # Clean description with bleach
            archive.description = bleach.clean(archive.description, strip=True)
            
            archive.save()
            
            # Handle tags
            tags = form.cleaned_data.get('tags', [])
            if tags:
                archive.tags.add(*tags)
            
            messages.success(request, 'Archive uploaded successfully! It will be reviewed by our team.')
            return redirect('archives:list')
    else:
        form = ArchiveForm()
    
    context = {
        'form': form,
        'categories': get_cached_categories()
    }
    return render(request, 'archives/create.html', context)


@login_required
def archive_edit(request, pk):
    """Edit an existing archive."""
    from .forms import ArchiveForm
    import bleach
    
    archive = get_object_or_404(Archive, pk=pk, uploaded_by=request.user)
    
    if request.method == 'POST':
        form = ArchiveForm(request.POST, request.FILES, instance=archive)
        
        if form.is_valid():
            archive = form.save(commit=False)
            
            # Clean description with bleach
            archive.description = bleach.clean(archive.description, strip=True)
            
            # Call full_clean to validate file changes
            try:
                archive.full_clean()
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
                context = {
                    'form': form,
                    'archive': archive,
                    'categories': get_cached_categories(),
                }
                return render(request, 'archives/edit.html', context)
            
            archive.save()
            
            # Handle tags
            tags = form.cleaned_data.get('tags', [])
            archive.tags.clear()
            if tags:
                archive.tags.add(*tags)
            
            if archive.is_approved:
                cache.delete('all_approved_archive_ids')
            
            messages.success(request, 'Archive updated successfully!')
            return redirect('archives:detail', pk=archive.pk)
    else:
        # Initialize form with existing data
        initial_tags = ', '.join([tag.name for tag in archive.tags.all()])
        form = ArchiveForm(instance=archive, initial={'tags': initial_tags})
    
    context = {
        'form': form,
        'archive': archive,
        'categories': get_cached_categories(),
    }
    return render(request, 'archives/edit.html', context)
