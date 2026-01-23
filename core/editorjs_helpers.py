"""
Shared helpers for Editor.js content handling across insights and books apps.
Centralizes JSON parsing, tag handling, slug generation, and workflow flags.
"""
import json
import uuid
from django.utils.text import slugify
from django.core.exceptions import ValidationError


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


def generate_unique_slug(base_text, model_class, max_length=200):
    """
    Generate a unique slug from text with collision handling.
    
    Args:
        base_text: Text to slugify
        model_class: Model class to check for uniqueness (must have 'slug' field)
        max_length: Maximum slug length (default 200)
        
    Returns:
        str: Unique slug
    """
    base_slug = slugify(base_text)[:max_length]
    slug = base_slug
    
    counter = 1
    while model_class.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
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
