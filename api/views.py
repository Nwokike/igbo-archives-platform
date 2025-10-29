from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from archives.models import Archive, Category
from insights.models import UploadedImage
import json
import os


@login_required
@require_http_methods(["GET"])
def archive_media_browser(request):
    """
    Archive media browser API endpoint.
    Returns paginated list of archives for selection in post editor.
    """
    # Filter parameters
    search = request.GET.get('search', '')
    archive_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    page = request.GET.get('page', 1)
    
    # Build queryset
    archives = Archive.objects.filter(is_approved=True)
    
    if search:
        archives = archives.filter(title__icontains=search)
    
    if archive_type:
        archives = archives.filter(archive_type=archive_type)
    
    if category:
        archives = archives.filter(category__slug=category)
    
    # Paginate
    paginator = Paginator(archives, 12)
    archives_page = paginator.get_page(page)
    
    # Serialize data
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
        
        # Get the appropriate file URL
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
@csrf_exempt
@require_http_methods(["POST"])
def upload_image(request):
    """
    Handle image uploads from Quill editor.
    Automatically creates Archive entry with caption and description.
    """
    if 'image' not in request.FILES:
        return JsonResponse({'success': 0, 'error': 'No image file provided'})
    
    image_file = request.FILES['image']
    caption = request.POST.get('caption', '').strip()
    description = request.POST.get('description', '').strip()
    
    # Validate required metadata
    if not caption:
        return JsonResponse({'success': 0, 'error': 'Caption with copyright/source info is required'})
    if not description:
        return JsonResponse({'success': 0, 'error': 'Image description (alt text) is required'})
    
    # Validate file size (Max 5MB)
    file_size = image_file.size
    if file_size > 5 * 1024 * 1024:
        return JsonResponse({'success': 0, 'error': 'Maximum file size is 5MB'})
    if file_size < 1024:  # Minimum 1KB for sanity check
        return JsonResponse({'success': 0, 'error': 'File too small'})
    
    # Validate file type
    allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
    file_extension = os.path.splitext(image_file.name)[1][1:].lower()
    if file_extension not in allowed_extensions:
        return JsonResponse({'success': 0, 'error': f'Only {", ".join(allowed_extensions)} files are allowed'})
    
    # Create Archive entry automatically using caption as title
    archive = Archive.objects.create(
        title=caption,  # Use caption as title instead of filename
        description=description,
        caption=caption,
        alt_text=description,
        archive_type='image',
        image=image_file,
        uploaded_by=request.user,
        is_approved=False  # Require admin approval to assign category
    )
    
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
    categories = Category.objects.all()
    data = [{'id': cat.id, 'name': cat.name, 'slug': cat.slug} for cat in categories]
    return JsonResponse({'categories': data})
