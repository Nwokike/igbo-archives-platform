"""
API views for Editor.js integration and image uploads.
"""
import os
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from archives.models import Archive, ArchiveItem, Category

logger = logging.getLogger(__name__)


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
    
    # UPDATED: Added 'copyright_holder' and 'original_author' to only()
    archives = Archive.objects.filter(is_approved=True).select_related('category').only(
        'id', 'title', 'description', 'archive_type', 'caption', 'alt_text',
        'copyright_holder', 'original_author', 
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
            'slug': getattr(archive, 'slug', None),
            'title': archive.title,
            'description': archive.description,
            'archive_type': archive.archive_type,
            'caption': archive.caption,
            'alt_text': archive.alt_text,
            # UPDATED: Return these fields
            'copyright_holder': archive.copyright_holder,
            'original_author': archive.original_author,
        }
        
        # Set media URL based on archive type
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
            continue
        
        data['archives'].append(archive_data)
    
    return JsonResponse(data)


@login_required
@require_POST
def upload_image(request):
    """
    Handle simple image uploads from Editor.js (Drag & Drop / Paste).
    This creates a basic Archive entry with minimal metadata.
    """
    rate_key = f'upload_rate_{request.user.id}'
    upload_count = cache.get(rate_key, 0)
    if upload_count >= 20:
        return JsonResponse({'success': 0, 'error': 'Upload limit reached. Try again later.'})
    
    if 'image' not in request.FILES:
        return JsonResponse({'success': 0, 'error': 'No image file provided'})
    
    image_file = request.FILES['image']
    caption = request.POST.get('caption', '').strip()
    
    # In simple drag & drop, description might not be provided, so we default
    description = request.POST.get('description', '').strip() or "Uploaded via editor"
    
    # Basic validation for simple upload
    if not caption:
        # Fallback for drag/drop where no caption is prompted immediately
        caption = "Untitled Image" 
    
    file_size = image_file.size
    if file_size > 5 * 1024 * 1024:
        return JsonResponse({'success': 0, 'error': 'Maximum file size is 5MB'})
    
    allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
    file_extension = os.path.splitext(image_file.name)[1][1:].lower()
    if file_extension not in allowed_extensions:
        return JsonResponse({'success': 0, 'error': f'Only {", ".join(allowed_extensions)} files are allowed'})
    
    # Atomic creation of Archive + Item
    try:
        with transaction.atomic():
            # 1. Parent Archive
            archive = Archive.objects.create(
                title=caption[:255],
                description=description,
                caption=caption,
                alt_text=description[:255],
                archive_type='image',
                image=image_file, # Kept for sync
                uploaded_by=request.user,
                is_approved=False
            )
            
            # 2. Archive Item
            ArchiveItem.objects.create(
                archive=archive,
                item_number=1,
                item_type='image',
                image=image_file,
                caption=caption,
                alt_text=description[:255]
            )
            
            cache.set(rate_key, upload_count + 1, 3600)
            
            return JsonResponse({
                'success': 1,
                'file': {
                    'url': request.build_absolute_uri(archive.image.url),
                    'size': file_size,
                    'name': image_file.name,
                },
                'archive_id': archive.id
            })
            
    except Exception as e:
        return JsonResponse({'success': 0, 'error': str(e)})


@login_required
@require_POST
def upload_media(request):
    """
    Handle multi-media uploads from the Modal with FULL archive fields.
    Updates: Captures Authors, Dates, ID Numbers, and separates Alt Text from Description.
    """
    rate_key = f'upload_rate_{request.user.id}'
    upload_count = cache.get(rate_key, 0)
    if upload_count >= 20:
        return JsonResponse({'success': 0, 'error': 'Upload limit reached. Try again later.'})
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': 0, 'error': 'No file provided'})
    
    uploaded_file = request.FILES['file']
    media_type = request.POST.get('media_type', 'image')
    
    # --- 1. Archive Details ---
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip() # This is now the Archive Description
    category_id = request.POST.get('category', '').strip()
    tags = request.POST.get('tags', '').strip()
    
    # --- 2. Source & Origin ---
    original_author = request.POST.get('original_author', '').strip()
    copyright_holder = request.POST.get('copyright_holder', '').strip()
    circa_date = request.POST.get('circa_date', '').strip()
    date_created = request.POST.get('date_created', '').strip() or None # Handle empty string for DateField
    location = request.POST.get('location', '').strip()
    original_identity_number = request.POST.get('original_identity_number', '').strip()
    original_url = request.POST.get('original_url', '').strip()
    
    # --- 3. Media Item ---
    caption = request.POST.get('caption', '').strip()
    alt_text = request.POST.get('alt_text', '').strip() # This is the Item Alt Text
    
    # Validation
    if not title:
        return JsonResponse({'success': 0, 'error': 'Archive Title is required'})
    if not description:
        return JsonResponse({'success': 0, 'error': 'Archive Description is required'})
    if not caption:
        return JsonResponse({'success': 0, 'error': 'Item Caption is required'})
    if not alt_text and media_type == 'image':
        return JsonResponse({'success': 0, 'error': 'Alt Text is required for images'})
    
    # Config for types
    media_config = {
        'image': {'max_size': 5*1024*1024, 'ext': ['jpg', 'jpeg', 'png', 'webp'], 'field': 'image'},
        'video': {'max_size': 50*1024*1024, 'ext': ['mp4', 'webm', 'ogg', 'mov'], 'field': 'video'},
        'audio': {'max_size': 10*1024*1024, 'ext': ['mp3', 'wav', 'ogg', 'm4a'], 'field': 'audio'}
    }
    
    if media_type not in media_config:
        return JsonResponse({'success': 0, 'error': 'Invalid media type'})
    
    config = media_config[media_type]
    
    if uploaded_file.size > config['max_size']:
        return JsonResponse({'success': 0, 'error': 'File too large'})
        
    ext = os.path.splitext(uploaded_file.name)[1][1:].lower()
    if ext not in config['ext']:
        return JsonResponse({'success': 0, 'error': 'Invalid file type'})
    
    try:
        with transaction.atomic():
            # 1. Create Parent Archive
            archive_data = {
                'title': title[:255],
                'description': description, # Full archive description
                
                # Metadata
                'archive_type': media_type,
                'uploaded_by': request.user,
                'is_approved': False,
                
                # Source & Origin
                'original_author': original_author[:255],
                'copyright_holder': copyright_holder[:255],
                'circa_date': circa_date[:100],
                'date_created': date_created,
                'location': location[:255],
                'original_identity_number': original_identity_number[:100],
                'original_url': original_url,
                
                # Defaults from the first item (for list view compatibility)
                'caption': caption[:500], 
                'alt_text': alt_text[:255],
                
                config['field']: uploaded_file # Save file to parent for legacy sync
            }
            
            archive = Archive.objects.create(**archive_data)
            
            # Handle category
            if category_id:
                try:
                    archive.category = Category.objects.get(id=int(category_id))
                    archive.save(update_fields=['category'])
                except Exception:
                    pass
            
            # Handle tags
            if tags:
                from taggit.utils import parse_tags
                tag_list = parse_tags(tags)
                if tag_list:
                    archive.tags.add(*tag_list[:20])

            # 2. Create Archive Item (The specific media file)
            item_data = {
                'archive': archive,
                'item_number': 1,
                'item_type': media_type,
                'caption': caption[:500],
                'alt_text': alt_text[:255],
                'description': '', # Optional specific item description, leaving blank for now
                config['field']: uploaded_file # Save file to item
            }
            ArchiveItem.objects.create(**item_data)
            
            cache.set(rate_key, upload_count + 1, 3600)
            
            media_field = getattr(archive, config['field'])
            
            return JsonResponse({
                'success': 1,
                'file': {
                    'url': request.build_absolute_uri(media_field.url),
                    'size': uploaded_file.size,
                    'name': uploaded_file.name,
                    # Return captions for Editor.js to display immediately
                    'caption': caption,
                    'alt': alt_text
                },
                'archive_id': archive.id
            })
            
    except Exception as e:
        logger.error(f"Media upload error: {e}", exc_info=True)
        return JsonResponse({'success': 0, 'error': str(e)})


@login_required
def notification_list_api(request):
    """Return top 5 unread notifications for the dropdown."""
    from django.shortcuts import render
    notifications = request.user.notifications.filter(unread=True).order_by('-timestamp')[:5]
    return render(request, 'users/partials/notification_dropdown.html', {
        'notifications': notifications
    })