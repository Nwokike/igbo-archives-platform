import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from core.editorjs_helpers import generate_unique_slug, parse_editorjs_content, get_workflow_flags
from archives.models import Category
from .models import LorePost
from .forms import LorePostForm
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

def get_cached_lore_categories():
    categories = cache.get('lore_categories')
    if categories is None:
        from django.db.models import Count
        categories = list(
            Category.objects.filter(type='lore')
            .annotate(count=Count('lore_posts', filter=Q(lore_posts__is_approved=True)))
            .order_by('name')
        )
        cache.set('lore_categories', categories, 3600)
    return categories

def lore_list(request):
    posts = LorePost.objects.filter(is_approved=True, is_published=True).select_related('author', 'category')
    
    if search := request.GET.get('search'):
        posts = posts.filter(Q(title__icontains=search) | Q(excerpt__icontains=search) | Q(legacy_content__icontains=search))
        
    if lore_type := request.GET.get('type'):
        posts = posts.filter(category__slug=lore_type)

    if author_name := request.GET.get('author'):
        posts = posts.filter(
            Q(author__first_name__icontains=author_name) | 
            Q(author__last_name__icontains=author_name) | 
            Q(author__username__icontains=author_name) | 
            Q(original_author__icontains=author_name)
        )

    # Sorting
    sort = request.GET.get('sort', 'recently-added')
    from core.validators import get_safe_sort, ALLOWED_LORE_SORTS
    sort_field = get_safe_sort(sort, ALLOWED_LORE_SORTS)
    posts = posts.order_by(sort_field)
        
    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    if request.htmx:
        return render(request, 'lore/partials/lore_grid.html', {'posts': page_obj})

    context = {
        'posts': page_obj,
        'categories': get_cached_lore_categories()
    }
    return render(request, 'lore/list.html', context)

def lore_detail(request, slug):
    post = get_object_or_404(LorePost.objects.select_related('author', 'category'), slug=slug)
    
    if not post.is_approved or not post.is_published:
        if request.user != post.author and not request.user.is_staff:
            raise Http404("Post not found.")

    # Previous / Next navigation
    published_filter = Q(is_approved=True, is_published=True)
    previous_post = LorePost.objects.filter(
        published_filter, created_at__lt=post.created_at
    ).order_by('-created_at').only('id', 'title', 'slug', 'featured_image', 'image_url').first()

    next_post = LorePost.objects.filter(
        published_filter, created_at__gt=post.created_at
    ).order_by('created_at').only('id', 'title', 'slug', 'featured_image', 'image_url').first()

    # "You May Also Like" — random selection from same category
    similar_ids = list(
        LorePost.objects.filter(
            category=post.category, is_approved=True, is_published=True
        ).exclude(id=post.id).values_list('id', flat=True)[:200]
    )
    if similar_ids:
        selected = random.sample(similar_ids, min(6, len(similar_ids)))
        recommended = LorePost.objects.filter(id__in=selected).select_related('author', 'category')
    else:
        recommended = LorePost.objects.none()
    
    context = {
        'post': post,
        'previous_post': previous_post,
        'next_post': next_post,
        'recommended': recommended,
        'turnstile_site_key': getattr(settings, 'TURNSTILE_SITE_KEY', ''),
    }
    return render(request, 'lore/detail.html', context)

@login_required
def lore_create(request):
    if request.method == 'POST':
        form = LorePostForm(request.POST, request.FILES)
        content_json = request.POST.get('content_json')
        action = request.POST.get('action')
        
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if content_json and content_json != '{}':
                try:
                    post.content_json = parse_editorjs_content(content_json)
                except Exception as e:
                    logger.warning(f"Editor.js parse failed, storing raw: {e}")
                    post.content_json = content_json
            
            # Workflow flags (draft vs submit)
            workflow = get_workflow_flags(action)
            post.is_published = workflow['is_published']
            post.is_approved = workflow['is_approved']
            post.pending_approval = workflow['pending_approval']
            post.submitted_at = workflow['submitted_at']
            
            post.slug = generate_unique_slug(post.title, LorePost)
            
            # Author profile creation logic
            author_name = form.cleaned_data.get('original_author')
            author_about_text = form.cleaned_data.get('original_author_about')
            
            if author_name:
                from archives.models import Author
                author_obj = Author.objects.filter(name__iexact=author_name).first()
                if not author_obj:
                    author_obj = Author.objects.create(name=author_name)
                if author_about_text and not author_obj.description:
                    author_obj.description = author_about_text
                    author_obj.save()
            
            post.save()
            
            # Flush cache
            cache.delete('lore_categories')
            
            if action == 'submit':
                messages.success(request, 'Your Lore post has been submitted for approval!')
                # Bell Notification
                try:
                    from core.notifications_utils import send_post_submitted_notification
                    send_post_submitted_notification(post, post_type='lore post')
                except Exception as e:
                    logger.warning(f"Failed to send in-app notification: {e}")
                
                # Email notification (async)
                try:
                    from core.notifications_utils import send_admin_notification
                    send_admin_notification(
                        subject=f"New Lore Post: {post.title}",
                        description=f"A new lore post has been submitted by {request.user.get_display_name()}.\n\nTitle: {post.title}",
                        target_url="/users/admin/moderation/"
                    )
                except Exception as e:
                    logger.warning(f"Failed to send notification email: {e}")
            else:
                messages.success(request, 'Your Lore post has been saved as a draft!')
            
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LorePostForm()
        
    context = {
        'form': form,
        'title': 'Share Cultural Lore',
        'submit_text': 'Submit Post'
    }
    return render(request, 'lore/form.html', context)

@login_required
def lore_edit(request, slug):
    post = get_object_or_404(LorePost, slug=slug)
    if post.author != request.user and not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You do not have permission to edit this post.")
    
    if request.method == 'POST':
        form = LorePostForm(request.POST, request.FILES, instance=post)
        content_json = request.POST.get('content_json')
        action = request.POST.get('action')
        
        if form.is_valid():
            post = form.save(commit=False)
            if content_json and content_json != '{}':
                try:
                    post.content_json = parse_editorjs_content(content_json)
                except Exception as e:
                    logger.warning(f"Editor.js parse failed, storing raw: {e}")
                    post.content_json = content_json
            
            if action == 'submit':
                workflow = get_workflow_flags(action, is_submit=True)
                post.pending_approval = workflow['pending_approval']
                post.submitted_at = workflow['submitted_at']
                post.is_published = workflow['is_published']
                post.is_approved = workflow['is_approved']
                messages.success(request, 'Your Lore post has been submitted for approval!')
                # Bell Notification
                try:
                    from core.notifications_utils import send_post_submitted_notification
                    send_post_submitted_notification(post, post_type='lore post')
                except Exception as e:
                    logger.warning(f"Failed to send in-app notification: {e}")
            else:
                if post.is_published and post.is_approved:
                    post.pending_approval = True
                    post.is_approved = False
                messages.success(request, 'Your Lore post has been saved!')
            
            # Author profile creation logic
            author_name = form.cleaned_data.get('original_author')
            author_about_text = form.cleaned_data.get('original_author_about')
            
            if author_name:
                from archives.models import Author
                author_obj = Author.objects.filter(name__iexact=author_name).first()
                if not author_obj:
                    author_obj = Author.objects.create(name=author_name)
                if author_about_text and not author_obj.description:
                    author_obj.description = author_about_text
                    author_obj.save()
            
            post.save()
            
            # Flush cache
            cache.delete('lore_categories')
            
            # Email notification on resubmit (async)
            if action == 'submit':
                try:
                    from core.notifications_utils import send_admin_notification
                    send_admin_notification(
                        subject=f"Lore Post Updated: {post.title}",
                        description=f"User {request.user.username} updated a lore post. Please review.",
                        target_url="/users/admin/moderation/"
                    )
                except Exception:
                    pass
            
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LorePostForm(instance=post)
        
    import json
    initial_content = ''
    if post.content_json:
        initial_content = json.dumps(post.content_json) if isinstance(post.content_json, dict) else post.content_json

    context = {
        'form': form,
        'post': post,
        'initial_content': initial_content,
        'title': 'Edit Lore',
        'submit_text': 'Update Post'
    }
    return render(request, 'lore/form.html', context)

@login_required
def lore_delete(request, slug):
    post = get_object_or_404(LorePost, slug=slug, author=request.user)
    
    if post.is_published and post.is_approved and not request.user.is_staff:
        messages.error(request, 'Published lore posts cannot be deleted. Please contact an administrator.')
        return redirect('lore:detail', slug=slug)
    
    if request.method == 'POST':
        post.delete()
        cache.delete('lore_categories')
        messages.success(request, 'Lore post deleted successfully.')
        return redirect('users:dashboard')
    return render(request, 'lore/delete.html', {'post': post})
