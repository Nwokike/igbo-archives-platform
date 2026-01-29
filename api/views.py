"""
API views for Editor.js integration and image uploads.
"""
import os
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from archives.models import Archive, Category


def get_cached_api_categories():
    """Cache categories for API responses."""
    categories = cache.get('api_categories')
    if categories is None:
        categories = list(Category.objects.values('id', 'name', 'slug'))
        cache.set('api_categories', categories, 3600)
    return categories


@login_required
@require_http_methods(["GET"])
def archive_media_browser(request):
    """Archive media browser API endpoint for Editor.js."""
    search = request.GET.get('search', '')
    archive_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    page = request.GET.get('page', 1)
    
    archives = Archive.objects.filter(is_approved=True).select_related('category').only(
        'id', 'title', 'description', 'archive_type', 'caption', 'alt_text',
        'image', 'video', 'audio', 'document', 'featured_image', 'category__id', 'category__name', 'category__slug'
    )
    
    if search:
        archives = archives.filter(title__icontains=search)
    
    if archive_type:
        archives = archives.filter(archive_type=archive_type)
    
    if category:
        archives = archives.filter(category__slug=category)
    
    paginator = Paginator(archives, 12)
    archives_page = paginator.get_page(page)
    
    data = {
        'archives': [],
        'has_next': archives_page.has_next(),
        'has_previous': archives_page.has_previous(),
        'total_pages': paginator.num_pages,
        'current_page': archives_page.number,
    }
    
    for archive in archives_page:
        archive_data = {
            'id': archive.id,
            'slug': getattr(archive, 'slug', None),  # Use getattr for safety
            'title': archive.title,
            'description': archive.description,
            'archive_type': archive.archive_type,
            'caption': archive.caption,
            'alt_text': archive.alt_text,
        }
        
        # Set media URL and thumbnail based on archive type
        if archive.archive_type == 'image' and archive.image:
            archive_data['url'] = archive.image.url
            archive_data['thumbnail'] = archive.image.url
        elif archive.archive_type == 'video' and archive.video:
            archive_data['url'] = archive.video.url
            archive_data['thumbnail'] = archive.featured_image.url if archive.featured_image else ''
        elif archive.archive_type == 'audio' and archive.audio:
            archive_data['url'] = archive.audio.url
            archive_data['thumbnail'] = archive.featured_image.url if archive.featured_image else ''
        elif archive.archive_type == 'document' and archive.document:
            archive_data['url'] = archive.document.url
            archive_data['thumbnail'] = ''
        else:
            continue  # Skip archives without valid media
        
        data['archives'].append(archive_data)
    
    return JsonResponse(data)


@login_required
@require_POST
def upload_image(request):
    """Handle image uploads from Editor.js with CSRF protection."""
    rate_key = f'upload_rate_{request.user.id}'
    upload_count = cache.get(rate_key, 0)
    if upload_count >= 20:
        return JsonResponse({'success': 0, 'error': 'Upload limit reached. Try again later.'})
    
    if 'image' not in request.FILES:
        return JsonResponse({'success': 0, 'error': 'No image file provided'})
    
    image_file = request.FILES['image']
    caption = request.POST.get('caption', '').strip()
    description = request.POST.get('description', '').strip()
    
    if not caption:
        return JsonResponse({'success': 0, 'error': 'Caption with copyright/source info is required'})
    if not description:
        return JsonResponse({'success': 0, 'error': 'Image description (alt text) is required'})
    
    file_size = image_file.size
    if file_size > 5 * 1024 * 1024:
        return JsonResponse({'success': 0, 'error': 'Maximum file size is 5MB'})
    if file_size < 1024:
        return JsonResponse({'success': 0, 'error': 'File too small'})
    
    allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
    file_extension = os.path.splitext(image_file.name)[1][1:].lower()
    if file_extension not in allowed_extensions:
        return JsonResponse({'success': 0, 'error': f'Only {", ".join(allowed_extensions)} files are allowed'})
    
    archive = Archive.objects.create(
        title=caption[:255],
        description=description,
        caption=caption,
        alt_text=description[:255],
        archive_type='image',
        image=image_file,
        uploaded_by=request.user,
        is_approved=False
    )
    
    cache.set(rate_key, upload_count + 1, 3600)
    
    file_url = request.build_absolute_uri(archive.image.url)
    
    return JsonResponse({
        'success': 1,
        'file': {
            'url': file_url,
            'size': file_size,
            'name': image_file.name,
        },
        'archive_id': archive.id
    })


@login_required
@require_POST
def upload_media(request):
    """Handle multi-media uploads (image/video/audio) with full archive fields."""
    rate_key = f'upload_rate_{request.user.id}'
    upload_count = cache.get(rate_key, 0)
    if upload_count >= 20:
        return JsonResponse({'success': 0, 'error': 'Upload limit reached. Try again later.'})
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': 0, 'error': 'No file provided'})
    
    uploaded_file = request.FILES['file']
    media_type = request.POST.get('media_type', 'image')
    title = request.POST.get('title', '').strip()
    caption = request.POST.get('caption', '').strip()
    description = request.POST.get('description', '').strip()
    
    # Optional fields
    category_id = request.POST.get('category', '').strip()
    location = request.POST.get('location', '').strip()
    circa_date = request.POST.get('circa_date', '').strip()
    copyright_holder = request.POST.get('copyright_holder', '').strip()
    original_url = request.POST.get('original_url', '').strip()
    tags = request.POST.get('tags', '').strip()
    
    # Validate required fields
    if not title:
        return JsonResponse({'success': 0, 'error': 'Title is required'})
    if not caption:
        return JsonResponse({'success': 0, 'error': 'Caption with copyright/source info is required'})
    if not description:
        return JsonResponse({'success': 0, 'error': 'Description (alt text) is required'})
    
    # Media type configuration
    media_config = {
        'image': {
            'max_size': 5 * 1024 * 1024,
            'extensions': ['jpg', 'jpeg', 'png', 'webp'],
            'field': 'image'
        },
        'video': {
            'max_size': 50 * 1024 * 1024,
            'extensions': ['mp4', 'webm', 'ogg', 'mov'],
            'field': 'video'
        },
        'audio': {
            'max_size': 10 * 1024 * 1024,
            'extensions': ['mp3', 'wav', 'ogg', 'm4a'],
            'field': 'audio'
        }
    }
    
    if media_type not in media_config:
        return JsonResponse({'success': 0, 'error': 'Invalid media type'})
    
    config = media_config[media_type]
    file_size = uploaded_file.size
    
    if file_size > config['max_size']:
        max_mb = config['max_size'] // (1024 * 1024)
        return JsonResponse({'success': 0, 'error': f'Maximum file size is {max_mb}MB'})
    if file_size < 1024:
        return JsonResponse({'success': 0, 'error': 'File too small'})
    
    file_extension = os.path.splitext(uploaded_file.name)[1][1:].lower()
    if file_extension not in config['extensions']:
        return JsonResponse({'success': 0, 'error': f'Only {", ".join(config["extensions"])} files are allowed'})
    
    # Create archive
    archive_data = {
        'title': title[:255],
        'description': description,
        'caption': caption,
        'alt_text': description[:255],
        'archive_type': media_type,
        'uploaded_by': request.user,
        'is_approved': False,
        config['field']: uploaded_file
    }
    
    # Optional fields
    if location:
        archive_data['location'] = location[:255]
    if circa_date:
        archive_data['circa_date'] = circa_date[:50]
    if copyright_holder:
        archive_data['copyright_holder'] = copyright_holder[:255]
    if original_url:
        archive_data['original_url'] = original_url
    
    archive = Archive.objects.create(**archive_data)
    
    # Handle category
    if category_id:
        try:
            category = Category.objects.get(id=int(category_id))
            archive.category = category
            archive.save(update_fields=['category'])
        except (ValueError, Category.DoesNotExist):
            pass
    
    # Handle tags
    if tags:
        from taggit.utils import parse_tags
        tag_list = parse_tags(tags)
        if tag_list:
            archive.tags.add(*tag_list[:20])  # Max 20 tags
    
    cache.set(rate_key, upload_count + 1, 3600)
    
    # Get file URL based on media type
    media_field = getattr(archive, config['field'])
    file_url = request.build_absolute_uri(media_field.url)
    
    return JsonResponse({
        'success': 1,
        'file': {
            'url': file_url,
            'size': file_size,
            'name': uploaded_file.name,
        },
        'archive_id': archive.id
    })


@login_required
def notification_list_api(request):
    """Return top 5 unread notifications for the dropdown."""
    from django.shortcuts import render
    notifications = request.user.notifications.filter(unread=True).order_by('-timestamp')[:5]
    return render(request, 'users/partials/notification_dropdown.html', {
        'notifications': notifications
    })
