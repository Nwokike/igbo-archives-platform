"""
Shared helpers for Editor.js content handling across insights and books apps.
Centralizes JSON parsing, tag handling, slug generation, and workflow flags.
"""
import json
import uuid
import os
import logging
import requests
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


def parse_editorjs_content(content_json):
    """
    Parse and validate Editor.js JSON content.
    
    Args:
        content_json: JSON string or dict
        
    Returns:
        dict: Parsed content data
        
    Raises:
        ValidationError: If content is invalid
    """
    if isinstance(content_json, str):
        try:
            content_data = json.loads(content_json)
        except json.JSONDecodeError as e:
            raise ValidationError(f'Invalid Editor.js content format: {str(e)}')
    elif isinstance(content_json, dict):
        content_data = content_json
    else:
        raise ValidationError('Content must be valid Editor.js JSON')
    
    # Basic structure validation
    if not isinstance(content_data, dict):
        raise ValidationError('Editor.js content must be a JSON object')
    
    if 'blocks' not in content_data:
        raise ValidationError('Editor.js content must contain "blocks" array')
    
    if not isinstance(content_data['blocks'], list):
        raise ValidationError('Editor.js "blocks" must be an array')
    
    return content_data


def parse_tags(tags_str, max_tags=20, max_tag_length=50):
    """
    Parse comma-separated tags with length and count limits.
    
    Args:
        tags_str: Comma-separated tag string
        max_tags: Maximum number of tags (default 20)
        max_tag_length: Maximum length per tag (default 50)
        
    Returns:
        list: List of cleaned tag names
    """
    if not tags_str:
        return []
    
    tags = []
    for tag in tags_str.split(','):
        tag = tag.strip()[:max_tag_length]
        if tag:
            tags.append(tag)
            if len(tags) >= max_tags:
                break
    
    return tags


def generate_unique_slug(base_text, model_class, max_length=200, exclude_pk=None):
    """
    Generate a unique slug from text with collision handling.
    
    Args:
        base_text: Text to slugify
        model_class: Model class to check for uniqueness (must have 'slug' field)
        max_length: Maximum slug length (default 200)
        exclude_pk: PK to exclude from uniqueness check (for updates)
        
    Returns:
        str: Unique slug
    """
    base_slug = slugify(base_text)[:max_length]
    slug = base_slug
    
    counter = 1
    queryset = model_class.objects.filter(slug=slug)
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    
    while queryset.exists():
        slug = f"{base_slug}-{counter}"
        queryset = model_class.objects.filter(slug=slug)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        counter += 1
        if counter > 100:
            # Fallback to UUID if too many collisions
            slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
            break
    
    return slug


def get_workflow_flags(action, is_submit=False):
    """
    Get workflow flags based on action.
    
    Args:
        action: Action string ('submit' or other)
        is_submit: Whether this is a submission action
        
    Returns:
        dict: Workflow flags dict with keys:
            - is_published: bool
            - is_approved: bool
            - pending_approval: bool
            - submitted_at: datetime or None
    """
    from django.utils import timezone
    
    if action == 'submit' or is_submit:
        return {
            'is_published': False,
            'is_approved': False,
            'pending_approval': True,
            'submitted_at': timezone.now()
        }
    else:
        return {
            'is_published': False,
            'is_approved': False,
            'pending_approval': False,
            'submitted_at': None
        }


def download_and_save_image_from_url(model_instance, image_field_name, url, max_size_mb=5):
    """
    Download an image from URL and save it to a model's ImageField.
    Handles both local media URLs and remote URLs.
    
    Args:
        model_instance: The model instance to save the image to
        image_field_name: Name of the ImageField (e.g., 'featured_image')
        url: URL of the image to download
        max_size_mb: Maximum file size in MB (default 5)
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not url:
        return False
    
    try:
        from django.conf import settings
        
        # Handle local media URLs - copy the file
        if url.startswith('/media/'):
            file_path = os.path.join(settings.MEDIA_ROOT, url.replace('/media/', '').lstrip('/'))
            if os.path.exists(file_path):
                # Check if already using this file to avoid unnecessary copy
                current_file = getattr(model_instance, image_field_name)
                if current_file and current_file.name:
                    current_path = os.path.join(settings.MEDIA_ROOT, current_file.name)
                    if os.path.exists(current_path) and os.path.samefile(file_path, current_path):
                        return True  # Already using this exact file
                
                # Copy the file
                with open(file_path, 'rb') as f:
                    file_name = os.path.basename(file_path)
                    getattr(model_instance, image_field_name).save(
                        file_name,
                        ContentFile(f.read()),
                        save=False
                    )
                return True
            return False
        
        # Handle absolute URLs (http/https)
        if url.startswith('http://') or url.startswith('https://'):
            # SSRF protection: block private/internal IP ranges
            from urllib.parse import urlparse
            import ipaddress
            import socket
            
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            if not hostname:
                return False
            
            # Block obvious internal hostnames
            blocked_hostnames = {'localhost', '127.0.0.1', '::1', '0.0.0.0'}
            if hostname.lower() in blocked_hostnames:
                logger.warning(f"Blocked SSRF attempt to internal host: {hostname}")
                return False
            
            # Resolve hostname and check for private IP ranges
            try:
                addr_info = socket.getaddrinfo(hostname, None)
                for _, _, _, _, sockaddr in addr_info:
                    ip = ipaddress.ip_address(sockaddr[0])
                    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                        logger.warning(f"Blocked SSRF attempt to private IP: {ip} ({hostname})")
                        return False
            except (socket.gaierror, ValueError):
                logger.warning(f"Could not resolve hostname: {hostname}")
                return False
            
            # Download from URL with streaming
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return False
            
            # Check declared file size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > max_size_mb * 1024 * 1024:
                return False
            
            # Stream download with size limit
            max_bytes = int(max_size_mb * 1024 * 1024)
            chunks = []
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                downloaded += len(chunk)
                if downloaded > max_bytes:
                    logger.warning(f"Image download exceeded size limit: {url}")
                    return False
                chunks.append(chunk)
            img_data = b''.join(chunks)
            
            # Get file extension from URL or content type
            ext = 'jpg'
            if '.jpg' in url.lower() or '.jpeg' in url.lower() or 'jpeg' in content_type:
                ext = 'jpg'
            elif '.png' in url.lower() or 'png' in content_type:
                ext = 'png'
            elif '.webp' in url.lower() or 'webp' in content_type:
                ext = 'webp'
            
            # Generate filename
            file_name = f"{image_field_name}_{uuid.uuid4().hex[:8]}.{ext}"
            
            # Save to ImageField
            getattr(model_instance, image_field_name).save(
                file_name,
                ContentFile(img_data),
                save=False
            )
            return True
    except Exception as e:
        logger.error(f"Error downloading image from URL {url}: {e}", exc_info=True)
        return False
    
    return False
