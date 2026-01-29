"""
Insight views for browsing and managing community articles.
"""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone
from .models import InsightPost, EditSuggestion
from archives.models import Archive, Category
from core.validators import ALLOWED_INSIGHT_SORTS, get_safe_sort
from core.editorjs_helpers import parse_editorjs_content, parse_tags, generate_unique_slug, get_workflow_flags, download_and_save_image_from_url


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
        'id', 'title', 'slug', 'excerpt', 'featured_image', 'created_at'
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
        'id', 'title', 'slug', 'excerpt', 'featured_image', 'created_at'
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
            content_data = parse_editorjs_content(content_json)
        except ValidationError as e:
            messages.error(request, str(e))
            context = {
                'archive_title': archive_title,
                'initial_title': title,
                'initial_content': content_json,
                'initial_excerpt': excerpt,
            }
            return render(request, 'insights/create.html', context)
        
        slug = generate_unique_slug(title, InsightPost)
        workflow_flags = get_workflow_flags(action, is_submit=(action == 'submit'))
        
        if action == 'submit':
            messages.success(request, 'Your insight has been submitted for approval!')
        else:
            messages.success(request, 'Your insight has been saved as a draft!')
        
        insight = InsightPost.objects.create(
            title=title[:200],
            slug=slug,
            content_json=content_data,
            excerpt=excerpt[:500] if excerpt else '',
            author=request.user,
            **workflow_flags
        )
        
        # Handle featured image - prioritize file upload, fallback to URL
        featured_url = request.POST.get('featured_image_url', '').strip()
        if request.FILES.get('featured_image'):
            insight.featured_image = request.FILES['featured_image']
            insight.alt_text = request.POST.get('alt_text', '')
        elif featured_url:
            # Download and save featured image from URL (auto-creates featured_image)
            if download_and_save_image_from_url(insight, 'featured_image', featured_url):
                insight.alt_text = request.POST.get('alt_text', '')
        
        tags = parse_tags(request.POST.get('tags', ''))
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
        'categories': Category.objects.all(),
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
                from core.editorjs_helpers import parse_editorjs_content
                insight.content_json = parse_editorjs_content(content_json)
            except (json.JSONDecodeError, ValidationError) as e:
                messages.error(request, f'Invalid content format: {e}')
                return render(request, 'insights/edit.html', {
                    'insight': insight,
                    'initial_content': content_json
                })
        
        action = request.POST.get('action')
        
        # Publishing is purely admin-controlled via moderation workflow
        # Users can only submit for approval, not self-publish
        if action == 'submit':
            insight.pending_approval = True
            insight.submitted_at = timezone.now()
            insight.is_published = False
            insight.is_approved = False
            messages.success(request, 'Your insight has been submitted for approval!')
        else:
            # Save as draft - preserve existing approval status
            # Only reset if it was previously published/approved and user is making changes
            if insight.is_published and insight.is_approved:
                # Changes to approved content require re-approval
                insight.pending_approval = True
                insight.is_published = False
                insight.is_approved = False
            messages.success(request, 'Your insight has been saved!')
        
        # Handle featured image update - prioritize file upload, fallback to URL
        featured_url = request.POST.get('featured_image_url', '').strip()
        current_featured_url = insight.featured_image.url if insight.featured_image else ''
        
        if request.FILES.get('featured_image'):
            insight.featured_image = request.FILES['featured_image']
        elif featured_url and featured_url != current_featured_url:
            # Download and save featured image from URL if changed
            download_and_save_image_from_url(insight, 'featured_image', featured_url)
        
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
        suggestion_text = request.POST.get('suggestion_text', request.POST.get('suggestion', '')).strip()
        
        if not suggestion_text:
            messages.error(request, 'Please provide a suggestion.')
            return render(request, 'insights/suggest_edit.html', {'post': insight, 'insight': insight})
        
        suggestion = EditSuggestion.objects.create(
            post=insight,
            suggested_by=request.user,
            suggestion_text=suggestion_text[:5000]
        )
        
        # Note: Notification is sent by signal in signals.py
        
        cache.set(rate_key, suggestion_count + 1, 86400)
        messages.success(request, 'Thank you! Your edit suggestion has been sent to the author.')
        return redirect('insights:detail', slug=slug)
    
    return render(request, 'insights/suggest_edit.html', {'post': insight, 'insight': insight})


@login_required
def insight_delete(request, slug):
    """Delete an insight post (only for drafts/pending, or owner)."""
    insight = get_object_or_404(InsightPost, slug=slug, author=request.user)
    
    # Only allow deletion if not approved (draft/pending) or if user is owner
    if insight.is_published and insight.is_approved and not request.user.is_staff:
        messages.error(request, 'Published insights cannot be deleted. Please contact an administrator.')
        return redirect('insights:detail', slug=slug)
    
    if request.method == 'POST':
        insight_title = insight.title
        insight.delete()
        cache.delete('insight_tags')
        messages.success(request, f'Insight "{insight_title}" has been deleted.')
        return redirect('users:dashboard')
    
    return render(request, 'insights/delete.html', {'insight': insight})
