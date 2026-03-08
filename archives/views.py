"""
Archive views for browsing and managing cultural archives.
"""
import random  # Non-cryptographic use for content recommendations
import logging
import json
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
        if category.isdigit():
            archives = archives.filter(category__id=category)
        else:
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
            pass # Allow owner or staff to see the detail page even if unapproved
        else:
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

    ai_correlations = cache.get(f'archive_explore_further_{archive.id}')
    
    if not ai_correlations and archive.is_approved:
        from core.similarity import get_similar_items
        from books.models import BookRecommendation
        from lore.models import LorePost
        import json
        
        target_text = f"{archive.title} {archive.description} {archive.caption or ''}"
        
        books_qs = BookRecommendation.objects.filter(is_approved=True)
        recommended_books = get_similar_items(
            target_text, 
            books_qs, 
            limit=9, 
            text_field=lambda b: f"{b.book_title} {b.author} {b.title} {b.content_json}"
        )
        
        lores_qs = LorePost.objects.filter(is_approved=True)
        recommended_lores = get_similar_items(
            target_text, 
            lores_qs, 
            limit=9, 
            text_field=lambda l: f"{l.title} {l.excerpt} {l.content_json}"
        )
        
        if recommended_books or recommended_lores:
            # Combine books and lores into one mixed list
            combined_items = recommended_books + recommended_lores
            ai_correlations = {
                'intro': "Discover related books and stories to deepen your understanding.",
                'items': combined_items
            }
            # Cache for a relatively long time, e.g. 1 hour, so it's snappy but still updates automatically
            cache.set(f'archive_explore_further_{archive.id}', ai_correlations, timeout=3600)

    # Author profile lookup for bio/description if not linked via FK
    author_profile = archive.author
    if not author_profile and archive.original_author:
        author_profile = Author.objects.filter(name__iexact=archive.original_author).first()

    context = {
        'archive': archive,
        'archive_items': archive_items,
        'similar_archives': similar_archives,
        'previous_archive': previous_archive,
        'next_archive': next_archive,
        'recommended': recommended,
        'ai_correlations': ai_correlations,
        'author_profile': author_profile,
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
    
    from lore.models import LorePost
    from books.models import BookRecommendation
    
    lore_posts = LorePost.objects.filter(
        is_published=True,
        is_approved=True,
        original_author__iexact=author.name
    ).select_related('category', 'author').order_by('-created_at')
    
    recommended_books = BookRecommendation.objects.filter(
        is_published=True,
        is_approved=True,
        author__iexact=author.name
    ).select_related('added_by').order_by('-created_at')
    
    from .forms import AuthorDescriptionRequestForm
    desc_form = AuthorDescriptionRequestForm()
    
    context = {
        'author': author,
        'archives': page_obj,
        'lore_posts': lore_posts,
        'recommended_books': recommended_books,
        'desc_form': desc_form,
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
                    from core.notifications_utils import send_admin_notification
                    subject = f'New Archive Uploaded: {archive.title}'
                    message = (
                        f"A new archive has been submitted by {request.user.get_display_name()}.\n\n"
                        f"Title: {archive.title}\n"
                        f"Description: {archive.description[:200]}...\n"
                    )
                    send_admin_notification(subject, message, target_url="/users/admin/moderation/")
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
        archive = get_object_or_404(Archive, slug=slug)
    elif pk:
        archive = get_object_or_404(Archive, pk=pk)
    else:
        raise Http404("Archive not found")
    
    # Permission check: owner or staff
    if archive.uploaded_by != request.user and not request.user.is_staff:
        messages.error(request, "You do not have permission to edit this archive.")
        return redirect('archives:detail', slug=archive.slug if archive.slug else archive.pk)
    
    if request.method == 'POST':
        form = ArchiveForm(request.POST, instance=archive)
        formset = ArchiveItemFormSet(request.POST, request.FILES, instance=archive)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                archive = form.save(commit=False)
                
                old_title = form.initial.get('title', '')
                if archive.title != old_title or not archive.slug:
                    archive.slug = generate_unique_slug(archive.title, Archive, exclude_pk=archive.pk)
                
                archive.save()
                
                items = formset.save(commit=False)
                
                for obj in formset.deleted_objects:
                    obj.delete()
                
                for i, item in enumerate(items):
                    item.archive = archive
                    if not item.item_number:
                        from django.db.models import Max
                        max_num = archive.items.aggregate(Max('item_number'))['item_number__max'] or 0
                        item.item_number = max_num + 1
                    item.save()
                
                if archive.is_approved:
                    # Reset approval if edited
                    archive.is_approved = False
                    archive.save(update_fields=['is_approved'])
                    cache.delete('all_approved_archive_ids')
                    cache.delete('archive_categories')
                    
                    try:
                        from core.notifications_utils import send_admin_notification
                        send_admin_notification(
                            subject=f"Archive Updated (Review Needed): {archive.title}",
                            description=f"User {request.user.username} updated an archive. Please re-review.",
                            target_url="/users/admin/moderation/"
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
        archive = get_object_or_404(Archive, slug=slug)
    elif pk:
        archive = get_object_or_404(Archive, pk=pk)
    else:
        raise Http404("Archive not found")
    
    # Permission check: owner or staff
    if archive.uploaded_by != request.user and not request.user.is_staff:
        messages.error(request, "You do not have permission to delete this archive.")
        return redirect('archives:detail', slug=archive.slug if archive.slug else archive.pk)
    
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

# --- Community Notes Views ---

@login_required
def add_archive_note(request, slug):
    """Add a new community note to an archive."""
    archive = get_object_or_404(Archive, slug=slug, is_approved=True)
    
    if request.method == 'POST':
        from core.turnstile import verify_turnstile
        token = request.POST.get('cf-turnstile-response')
        turnstile_result = verify_turnstile(token)
        
        if not turnstile_result.get('success', False):
            messages.error(request, 'Security check failed. Please refresh and try again.')
            return redirect('archives:detail', slug=slug)
        content_json = request.POST.get('content_json')
        try:
            parsed_json = json.loads(content_json) if isinstance(content_json, str) else content_json
        except (ValueError, TypeError):
            parsed_json = {}

        from .models import ArchiveNote
        note = ArchiveNote.objects.create(
            archive=archive,
            added_by=request.user,
            content_json=parsed_json,
            is_approved=False  
        )
        
        # Notify the original uploader of the archive
        from core.notifications_utils import send_community_note_notification, send_admin_notification
        send_community_note_notification(note, archive)
        
        # Notify admins
        send_admin_notification(
            subject=f"New Community Note on {archive.title}",
            description=f"{request.user.get_display_name()} added a new community note to the archive '{archive.title}'.",
            target_url=archive.get_absolute_url()
        )
            
        messages.success(request, 'Your note has been submitted and is pending moderation.')
        
    return redirect('archives:detail', slug=slug)

@login_required
def suggest_note_edit(request, note_id):
    """Submit a suggestion to edit an existing note. Notifies the original note author."""
    from .models import ArchiveNote, ArchiveNoteSuggestion
    note = get_object_or_404(ArchiveNote, id=note_id)
    archive = note.archive
    
    if request.method == 'POST':
        suggestion_text = request.POST.get('content_json')
        try:
            parsed_json = json.loads(suggestion_text) if isinstance(suggestion_text, str) else suggestion_text
        except (ValueError, TypeError):
            parsed_json = {}

        suggestion = ArchiveNoteSuggestion.objects.create(
            note=note,
            suggested_by=request.user,
            suggestion_text=parsed_json
        )
        
        # Notify original note author via centralized notification system
        from core.notifications_utils import _send_notification_and_push
        _send_notification_and_push(
            recipient=note.added_by,
            sender=request.user,
            verb='suggested an edit to your Community Note',
            description=f'{request.user.get_display_name()} suggested a modification to your note on "{archive.title}". Check your dashboard.',
            target_object=note,
            push_head='Note Edit Suggestion',
            push_body=f'{request.user.get_display_name()} suggested an edit to your note.',
            push_url=archive.get_absolute_url()
        )
            
        messages.success(request, 'Your suggestion has been sent to the note author for review.')
        
    return redirect('archives:detail', slug=archive.slug)


@login_required
def edit_archive_note(request, pk):
    """Allow owners to edit their own community notes."""
    from .models import ArchiveNote
    note = get_object_or_404(ArchiveNote, pk=pk)
    
    if note.added_by != request.user and not request.user.is_staff:
        messages.error(request, "You can only edit your own notes.")
        return redirect('archives:detail', slug=note.archive.slug)
    
    if request.method == 'POST':
        content_json = request.POST.get('content_json')
        if content_json and content_json != '{}':
            try:
                note.content_json = json.loads(content_json) if isinstance(content_json, str) else content_json
                note.is_approved = False  # Re-moderation required
                note.save()
                messages.success(request, 'Your note has been updated and is pending re-moderation.')
            except (ValueError, TypeError):
                messages.error(request, 'Failed to save note content.')
        else:
            messages.error(request, 'Note content cannot be empty.')
            
    return redirect('archives:detail', slug=note.archive.slug)


@login_required
def submit_author_description(request, slug):
    """Handle submissions to add or edit an Author's description."""
    author = get_object_or_404(Author, slug=slug)
    
    if request.method == 'POST':
        from .forms import AuthorDescriptionRequestForm
        form = AuthorDescriptionRequestForm(request.POST, request.FILES)
        if form.is_valid():
            req = form.save(commit=False)
            req.author = author
            req.requested_by = request.user
            
            # Auto-approve if author has no existing description
            if not author.description:
                req.is_approved = True
                req.save()
                author.description = req.proposed_description
                if req.proposed_image:
                    # Properly copy the file to the author's upload path
                    author.image.save(req.proposed_image.name, req.proposed_image.file, save=False)
                author.save()
                messages.success(request, 'Thank you! Your description and photo have been automatically approved and updated.')
            else:
                req.save()
                # Notify admin via async task
                try:
                    from core.notifications_utils import send_admin_notification
                    send_admin_notification(
                        subject=f"Author Biography Edit Request: {author.name}",
                        description=f"User {request.user.username} has submitted an updated biography for {author.name}.\n\nReview it in the admin panel.",
                    )
                except Exception as e:
                    logger.error(f"Failed to send author desc notification: {e}")
                    
                messages.success(request, 'Your proposed biography edit has been submitted to moderators for review.')
                
    return redirect('archives:author_detail', slug=slug)

@login_required
def author_suggestions(request):
    """
    Returns a JSON list of matching authors for autocomplete in forms.
    """
    from django.http import JsonResponse
    from archives.models import Author, Archive
    from books.models import BookRecommendation
    from lore.models import LorePost
    
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'authors': []})
        
    authors = list(Author.objects.filter(name__icontains=query).order_by('name')[:10])
    
    # Collect existing names from other models to suggest legacy authors
    existing_names = {a.name.lower() for a in authors}
    
    books = BookRecommendation.objects.filter(author__icontains=query).values_list('author', flat=True).distinct()[:10]
    archives_qs = Archive.objects.filter(original_author__icontains=query).values_list('original_author', flat=True).distinct()[:10]
    lores = LorePost.objects.filter(original_author__icontains=query).values_list('original_author', flat=True).distinct()[:10]
    
    results = [{'name': a.name, 'description': a.description or ''} for a in authors]
    
    for name in list(books) + list(archives_qs) + list(lores):
        if name and name.lower() not in existing_names:
            results.append({'name': name, 'description': ''})
            existing_names.add(name.lower())
            
    # Keep it clean and limited to exactly 10
    results = sorted(results, key=lambda x: x['name'])[:10]
    return JsonResponse({'authors': results})
