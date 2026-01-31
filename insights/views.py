"""
Insight views for browsing and managing community articles.
"""
import json
import ast
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import InsightPost, EditSuggestion
from archives.models import Archive, Category
from core.validators import ALLOWED_INSIGHT_SORTS, get_safe_sort
from core.editorjs_helpers import parse_editorjs_content, generate_unique_slug, get_workflow_flags, download_and_save_image_from_url

User = get_user_model()

def get_cached_insight_categories():
    """Cache insight categories for 30 minutes."""
    categories = cache.get('insight_categories')
    if categories is None:
        # Only fetch categories marked for 'insight'
        categories = list(Category.objects.filter(type='insight').annotate(
            post_count=Count('insights', filter=Q(insights__is_published=True))
        ).order_by('name'))
        cache.set('insight_categories', categories, 1800)
    return categories


def get_insight_recommendations(insight, count=9):
    """Efficient recommendation fetching based on shared category."""
    recommendations = InsightPost.objects.filter(
        is_published=True,
        is_approved=True
    ).exclude(pk=insight.pk).select_related('author', 'category').only(
        'id', 'title', 'slug', 'excerpt', 'featured_image', 'created_at', 'author', 'category'
    )
    
    if insight.category:
        recommendations = recommendations.order_by(
            '-category', # Prioritize same category
            '-created_at'
        )
    else:
        recommendations = recommendations.order_by('-created_at')
    
    return recommendations[:count]


def insight_list(request):
    """List all published insights with filtering and pagination."""
    insights = InsightPost.objects.filter(
        is_published=True, is_approved=True
    ).select_related('author', 'category').only(
        'id', 'title', 'slug', 'excerpt', 'featured_image', 'created_at', 'author', 'category'
    )
    
    if search := request.GET.get('search'):
        insights = insights.filter(title__icontains=search)
    
    # FILTER BY CATEGORY (Instead of Tag)
    if category_slug := request.GET.get('category'):
        insights = insights.filter(category__slug=category_slug)
    
    sort = get_safe_sort(request.GET.get('sort', '-created_at'), ALLOWED_INSIGHT_SORTS)
    insights = insights.order_by(sort)
    
    paginator = Paginator(insights, 12)
    posts = paginator.get_page(request.GET.get('page'))
    
    context = {
        'posts': posts,
        'categories': get_cached_insight_categories()
    }
    
    if request.htmx:
        return render(request, 'insights/partials/insight_grid.html', context)
    
    return render(request, 'insights/list.html', context)


def insight_detail(request, slug):
    """Display a single insight with recommendations."""
    insight = get_object_or_404(
        InsightPost.objects.select_related('author', 'category'),
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
        category_id = request.POST.get('category')
        action = request.POST.get('action')
        
        # Prepare context for potential error re-render
        categories = Category.objects.filter(type='insight').order_by('name')
        archive_categories = Category.objects.filter(type='archive').order_by('name')

        if not title or not content_json:
            messages.error(request, 'Please fill in all required fields.')
            context = {
                'archive_title': archive_title,
                'initial_title': title or initial_title,
                'initial_content': content_json or initial_content,
                'initial_excerpt': excerpt or initial_excerpt,
                'categories': categories,
                'archive_categories': archive_categories, # ADDED
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
                'categories': categories,
                'archive_categories': archive_categories, # ADDED
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
        
        # SAVE CATEGORY
        if category_id:
            try:
                insight.category = Category.objects.get(id=category_id, type='insight')
            except Category.DoesNotExist:
                pass
        
        # Handle featured image
        featured_url = request.POST.get('featured_image_url', '').strip()
        if request.FILES.get('featured_image'):
            insight.featured_image = request.FILES['featured_image']
            insight.alt_text = request.POST.get('alt_text', '')
        elif featured_url:
            if download_and_save_image_from_url(insight, 'featured_image', featured_url):
                insight.alt_text = request.POST.get('alt_text', '')
        
        insight.save()
        cache.delete('insight_categories')
        
        # --- PHASE 4: EMAIL NOTIFICATION ---
        if action == 'submit':
            try:
                staff_emails = list(User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True))
                if staff_emails:
                    send_mail(
                        subject=f"New Insight Submitted: {insight.title}",
                        message=f"""
                        A new insight has been submitted by {request.user.get_full_name() or request.user.username}.
                        
                        Title: {insight.title}
                        Excerpt: {insight.excerpt}
                        
                        Review it here: {request.scheme}://{request.get_host()}/users/admin/moderation/
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=staff_emails,
                        fail_silently=True
                    )
            except Exception as e:
                pass # logger.warning(f"Failed to send notification email: {e}")
        # -----------------------------------
        
        return redirect('users:dashboard')
    
    # Context for GET request
    context = {
        'archive_title': archive_title,
        'initial_title': initial_title,
        'initial_content': initial_content,
        'initial_excerpt': initial_excerpt,
        'categories': Category.objects.filter(type='insight').order_by('name'),
        # ADDED: Archive categories for the media upload modal
        'archive_categories': Category.objects.filter(type='archive').order_by('name'),
    }
    return render(request, 'insights/create.html', context)


@login_required
def insight_edit(request, slug):
    """Edit an existing insight post."""
    insight = get_object_or_404(InsightPost, slug=slug, author=request.user)
    
    if request.method == 'POST':
        insight.title = request.POST.get('title', '').strip()[:255]
        insight.excerpt = request.POST.get('excerpt', '').strip()[:500]
        category_id = request.POST.get('category')
        content_json = request.POST.get('content_json')
        
        if content_json:
            try:
                from core.editorjs_helpers import parse_editorjs_content
                insight.content_json = parse_editorjs_content(content_json)
            except (json.JSONDecodeError, ValidationError) as e:
                messages.error(request, f'Invalid content format: {e}')
                return render(request, 'insights/edit.html', {
                    'insight': insight,
                    'initial_content': content_json,
                    'categories': Category.objects.filter(type='insight').order_by('name'),
                    'archive_categories': Category.objects.filter(type='archive').order_by('name'), # ADDED
                })
        
        action = request.POST.get('action')
        
        if action == 'submit':
            insight.pending_approval = True
            insight.submitted_at = timezone.now()
            insight.is_published = False
            insight.is_approved = False
            messages.success(request, 'Your insight has been submitted for approval!')
        else:
            if insight.is_published and insight.is_approved:
                insight.pending_approval = True
                insight.is_published = False
                insight.is_approved = False
            messages.success(request, 'Your insight has been saved!')
        
        # Handle featured image
        featured_url = request.POST.get('featured_image_url', '').strip()
        current_featured_url = insight.featured_image.url if insight.featured_image else ''
        
        if request.FILES.get('featured_image'):
            insight.featured_image = request.FILES['featured_image']
        elif featured_url and featured_url != current_featured_url:
            download_and_save_image_from_url(insight, 'featured_image', featured_url)
        
        # UPDATE CATEGORY
        if category_id:
            try:
                insight.category = Category.objects.get(id=category_id, type='insight')
            except Category.DoesNotExist:
                pass
        else:
            insight.category = None
            
        insight.save()
        cache.delete('insight_categories')
        
        # --- PHASE 4: EMAIL NOTIFICATION ON RESUBMIT ---
        if action == 'submit':
            try:
                staff_emails = list(User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True))
                if staff_emails:
                    send_mail(
                        subject=f"Insight Updated (Review Needed): {insight.title}",
                        message=f"User {request.user.username} updated an insight. Please re-review.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=staff_emails,
                        fail_silently=True
                    )
            except Exception:
                pass
        # -----------------------------------------------
        
        return redirect('users:dashboard')
    
    # Robust JSON parsing for the editor
    initial_content = '{}'
    if insight.content_json:
        if isinstance(insight.content_json, dict):
            initial_content = json.dumps(insight.content_json)
        elif isinstance(insight.content_json, str):
            content_str = insight.content_json.strip()
            try:
                json.loads(content_str)
                initial_content = content_str
            except json.JSONDecodeError:
                try:
                    cleaned_data = ast.literal_eval(content_str)
                    initial_content = json.dumps(cleaned_data)
                except (ValueError, SyntaxError):
                    initial_content = content_str
    
    return render(request, 'insights/edit.html', {
        'insight': insight,
        'initial_content': initial_content,
        'categories': Category.objects.filter(type='insight').order_by('name'),
        # ADDED: Archive categories for the media upload modal
        'archive_categories': Category.objects.filter(type='archive').order_by('name'),
    })


@login_required
def suggest_edit(request, slug):
    """Submit an edit suggestion for an insight."""
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
        
        cache.set(rate_key, suggestion_count + 1, 86400)
        messages.success(request, 'Thank you! Your edit suggestion has been sent to the author.')
        return redirect('insights:detail', slug=slug)
    
    return render(request, 'insights/suggest_edit.html', {'post': insight, 'insight': insight})


@login_required
def insight_delete(request, slug):
    """Delete an insight post (only for drafts/pending, or owner)."""
    insight = get_object_or_404(InsightPost, slug=slug, author=request.user)
    
    if insight.is_published and insight.is_approved and not request.user.is_staff:
        messages.error(request, 'Published insights cannot be deleted. Please contact an administrator.')
        return redirect('insights:detail', slug=slug)
    
    if request.method == 'POST':
        insight_title = insight.title
        insight.delete()
        cache.delete('insight_categories')
        messages.success(request, f'Insight "{insight_title}" has been deleted.')
        return redirect('users:dashboard')
    
    return render(request, 'insights/delete.html', {'insight': insight})