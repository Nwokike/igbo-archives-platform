from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Archive, Category
from django.core.paginator import Paginator

def archive_list(request):
    archives = Archive.objects.filter(is_approved=True)
    
    category = request.GET.get('category')
    if category:
        archives = archives.filter(category__slug=category)
    
    search = request.GET.get('search')
    if search:
        archives = archives.filter(title__icontains=search)
    
    archive_type = request.GET.get('type')
    if archive_type:
        archives = archives.filter(archive_type=archive_type)
    
    sort = request.GET.get('sort', '-created_at')
    archives = archives.order_by(sort)
    
    paginator = Paginator(archives, 12)
    page = request.GET.get('page')
    archives = paginator.get_page(page)
    
    categories = Category.objects.all()
    
    context = {
        'archives': archives,
        'categories': categories,
    }
    
    if request.htmx:
        return render(request, 'archives/partials/archive_grid.html', context)
    
    return render(request, 'archives/list.html', context)

def archive_detail(request, pk):
    archive = get_object_or_404(Archive, pk=pk, is_approved=True)
    
    # Get previous and next archives
    previous_archive = Archive.objects.filter(
        is_approved=True,
        created_at__lt=archive.created_at
    ).order_by('-created_at').first()
    
    next_archive = Archive.objects.filter(
        is_approved=True,
        created_at__gt=archive.created_at
    ).order_by('created_at').first()
    
    # Get recommended archives (9 total: same category, same tags, or featured)
    recommended = Archive.objects.filter(is_approved=True).exclude(pk=archive.pk)
    
    if archive.category:
        recommended = recommended.filter(category=archive.category)
    
    # If we need more, add by tags
    if recommended.count() < 9:
        tag_names = archive.tags.values_list('name', flat=True)
        if tag_names:
            recommended = Archive.objects.filter(
                is_approved=True,
                tags__name__in=tag_names
            ).exclude(pk=archive.pk).distinct()
    
    # If still need more, add random archives
    if recommended.count() < 9:
        recommended = Archive.objects.filter(is_approved=True).exclude(pk=archive.pk).order_by('?')
    
    recommended = recommended[:9]
    
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
        
        # Validate required fields
        if not title or not description or not archive_type or not caption:
            messages.error(request, 'Please fill in all required fields.')
            categories = Category.objects.all()
            return render(request, 'archives/create.html', {'categories': categories})
        
        # Create archive instance
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
            is_approved=False  # Requires admin approval before appearing on frontend
        )
        
        # Handle file uploads based on type
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
            
            # Add tags
            tags = request.POST.get('tags', '').split(',')
            for tag in tags:
                if tag.strip():
                    archive.tags.add(tag.strip())
            
            messages.success(request, 'Archive uploaded successfully!')
            return redirect('archives:detail', pk=archive.pk)
        except Exception as e:
            messages.error(request, f'Error uploading archive: {str(e)}')
            return redirect('archives:create')
    
    categories = Category.objects.all()
    return render(request, 'archives/create.html', {'categories': categories})

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
        
        # Handle file uploads
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
        
        # Clear existing tags and add new ones
        archive.tags.clear()
        tags = request.POST.get('tags', '').split(',')
        for tag in tags:
            if tag.strip():
                archive.tags.add(tag.strip())
        
        archive.save()
        messages.success(request, 'Archive updated successfully!')
        return redirect('archives:detail', pk=archive.pk)
    
    categories = Category.objects.all()
    return render(request, 'archives/edit.html', {'archive': archive, 'categories': categories})
