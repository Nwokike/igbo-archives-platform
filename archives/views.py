"""
Archive views for browsing and managing cultural archives.
"""
import random  # Non-cryptographic use for content recommendations
import logging
import nh3
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.db import transaction
from django.db.models import Q
from django.conf import settings        # Added for email settings
from django.contrib.auth import get_user_model # Added to find staff

from .models import Archive, Category, ArchiveItem, Author
from .forms import ArchiveForm, ArchiveItemFormSet
from core.validators import ALLOWED_ARCHIVE_SORTS, get_safe_sort
from core.views import get_all_approved_archive_ids
from core.editorjs_helpers import generate_unique_slug

User = get_user_model()
logger = logging.getLogger(__name__)

def get_cached_categories():
    """Cache categories for 1 hour (Archives only)."""
    categories = cache.get('archive_categories')
    if categories is None:
        # STRICT FILTER: Only show categories meant for Archives
        # Annotate with count for template usage
        from django.db.models import Count
        categories = list(
            Category.objects.filter(type='archive')
            .annotate(count=Count('archive', filter=Q(archive__is_approved=True)))
            .order_by('name')
        )
        cache.set('archive_categories', categories, 3600)
    return categories


def get_random_recommendations(exclude_pk, count=9):
    """Memory-efficient random archive selection."""
    archive_ids = get_all_approved_archive_ids()
    available_ids = [aid for aid in archive_ids if aid != exclude_pk]
    
    if not available_ids:
        return Archive.objects.none()
    
    sample_size = min(count, len(available_ids))
    random_ids = random.sample(available_ids, sample_size)
    
    return Archive.objects.filter(pk__in=random_ids).select_related('uploaded_by', 'category')


def archive_list(request):
    """List all approved archives with filtering and pagination."""
    # REMOVED: prefetch_related('tags')
    archives = Archive.objects.filter(is_approved=True).select_related(
        'uploaded_by', 'category', 'author'
    ).only(
        'id', 'title', 'archive_type', 'image', 'featured_image',
        'alt_text', 'description', 'created_at', 'uploaded_by_id', 'category_id',
        'author_id', 'uploaded_by__full_name', 'uploaded_by__username',
        'category__name', 'category__slug', 'sort_year'
    )
    
    if category := request.GET.get('category'):
        archives = archives.filter(category__slug=category)
    
    if author_query := request.GET.get('author'):
        archives = archives.filter(
            Q(author__name__icontains=author_query) | 
            Q(original_author__icontains=author_query) |
            Q(author__slug=author_query)
        )
    
    if circa_date := request.GET.get('date'):
        archives = archives.filter(circa_date__icontains=circa_date)
    
    if search := request.GET.get('search'):
        archives = archives.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(original_author__icontains=search)
        )
    
    if archive_type := request.GET.get('type'):
        archives = archives.filter(archive_type=archive_type)
    
    sort = get_safe_sort(request.GET.get('sort', '-created_at'), ALLOWED_ARCHIVE_SORTS)
    archives = archives.order_by(sort)
    
    paginator = Paginator(archives, 12)
    archives_page = paginator.get_page(request.GET.get('page'))
    
    context = {
        'archives': archives_page,
        'categories': get_cached_categories(),
    }
    
    if request.htmx:
        return render(request, 'archives/partials/archive_grid.html', context)
    
    return render(request, 'archives/list.html', context)


def archive_detail(request, pk=None, slug=None):
    """Display a single archive with recommendations."""
    if slug:
        archive = get_object_or_404(
            Archive.objects.select_related('uploaded_by', 'category', 'author').prefetch_related('items'),
            slug=slug
        )
    elif pk:
        archive = get_object_or_404(
            Archive.objects.select_related('uploaded_by', 'category', 'author').prefetch_related('items'),
            pk=pk
        )
        if archive.slug:
            return redirect('archives:detail', slug=archive.slug, permanent=True)
    else:
        raise Http404("Archive not found")
    
    if not archive.is_approved:
        if request.user.is_authenticated and (archive.uploaded_by == request.user or request.user.is_staff):
            if archive.slug:
                return redirect('archives:edit', slug=archive.slug)
            return redirect('archives:edit', pk=archive.pk)
        raise Http404("Archive not found")
    
    similar_archives = Archive.objects.filter(
        is_approved=True,
        category=archive.category
    ).exclude(pk=archive.pk).select_related('uploaded_by', 'author')[:5]
    
    previous_archive = Archive.objects.filter(
        is_approved=True, created_at__lt=archive.created_at
    ).order_by('-created_at').only('id', 'title', 'slug').first()
    
    next_archive = Archive.objects.filter(
        is_approved=True, created_at__gt=archive.created_at
    ).order_by('created_at').only('id', 'title', 'slug').first()
    
    recommended = get_random_recommendations(archive.pk, count=9)
    
    archive_items = archive.items.all().order_by('item_number')
    
    context = {
        'archive': archive,
        'archive_items': archive_items,
        'similar_archives': similar_archives,
        'previous_archive': previous_archive,
        'next_archive': next_archive,
        'recommended': recommended,
    }
    
    return render(request, 'archives/detail.html', context)


def author_detail(request, slug):
    author = get_object_or_404(Author, slug=slug)
    
    archives_list = Archive.objects.filter(
        is_approved=True, 
        author=author
    ).select_related('category', 'uploaded_by').order_by('-created_at')
    
    paginator = Paginator(archives_list, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'author': author,
        'archives': page_obj,
    }
    return render(request, 'archives/author_detail.html', context)


@login_required
def metadata_suggestions(request):
    """Suggestions for autocomplete (Authors, Dates)."""
    query = request.GET.get('q', '')
    field = request.GET.get('field', 'author')
    results = []
    
    if len(query) > 1:
        if field == 'author':
            results = list(Author.objects.filter(
                name__icontains=query
            ).values_list('name', flat=True)[:10])
            
            if len(results) < 5:
                text_results = Archive.objects.filter(
                    original_author__icontains=query
                ).values_list('original_author', flat=True).distinct()[:5]
                results = list(set(results + list(text_results)))[:10]
            
        elif field == 'date':
            results = list(Archive.objects.filter(
                circa_date__icontains=query
            ).values_list('circa_date', flat=True).distinct()[:10])

    return JsonResponse({'results': results})



@login_required
def archive_create(request):
    """Create a new archive."""
    if request.method == 'POST':
        form = ArchiveForm(request.POST)
        formset = ArchiveItemFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                archive = form.save(commit=False)
                archive.uploaded_by = request.user
                archive.is_approved = False
                
                if not archive.slug:
                    archive.slug = generate_unique_slug(archive.title, Archive)
                
                archive.description = nh3.clean(archive.description)
                archive.save()
                
                # REMOVED: form.save_m2m() (Tags are gone)
                
                items = formset.save(commit=False)
                if not items:
                    messages.error(request, 'You must upload at least one item.')
                    return render(request, 'archives/create.html', {
                        'form': form,
                        'formset': formset,
                        'categories': get_cached_categories()
                    })

                for i, item in enumerate(items):
                    item.archive = archive
                    item.item_number = i + 1
                    item.save()
                
                # Signals handle sync_parent_archive_with_first_item automatically
                
                # Bell Notification
                try:
                    from core.notifications_utils import send_post_submitted_notification
                    send_post_submitted_notification(archive, post_type='archive')
                except Exception as e:
                    logger.warning(f"Failed to send in-app notification: {e}")
                
                # Email Notification (async via Huey)
                try:
                    from .tasks import send_archive_notification_email
                    staff_emails = list(User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True))
                    if staff_emails:
                        send_archive_notification_email(
                            subject=f"New Archive Submitted: {archive.title}",
                            message_body=(
                                f"A new archive has been submitted by {request.user.get_full_name() or request.user.username}.\n\n"
                                f"Title: {archive.title}\n"
                                f"Description: {archive.description[:200]}...\n\n"
                                f"Review it here: {request.scheme}://{request.get_host()}/users/admin/moderation/"
                            ),
                            staff_emails=staff_emails,
                        )
                except Exception as e:
                    logger.warning(f"Failed to schedule notification email: {e}")
                
                messages.success(request, 'Archive uploaded successfully! It will be reviewed by our team.')

                if archive.slug:
                    return redirect('archives:detail', slug=archive.slug)
                return redirect('archives:detail', pk=archive.pk)
        else:
            messages.error(request, 'Please check the form for errors.')
    else:
        form = ArchiveForm()
        formset = ArchiveItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'categories': get_cached_categories()
    }
    return render(request, 'archives/create.html', context)


@login_required
def archive_edit(request, pk=None, slug=None):
    """Edit an existing archive."""
    if slug:
        archive = get_object_or_404(Archive, slug=slug, uploaded_by=request.user)
    elif pk:
        archive = get_object_or_404(Archive, pk=pk, uploaded_by=request.user)
    else:
        raise Http404("Archive not found")
    
    if request.method == 'POST':
        form = ArchiveForm(request.POST, instance=archive)
        formset = ArchiveItemFormSet(request.POST, request.FILES, instance=archive)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                archive = form.save(commit=False)
                
                old_title = form.initial.get('title', '')
                if archive.title != old_title or not archive.slug:
                    archive.slug = generate_unique_slug(archive.title, Archive, exclude_pk=archive.pk)
                
                archive.description = nh3.clean(archive.description)
                archive.save()
                
                # REMOVED: form.save_m2m() (Tags are gone)
                
                items = formset.save(commit=False)
                
                for obj in formset.deleted_objects:
                    obj.delete()
                
                for i, item in enumerate(items):
                    item.archive = archive
                    if not item.item_number:
                        max_num = archive.items.aggregate(models.Max('item_number'))['item_number__max'] or 0
                        item.item_number = max_num + 1
                    item.save()
                
                # Signals handle sync_parent_archive_with_first_item automatically
                
                if archive.is_approved:
                    # Reset approval if edited
                    archive.is_approved = False
                    archive.save(update_fields=['is_approved'])
                    cache.delete('all_approved_archive_ids')
                    cache.delete('archive_categories')
                    
                    # Notify admin of re-submission (Optional, re-using logic)
                    try:
                        staff_emails = list(User.objects.filter(is_staff=True).exclude(email='').values_list('email', flat=True))
                        if staff_emails:
                            send_mail(
                                subject=f"Archive Updated (Review Needed): {archive.title}",
                                message=f"User {request.user.username} updated an archive. Please re-review.",
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=staff_emails,
                                fail_silently=True
                            )
                    except Exception:
                        pass
                
                messages.success(request, 'Archive updated successfully!')
                if archive.slug:
                    return redirect('archives:detail', slug=archive.slug)
                return redirect('archives:detail', pk=archive.pk)
        else:
            messages.error(request, 'Please check the form for errors.')
    else:
        # REMOVED: initial tag parsing logic
        form = ArchiveForm(instance=archive)
        formset = ArchiveItemFormSet(instance=archive)
    
    context = {
        'form': form,
        'formset': formset,
        'archive': archive,
        'categories': get_cached_categories(),
    }
    return render(request, 'archives/edit.html', context)


@login_required
def archive_delete(request, pk=None, slug=None):
    """Delete an archive."""
    if slug:
        archive = get_object_or_404(Archive, slug=slug, uploaded_by=request.user)
    elif pk:
        archive = get_object_or_404(Archive, pk=pk, uploaded_by=request.user)
    else:
        raise Http404("Archive not found")
    
    if archive.is_approved and not request.user.is_staff:
        messages.error(request, 'Approved archives cannot be deleted. Please contact an administrator.')
        if archive.slug:
            return redirect('archives:detail', slug=archive.slug)
        return redirect('archives:detail', pk=archive.pk)
    
    if request.method == 'POST':
        archive_title = archive.title
        archive.delete()
        cache.delete('all_approved_archive_ids')
        messages.success(request, f'Archive "{archive_title}" has been deleted.')
        return redirect('users:dashboard')
    
    return render(request, 'archives/delete.html', {'archive': archive})