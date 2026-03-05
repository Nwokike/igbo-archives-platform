import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from core.editorjs_helpers import generate_unique_slug
from archives.models import Category
from .models import LorePost
from .forms import LorePostForm

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
            
    similar_ids = list(
        LorePost.objects.filter(
            category=post.category, is_approved=True, is_published=True
        ).exclude(id=post.id).values_list('id', flat=True)
    )
    if similar_ids:
        selected = random.sample(similar_ids, min(3, len(similar_ids)))
        similar_posts = LorePost.objects.filter(id__in=selected).select_related('author', 'category')
    else:
        similar_posts = LorePost.objects.none()
    
    context = {
        'post': post,
        'similar_posts': similar_posts,
    }
    return render(request, 'lore/detail.html', context)

@login_required
def lore_create(request):
    if request.method == 'POST':
        form = LorePostForm(request.POST, request.FILES)
        content_json = request.POST.get('content_json')
        
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if content_json and content_json != '{}':
                post.content_json = content_json
            post.is_published = True
            post.is_approved = False 
            
            post.slug = generate_unique_slug(post.title, LorePost)
            
            # Author profile creation logic
            author_name = form.cleaned_data.get('original_author')
            author_about_text = form.cleaned_data.get('original_author_about')
            
            if author_name:
                from archives.models import Author
                author_obj, created = Author.objects.get_or_create(
                    name__iexact=author_name,
                    defaults={'name': author_name}
                )
                if author_about_text and not author_obj.description:
                    author_obj.description = author_about_text
                    author_obj.save()
            
            post.save()
            
            # Flush cache
            cache.delete('lore_categories')
            
            messages.success(request, 'Your Lore post has been submitted and is pending administrator approval.')
            return redirect('lore:detail', slug=post.slug)
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
        
        if form.is_valid():
            post = form.save(commit=False)
            if content_json and content_json != '{}':
                post.content_json = content_json
            
            post.is_approved = False
            
            # Author profile creation logic
            author_name = form.cleaned_data.get('original_author')
            author_about_text = form.cleaned_data.get('original_author_about')
            
            if author_name:
                from archives.models import Author
                author_obj, created = Author.objects.get_or_create(
                    name__iexact=author_name,
                    defaults={'name': author_name}
                )
                if author_about_text:
                    author_obj.description = author_about_text
                    author_obj.save()
            
            post.save()
            
            # Flush cache
            cache.delete('lore_categories')
            
            messages.success(request, 'Your Lore post has been updated and is pending re-approval.')
            return redirect('lore:detail', slug=post.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LorePostForm(instance=post)
        
    context = {
        'form': form,
        'post': post,
        'title': 'Edit Lore',
        'submit_text': 'Update Post'
    }
    return render(request, 'lore/form.html', context)

@login_required
def lore_delete(request, slug):
    post = get_object_or_404(LorePost, slug=slug, author=request.user)
    if request.method == 'POST':
        post.delete()
        cache.delete('lore_categories')
        messages.success(request, 'Lore post deleted successfully.')
        return redirect('lore:list')
    return render(request, 'lore/delete.html', {'post': post})
