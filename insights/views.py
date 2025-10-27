from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import InsightPost, EditSuggestion
from archives.models import Archive
from django.core.paginator import Paginator
from django.utils.text import slugify
import json
import re

def insight_list(request):
    from taggit.models import Tag
    
    insights = InsightPost.objects.filter(is_published=True, is_approved=True)
    
    search = request.GET.get('search')
    if search:
        insights = insights.filter(title__icontains=search)
    
    tag = request.GET.get('tag')
    if tag:
        insights = insights.filter(tags__name=tag)
    
    sort = request.GET.get('sort', '-created_at')
    insights = insights.order_by(sort)
    
    paginator = Paginator(insights, 12)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    tags = Tag.objects.filter(insightpost__isnull=False).distinct()
    
    context = {
        'posts': posts,
        'tags': tags
    }
    
    if request.htmx:
        return render(request, 'insights/partials/insight_grid.html', context)
    
    return render(request, 'insights/list.html', context)

def insight_detail(request, slug):
    insight = get_object_or_404(InsightPost, slug=slug, is_published=True, is_approved=True)
    
    # Get previous and next insights
    previous_insight = InsightPost.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__lt=insight.created_at
    ).order_by('-created_at').first()
    
    next_insight = InsightPost.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__gt=insight.created_at
    ).order_by('created_at').first()
    
    # Get recommended insights (9 total: same tags, same author, or recent)
    recommended = InsightPost.objects.filter(
        is_published=True,
        is_approved=True
    ).exclude(slug=insight.slug)
    
    tag_names = insight.tags.values_list('name', flat=True)
    if tag_names:
        recommended = recommended.filter(tags__name__in=tag_names).distinct()
    
    # If we need more, add by author
    if recommended.count() < 9:
        recommended = InsightPost.objects.filter(
            is_published=True,
            is_approved=True,
            author=insight.author
        ).exclude(slug=insight.slug)
    
    # If still need more, add recent
    if recommended.count() < 9:
        recommended = InsightPost.objects.filter(
            is_published=True,
            is_approved=True
        ).exclude(slug=insight.slug).order_by('-created_at')
    
    recommended = recommended[:9]
    
    context = {
        'insight': insight,
        'previous_insight': previous_insight,
        'next_insight': next_insight,
        'recommended': recommended,
    }
    
    return render(request, 'insights/detail.html', context)

def extract_first_image_from_editorjs(content_json_str):
    """Extract first image URL from Editor.js JSON content"""
    try:
        content = json.loads(content_json_str)
        for block in content.get('blocks', []):
            if block.get('type') == 'image':
                return block.get('data', {}).get('file', {}).get('url')
    except:
        pass
    return None

@login_required
def insight_create(request):
    archive_id = request.GET.get('archive_id')
    initial_title = ''
    initial_content = ''
    initial_excerpt = ''
    archive_title = ''
    
    if archive_id:
        try:
            archive = Archive.objects.get(id=archive_id)
            archive_title = archive.title
            initial_title = f"Insights on {archive.title}"
            # Create Editor.js JSON format
            initial_content_data = {
                "time": timezone.now().timestamp() * 1000,
                "blocks": [
                    {
                        "type": "paragraph",
                        "data": {
                            "text": f"Related to <a href='/archives/{archive.id}/'>{archive.title}</a>"
                        }
                    },
                    {
                        "type": "paragraph",
                        "data": {
                            "text": archive.description
                        }
                    }
                ],
                "version": "2.28.0"
            }
            initial_content = json.dumps(initial_content_data)
            initial_excerpt = f"A reflection on {archive.title}"
        except Archive.DoesNotExist:
            pass
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content_json = request.POST.get('content_json')
        excerpt = request.POST.get('excerpt', '')
        action = request.POST.get('action')  # 'save' or 'submit'
        
        # Validate required fields
        if not title or not content_json:
            messages.error(request, 'Please fill in all required fields.')
            context = {
                'archive_title': archive_title,
                'initial_title': title or initial_title,
                'initial_content': content_json or initial_content,
                'initial_excerpt': excerpt or initial_excerpt,
            }
            return render(request, 'insights/create.html', context)
        
        # Generate unique slug
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while InsightPost.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Determine publishing status based on action
        is_published = False
        is_approved = False
        pending_approval = False
        submitted_at = None
        
        if action == 'submit':
            pending_approval = True
            submitted_at = timezone.now()
            messages.success(request, 'Your insight has been submitted for approval!')
        else:  # action == 'save'
            messages.success(request, 'Your insight has been saved as a draft!')
        
        # Create insight
        insight = InsightPost.objects.create(
            title=title,
            slug=slug,
            content_json=content_json,
            excerpt=excerpt,
            author=request.user,
            is_published=is_published,
            is_approved=is_approved,
            pending_approval=pending_approval,
            submitted_at=submitted_at
        )
        
        # Handle featured image
        if request.FILES.get('featured_image'):
            insight.featured_image = request.FILES['featured_image']
            insight.alt_text = request.POST.get('alt_text', '')
        else:
            # Auto-select first image from content
            first_image_url = extract_first_image_from_editorjs(content_json)
            if first_image_url:
                # Note: This is a URL, we'd need to download and save it
                # For now, we'll just note it in a comment
                pass
        
        # Add tags
        tags = request.POST.get('tags', '').split(',')
        for tag in tags:
            if tag.strip():
                insight.tags.add(tag.strip())
        
        insight.save()
        
        return redirect('users:dashboard')
    
    context = {
        'archive_title': archive_title,
        'initial_title': initial_title,
        'initial_content': initial_content,
        'initial_excerpt': initial_excerpt,
    }
    return render(request, 'insights/create.html', context)

@login_required
def insight_edit(request, slug):
    insight = get_object_or_404(InsightPost, slug=slug, author=request.user)
    
    if request.method == 'POST':
        insight.title = request.POST.get('title')
        insight.excerpt = request.POST.get('excerpt', '')
        content_json = request.POST.get('content_json')
        if content_json:
            insight.content_json = content_json
        
        action = request.POST.get('action')
        
        if action == 'submit':
            insight.pending_approval = True
            insight.submitted_at = timezone.now()
            insight.is_published = False
            insight.is_approved = False
            messages.success(request, 'Your insight has been submitted for approval!')
        else:  # action == 'save'
            messages.success(request, 'Your insight has been saved!')
        
        if request.FILES.get('featured_image'):
            insight.featured_image = request.FILES['featured_image']
        
        # Clear existing tags and add new ones
        insight.tags.clear()
        tags = request.POST.get('tags', '').split(',')
        for tag in tags:
            if tag.strip():
                insight.tags.add(tag.strip())
        
        insight.save()
        return redirect('users:dashboard')
    
    # Prepare initial content for editor
    initial_content = ''
    if insight.content_json:
        initial_content = insight.content_json
    
    return render(request, 'insights/edit.html', {
        'insight': insight,
        'initial_content': initial_content
    })

@login_required
def suggest_edit(request, slug):
    insight = get_object_or_404(InsightPost, slug=slug)
    if request.method == 'POST':
        suggestion_text = request.POST.get('suggestion')
        EditSuggestion.objects.create(
            post=insight,
            suggested_by=request.user if request.user.is_authenticated else None,
            suggestion_text=suggestion_text
        )
        messages.success(request, 'Thank you! Your edit suggestion has been sent to the author.')
        return redirect('insights:detail', slug=slug)
    return render(request, 'insights/suggest_edit.html', {'insight': insight})
