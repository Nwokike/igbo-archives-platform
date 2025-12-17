"""
Editor.js Block Renderer Template Tags

Converts Editor.js JSON block format to HTML for display on detail pages.
"""
import json
from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='render_editorjs')
def render_editorjs(content):
    """
    Renders Editor.js JSON content to HTML.
    Falls back to returning content as-is if it's already HTML or invalid JSON.
    """
    if not content:
        return ''
    
    if isinstance(content, str):
        content = content.strip()
        if content.startswith('<'):
            return mark_safe(content)
        try:
            content = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return mark_safe(content)
    
    if not isinstance(content, dict):
        return mark_safe(str(content))
    
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
    text = data.get('text', '')
    return f'<p>{text}</p>'


def render_header(data):
    """Render header block."""
    text = data.get('text', '')
    level = data.get('level', 2)
    level = max(1, min(6, level))
    
    class_map = {
        1: 'font-serif text-3xl font-bold text-dark-brown mt-8 mb-4',
        2: 'font-serif text-2xl font-semibold text-dark-brown mt-8 mb-4',
        3: 'font-serif text-xl font-semibold text-dark-brown mt-6 mb-3',
        4: 'font-semibold text-lg text-dark-brown mt-4 mb-2',
        5: 'font-semibold text-dark-brown mt-4 mb-2',
        6: 'font-semibold text-sm text-dark-brown mt-4 mb-2',
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
            text = item.get('content', '')
            nested = item.get('items', [])
            if nested:
                nested_html = render_list({'style': style, 'items': nested})
                items_html.append(f'<li>{text}{nested_html}</li>')
            else:
                items_html.append(f'<li>{text}</li>')
        else:
            items_html.append(f'<li>{item}</li>')
    
    return f'<{tag} class="{list_class} list-inside space-y-1 my-4 text-dark-umber">{"".join(items_html)}</{tag}>'


def render_quote(data):
    """Render quote block."""
    text = data.get('text', '')
    caption = data.get('caption', '')
    alignment = data.get('alignment', 'left')
    
    align_class = 'text-center' if alignment == 'center' else ''
    
    html = f'<blockquote class="border-l-4 border-vintage-gold pl-6 my-6 italic text-dark-umber {align_class}">'
    html += f'<p class="text-lg">{text}</p>'
    if caption:
        html += f'<cite class="block mt-2 text-sm text-vintage-beaver not-italic">— {caption}</cite>'
    html += '</blockquote>'
    return html


def render_code(data):
    """Render code block."""
    code = escape(data.get('code', ''))
    language = data.get('language', '')
    
    return f'<pre class="bg-dark-brown text-heritage-cream rounded-lg p-4 my-4 overflow-x-auto"><code class="text-sm font-mono">{code}</code></pre>'


def render_image(data):
    """Render image block."""
    url = data.get('file', {}).get('url', '') or data.get('url', '')
    caption = data.get('caption', '')
    with_border = data.get('withBorder', False)
    stretched = data.get('stretched', False)
    with_background = data.get('withBackground', False)
    
    if not url:
        return ''
    
    img_classes = ['rounded-lg', 'max-w-full', 'h-auto']
    if with_border:
        img_classes.append('border-2 border-sepia-pale')
    if stretched:
        img_classes.append('w-full')
    
    wrapper_classes = ['my-6']
    if with_background:
        wrapper_classes.append('bg-heritage-cream p-4 rounded-lg')
    if not stretched:
        wrapper_classes.append('text-center')
    
    html = f'<figure class="{" ".join(wrapper_classes)}">'
    html += f'<img src="{url}" alt="{escape(caption)}" class="{" ".join(img_classes)}" loading="lazy">'
    if caption:
        html += f'<figcaption class="text-sm text-vintage-beaver mt-2 text-center">{caption}</figcaption>'
    html += '</figure>'
    return html


def render_embed(data):
    """Render embed block (YouTube, Vimeo, etc.)."""
    embed = data.get('embed', '')
    caption = data.get('caption', '')
    service = data.get('service', '')
    
    if not embed:
        return ''
    
    html = '<figure class="my-6">'
    html += f'<div class="relative pb-[56.25%] h-0 overflow-hidden rounded-lg">'
    html += f'<iframe src="{embed}" class="absolute top-0 left-0 w-full h-full" frameborder="0" allowfullscreen loading="lazy"></iframe>'
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
    title = data.get('title', '')
    message = data.get('message', '')
    
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
                html += f'<th class="px-4 py-3 text-left text-dark-brown font-semibold border-b border-sepia-pale">{cell}</th>'
            html += '</tr></thead><tbody>'
        else:
            if i == 1 and with_headings:
                pass
            html += '<tr class="border-b border-sepia-pale/50 hover:bg-heritage-cream/50">'
            for cell in row:
                html += f'<td class="px-4 py-3 text-dark-umber">{cell}</td>'
            html += '</tr>'
    
    if with_headings:
        html += '</tbody>'
    html += '</table></div>'
    return html


def render_raw(data):
    """Render raw HTML block."""
    return data.get('html', '')


def render_checklist(data):
    """Render checklist block."""
    items = data.get('items', [])
    
    if not items:
        return ''
    
    html = '<ul class="space-y-2 my-4">'
    for item in items:
        text = item.get('text', '')
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
