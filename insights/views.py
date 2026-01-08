"""
Insight views for browsing and managing community articles.
"""
import json
import uuid
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
from core.validators import ALLOWED_INSIGHT_SORTS, get_safe_sort


def get_cached_insight_tags():
    """Cache tags for 30 minutes."""
    tags = cache.get('insight_tags')
    if tags is None:
        from taggit.models import Tag
        tags = list(Tag.objects.filter(insightpost__isnull=False).distinct()[:50])
        cache.set('insight_tags', tags, 1800)
    return tags


def get_insight_recommendations(insight, count=9):
    """Efficient recommendation fetching based on shared tags."""
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
    """List all published insights with filtering and pagination."""
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
    
    sort = get_safe_sort(request.GET.get('sort', '-created_at'), ALLOWED_INSIGHT_SORTS)
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
    """Display a single insight with recommendations."""
    insight = get_object_or_404(
        InsightPost.objects.select_related('author'),
        slug=slug, is_published=True, is_approved=True
    )
    
    previous_insight = InsightPost.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__lt=insight.created_at
    ).order_by('-created_at').only('id', 'title', 'slug').first()
    
    next_insight = InsightPost.objects.filter(
        is_published=True,
        is_approved=True,
        created_at__gt=insight.created_at
    ).order_by('created_at').only('id', 'title', 'slug').first()
    
    recommended = get_insight_recommendations(insight, 9)
    
    context = {
        'insight': insight,
        'previous_insight': previous_insight,
        'next_insight': next_insight,
        'recommended': recommended,
    }
    
    return render(request, 'insights/detail.html', context)


@login_required
def insight_create(request):
    """Create a new insight post."""
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
        title = request.POST.get('title', '').strip()
        content_json = request.POST.get('content_json')
        excerpt = request.POST.get('excerpt', '').strip()
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
        
        try:
            content_data = json.loads(content_json) if isinstance(content_json, str) else content_json
        except json.JSONDecodeError:
            messages.error(request, 'Invalid content format. Please try again.')
            context = {
                'archive_title': archive_title,
                'initial_title': title,
                'initial_content': content_json,
                'initial_excerpt': excerpt,
            }
            return render(request, 'insights/create.html', context)
        
        base_slug = slugify(title)[:200]
        slug = base_slug
        counter = 1
        while InsightPost.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            if counter > 100:
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                break
        
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
        
        tags = [t.strip()[:50] for t in request.POST.get('tags', '').split(',') if t.strip()][:20]
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
    """Edit an existing insight post."""
    insight = get_object_or_404(InsightPost, slug=slug, author=request.user)
    
    if request.method == 'POST':
        insight.title = request.POST.get('title', '').strip()[:255]
        insight.excerpt = request.POST.get('excerpt', '').strip()[:500]
        content_json = request.POST.get('content_json')
        
        if content_json:
            try:
                insight.content_json = json.loads(content_json) if isinstance(content_json, str) else content_json
            except json.JSONDecodeError:
                messages.error(request, 'Invalid content format. Please try again.')
                return render(request, 'insights/edit.html', {
                    'insight': insight,
                    'initial_content': content_json
                })
        
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
        tags = [t.strip()[:50] for t in request.POST.get('tags', '').split(',') if t.strip()][:20]
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
    """Submit an edit suggestion for an insight."""
    from core.notifications_utils import send_edit_suggestion_notification
    
    insight = get_object_or_404(InsightPost, slug=slug)
    
    rate_key = f'suggestion_rate_{request.user.id}'
    suggestion_count = cache.get(rate_key, 0)
    if suggestion_count >= 5:
        messages.error(request, 'You have reached the daily limit for edit suggestions.')
        return redirect('insights:detail', slug=slug)
    
    if request.method == 'POST':
        suggestion_text = request.POST.get('suggestion', '').strip()
        
        if not suggestion_text:
            messages.error(request, 'Please provide a suggestion.')
            return render(request, 'insights/suggest_edit.html', {'insight': insight})
        
        suggestion = EditSuggestion.objects.create(
            post=insight,
            suggested_by=request.user,
            suggestion_text=suggestion_text[:5000]
        )
        
        # Send notification to post author
        send_edit_suggestion_notification(suggestion)
        
        cache.set(rate_key, suggestion_count + 1, 86400)
        messages.success(request, 'Thank you! Your edit suggestion has been sent to the author.')
        return redirect('insights:detail', slug=slug)
    
    return render(request, 'insights/suggest_edit.html', {'insight': insight})
