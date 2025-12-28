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
        'image', 'video', 'audio', 'document', 'featured_image'
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
            'title': archive.title,
            'description': archive.description,
            'archive_type': archive.archive_type,
            'caption': archive.caption,
            'alt_text': archive.alt_text,
        }
        
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
    
    cache.delete('all_approved_archive_ids')
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
@require_http_methods(["GET"])
def get_categories(request):
    """Return all categories for archive submission."""
    categories = get_cached_api_categories()
    return JsonResponse({'categories': categories})
