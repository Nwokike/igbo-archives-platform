"""
Editor.js Block Renderer Template Tags

Converts Editor.js JSON block format to HTML for display on detail pages.
Includes XSS protection via bleach sanitization.
"""
import json
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False

register = template.Library()

ALLOWED_TAGS = [
    'a', 'b', 'strong', 'i', 'em', 'u', 'br', 'span', 'mark', 'code', 'sub', 'sup'
]
ALLOWED_ATTRS = {
    'a': ['href', 'title', 'target', 'rel'],
    'span': ['class'],
    'mark': ['class'],
}


def sanitize_html(text):
    """Sanitize HTML content while preserving safe inline formatting tags."""
    if not text:
        return ''
    if BLEACH_AVAILABLE:
        cleaned = bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            strip=True
        )
        if 'href' in cleaned:
            cleaned = bleach.linkify(cleaned, callbacks=[lambda attrs, new: {**attrs, (None, 'rel'): 'noopener noreferrer'}])
        return cleaned
    return escape(text)


@register.filter(name='render_editorjs')
def render_editorjs(content):
    """Renders Editor.js JSON content to HTML with XSS protection."""
    if not content:
        return ''
    
    if isinstance(content, str):
        content = content.strip()
        if content.startswith('<'):
            return mark_safe(sanitize_html(content))
        try:
            content = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return mark_safe(sanitize_html(content))
    
    if not isinstance(content, dict):
        return mark_safe(sanitize_html(str(content)))
    
    blocks = content.get('blocks', [])
    if not blocks:
        return ''
    
    html_parts = []
    
    for block in blocks:
        block_type = block.get('type', '')
        data = block.get('data', {})
        
        renderer = BLOCK_RENDERERS.get(block_type, render_unknown)
        html_parts.append(renderer(data))
    
    return mark_safe('\n'.join(html_parts))


def render_paragraph(data):
    """Render paragraph block."""
    text = sanitize_html(data.get('text', ''))
    return f'<p>{text}</p>'


def render_header(data):
    """Render header block."""
    text = sanitize_html(data.get('text', ''))
    level = data.get('level', 2)
    level = max(1, min(6, level))
    
    class_map = {
        1: 'font-serif text-3xl font-bold text-text dark:text-text-dark mt-8 mb-4',
        2: 'font-serif text-2xl font-semibold text-text dark:text-text-dark mt-8 mb-4',
        3: 'font-serif text-xl font-semibold text-text dark:text-text-dark mt-6 mb-3',
        4: 'font-semibold text-lg text-text dark:text-text-dark mt-4 mb-2',
        5: 'font-semibold text-text dark:text-text-dark mt-4 mb-2',
        6: 'font-semibold text-sm text-text dark:text-text-dark mt-4 mb-2',
    }
    
    return f'<h{level} class="{class_map[level]}">{text}</h{level}>'


def render_list(data):
    """Render list block (ordered or unordered)."""
    style = data.get('style', 'unordered')
    items = data.get('items', [])
    
    if not items:
        return ''
    
    tag = 'ol' if style == 'ordered' else 'ul'
    list_class = 'list-decimal' if style == 'ordered' else 'list-disc'
    
    items_html = []
    for item in items:
        if isinstance(item, dict):
            text = sanitize_html(item.get('content', ''))
            nested = item.get('items', [])
            if nested:
                nested_html = render_list({'style': style, 'items': nested})
                items_html.append(f'<li>{text}{nested_html}</li>')
            else:
                items_html.append(f'<li>{text}</li>')
        else:
            items_html.append(f'<li>{sanitize_html(item)}</li>')
    
    return f'<{tag} class="{list_class} list-inside space-y-1 my-4 text-dark-umber">{"".join(items_html)}</{tag}>'


def render_quote(data):
    """Render quote block."""
    text = sanitize_html(data.get('text', ''))
    caption = sanitize_html(data.get('caption', ''))
    alignment = data.get('alignment', 'left')
    
    align_class = 'text-center' if alignment == 'center' else ''
    
    html = f'<blockquote class="border-l-4 border-accent pl-6 my-6 italic text-text dark:text-text-dark {align_class}">'
    html += f'<p class="text-lg">{text}</p>'
    if caption:
        html += f'<cite class="block mt-2 text-sm text-text-muted dark:text-text-dark-muted not-italic">— {caption}</cite>'
    html += '</blockquote>'
    return html


def render_code(data):
    """Render code block."""
    code = escape(data.get('code', ''))
    return f'<pre class="bg-dark-brown text-heritage-cream rounded-lg p-4 my-4 overflow-x-auto"><code class="text-sm font-mono">{code}</code></pre>'


def render_image(data):
    """Render image block."""
    from django.urls import reverse
    
    url = data.get('file', {}).get('url', '') or data.get('url', '')
    caption = sanitize_html(data.get('caption', ''))
    with_border = data.get('withBorder', False)
    stretched = data.get('stretched', False)
    with_background = data.get('withBackground', False)
    archive_id = data.get('archive_id')
    archive_slug = data.get('archive_slug')
    
    if not url:
        return ''
    
    safe_url = escape(url)
    
    img_classes = ['rounded-lg', 'max-w-full', 'h-auto', 'cursor-pointer', 'hover:opacity-90', 'transition-opacity']
    if with_border:
        img_classes.append('border-2 border-sepia-pale')
    if stretched:
        img_classes.append('w-full')
    
    wrapper_classes = ['my-6']
    if with_background:
        wrapper_classes.append('bg-heritage-cream p-4 rounded-lg')
    if not stretched:
        wrapper_classes.append('text-center')
    
    # Build image tag with clickable link
    img_tag = f'<img src="{safe_url}" alt="{escape(caption)}" class="{" ".join(img_classes)}" loading="lazy">'
    
    # Determine link URL: archive detail if from archive, otherwise full-size image
    if archive_slug:
        link_url = reverse('archives:detail', args=[archive_slug])
    elif archive_id:
        link_url = reverse('archives:detail', args=[archive_id])
    else:
        link_url = safe_url
    
    img_tag = f'<a href="{link_url}" target="_blank" rel="noopener noreferrer" class="block">{img_tag}</a>'
    
    html = f'<figure class="{" ".join(wrapper_classes)}">'
    html += img_tag
    if caption:
        html += f'<figcaption class="text-sm text-vintage-beaver mt-2 text-center">{caption}</figcaption>'
    html += '</figure>'
    return html


def render_embed(data):
    """Render embed block (YouTube, Vimeo, etc.)."""
    embed = data.get('embed', '')
    caption = sanitize_html(data.get('caption', ''))
    
    if not embed:
        return ''
    
    allowed_domains = ['youtube.com', 'youtube-nocookie.com', 'vimeo.com', 'player.vimeo.com']
    is_safe = any(domain in embed for domain in allowed_domains)
    
    if not is_safe:
        return f'<p class="text-vintage-beaver italic">Embed not supported: {escape(embed)}</p>'
    
    safe_embed = escape(embed)
    
    html = '<figure class="my-6">'
    html += '<div class="relative pb-[56.25%] h-0 overflow-hidden rounded-lg">'
    html += f'<iframe src="{safe_embed}" class="absolute top-0 left-0 w-full h-full" frameborder="0" allowfullscreen loading="lazy"></iframe>'
    html += '</div>'
    if caption:
        html += f'<figcaption class="text-sm text-vintage-beaver mt-2 text-center">{caption}</figcaption>'
    html += '</figure>'
    return html


def render_delimiter(data):
    """Render delimiter block."""
    return '<hr class="my-8 border-t-2 border-sepia-pale">'


def render_warning(data):
    """Render warning block."""
    title = sanitize_html(data.get('title', ''))
    message = sanitize_html(data.get('message', ''))
    
    html = '<div class="alert alert-warning my-4">'
    html += '<i class="fas fa-exclamation-triangle"></i>'
    html += '<div>'
    if title:
        html += f'<strong class="block">{title}</strong>'
    html += f'{message}</div></div>'
    return html


def render_table(data):
    """Render table block."""
    content = data.get('content', [])
    with_headings = data.get('withHeadings', False)
    
    if not content:
        return ''
    
    html = '<div class="overflow-x-auto my-6"><table class="min-w-full border border-sepia-pale rounded-lg overflow-hidden">'
    
    for i, row in enumerate(content):
        if i == 0 and with_headings:
            html += '<thead class="bg-heritage-cream"><tr>'
            for cell in row:
                html += f'<th class="px-4 py-3 text-left text-dark-brown font-semibold border-b border-sepia-pale">{sanitize_html(cell)}</th>'
            html += '</tr></thead><tbody>'
        else:
            html += '<tr class="border-b border-sepia-pale/50 hover:bg-heritage-cream/50">'
            for cell in row:
                html += f'<td class="px-4 py-3 text-dark-umber">{sanitize_html(cell)}</td>'
            html += '</tr>'
    
    if with_headings:
        html += '</tbody>'
    html += '</table></div>'
    return html


def render_raw(data):
    """Render raw HTML block - sanitized for safety."""
    raw_html = data.get('html', '')
    return sanitize_html(raw_html)


def render_checklist(data):
    """Render checklist block."""
    items = data.get('items', [])
    
    if not items:
        return ''
    
    html = '<ul class="space-y-2 my-4">'
    for item in items:
        text = sanitize_html(item.get('text', ''))
        checked = item.get('checked', False)
        icon = '☑' if checked else '☐'
        style = 'line-through text-vintage-beaver' if checked else 'text-dark-umber'
        html += f'<li class="flex items-start gap-2"><span class="text-vintage-gold">{icon}</span><span class="{style}">{text}</span></li>'
    html += '</ul>'
    return html


def render_unknown(data):
    """Fallback renderer for unknown block types."""
    return ''


BLOCK_RENDERERS = {
    'paragraph': render_paragraph,
    'header': render_header,
    'list': render_list,
    'nestedList': render_list,
    'quote': render_quote,
    'code': render_code,
    'image': render_image,
    'embed': render_embed,
    'delimiter': render_delimiter,
    'warning': render_warning,
    'table': render_table,
    'raw': render_raw,
    'checklist': render_checklist,
}
