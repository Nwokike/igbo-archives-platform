import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.text import slugify
from .models import InsightPost, EditSuggestion
from archives.models import Archive


def get_cached_insight_tags():
    """Cache tags for 30 minutes"""
    tags = cache.get('insight_tags')
    if tags is None:
        from taggit.models import Tag
        tags = list(Tag.objects.filter(insightpost__isnull=False).distinct()[:50])
        cache.set('insight_tags', tags, 1800)
    return tags


def get_insight_recommendations(insight, count=9):
    """Efficient recommendation fetching"""
    tag_names = list(insight.tags.values_list('name', flat=True))
    
    recommendations = InsightPost.objects.filter(
        is_published=True,
        is_approved=True
    ).exclude(pk=insight.pk).select_related('author').only(
        'id', 'title', 'slug', 'excerpt', 'featured_image', 'created_at',
        'author__full_name', 'author__username'
    )
    
    if tag_names:
        recommendations = recommendations.annotate(
            tag_matches=Count('tags', filter=Q(tags__name__in=tag_names))
        ).order_by('-tag_matches', '-created_at')
    else:
        recommendations = recommendations.order_by('-created_at')
    
    return recommendations[:count]


def insight_list(request):
    insights = InsightPost.objects.filter(
        is_published=True, is_approved=True
    ).select_related('author').prefetch_related('tags').only(
        'id', 'title', 'slug', 'excerpt', 'featured_image', 'created_at',
        'author__full_name', 'author__username'
    )
    
    if search := request.GET.get('search'):
        insights = insights.filter(title__icontains=search)
    
    if tag := request.GET.get('tag'):
        insights = insights.filter(tags__name=tag)
    
    sort = request.GET.get('sort', '-created_at')
    insights = insights.order_by(sort)
    
    paginator = Paginator(insights, 12)
    posts = paginator.get_page(request.GET.get('page'))
    
    context = {
        'posts': posts,
        'tags': get_cached_insight_tags()
    }
    
    if request.htmx:
        return render(request, 'insights/partials/insight_grid.html', context)
    
    return render(request, 'insights/list.html', context)


def insight_detail(request, slug):
    insight = get_object_or_404(
        InsightPost.objects.select_related('author'),
        slug=slug, is_published=True, is_approved=True
    )
    
    previous_insight = InsightPost.objects.filter(
        is_published=True,
        is_approved=True,
        pk__lt=insight.pk
    ).order_by('-pk').only('id', 'title', 'slug').first()
    
    next_insight = InsightPost.objects.filter(
        is_published=True,
        is_approved=True,
        pk__gt=insight.pk
    ).order_by('pk').only('id', 'title', 'slug').first()
    
    recommended = get_insight_recommendations(insight, 9)
    
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
        content = json.loads(content_json_str) if isinstance(content_json_str, str) else content_json_str
        for block in content.get('blocks', []):
            if block.get('type') == 'image':
                return block.get('data', {}).get('file', {}).get('url')
    except Exception:
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
            archive = Archive.objects.only('id', 'title', 'description').get(id=archive_id)
            archive_title = archive.title
            initial_title = f"Insights on {archive.title}"
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
        action = request.POST.get('action')
        
        if not title or not content_json:
            messages.error(request, 'Please fill in all required fields.')
            context = {
                'archive_title': archive_title,
                'initial_title': title or initial_title,
                'initial_content': content_json or initial_content,
                'initial_excerpt': excerpt or initial_excerpt,
            }
            return render(request, 'insights/create.html', context)
        
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while InsightPost.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        is_published = False
        is_approved = False
        pending_approval = False
        submitted_at = None
        
        if action == 'submit':
            pending_approval = True
            submitted_at = timezone.now()
            messages.success(request, 'Your insight has been submitted for approval!')
        else:
            messages.success(request, 'Your insight has been saved as a draft!')
        
        try:
            content_data = json.loads(content_json) if isinstance(content_json, str) else content_json
        except json.JSONDecodeError:
            content_data = content_json
        
        insight = InsightPost.objects.create(
            title=title,
            slug=slug,
            content_json=content_data,
            excerpt=excerpt,
            author=request.user,
            is_published=is_published,
            is_approved=is_approved,
            pending_approval=pending_approval,
            submitted_at=submitted_at
        )
        
        if request.FILES.get('featured_image'):
            insight.featured_image = request.FILES['featured_image']
            insight.alt_text = request.POST.get('alt_text', '')
        
        tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
        if tags:
            insight.tags.add(*tags)
        
        insight.save()
        
        cache.delete('insight_tags')
        
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
            try:
                insight.content_json = json.loads(content_json) if isinstance(content_json, str) else content_json
            except json.JSONDecodeError:
                insight.content_json = content_json
        
        action = request.POST.get('action')
        
        if action == 'submit':
            insight.pending_approval = True
            insight.submitted_at = timezone.now()
            insight.is_published = False
            insight.is_approved = False
            messages.success(request, 'Your insight has been submitted for approval!')
        else:
            messages.success(request, 'Your insight has been saved!')
        
        if request.FILES.get('featured_image'):
            insight.featured_image = request.FILES['featured_image']
        
        insight.tags.clear()
        tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
        if tags:
            insight.tags.add(*tags)
        
        insight.save()
        
        cache.delete('insight_tags')
        
        return redirect('users:dashboard')
    
    initial_content = ''
    if insight.content_json:
        initial_content = json.dumps(insight.content_json) if isinstance(insight.content_json, dict) else insight.content_json
    
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
