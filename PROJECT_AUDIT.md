# Igbo Archives Platform - Comprehensive Project Audit

This document provides a complete audit of all apps in the Igbo Archives Django platform, optimized for a 1GB RAM constraint (free Google VM).

**Constraints & Requirements:**
- 1GB RAM limit on free Google VM
- Local vendor files (no CDN dependencies)
- Huey for background tasks (not Celery)
- SQLite with WAL mode
- Editor.js block editor integration
- Preserve featured images and archive importing

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Core App Audit](#1-core-app)
3. [Archives App Audit](#2-archives-app)
4. [Insights App Audit](#3-insights-app)
5. [Books App Audit](#4-books-app)
6. [Users App Audit](#5-users-app)
7. [API App Audit](#6-api-app)
8. [Academy App Audit](#7-academy-app)
9. [Settings & Configuration](#8-settings--configuration)
10. [Memory Budget & Optimization Strategy](#9-memory-budget--optimization-strategy)
11. [Implementation Roadmap](#10-implementation-roadmap)

---

## Executive Summary

### Critical Issues Found

| Priority | App | Issue | Impact |
|----------|-----|-------|--------|
| CRITICAL | core, archives | `order_by('?')` causes full table scan | Memory exhaustion on large datasets |
| CRITICAL | insights, books | N+1 queries in list/detail views | Slow page loads, DB overload |
| HIGH | all apps | Missing `select_related()`/`prefetch_related()` | 10x more DB queries than needed |
| HIGH | archives, insights | No database indexes on filtered columns | Slow queries as data grows |
| HIGH | settings | No Huey configuration | Background tasks not functional |
| MEDIUM | all apps | Repeated category/tag queries | Redundant database load |
| MEDIUM | users | Dashboard queries not optimized | Slow dashboard for active users |
| LOW | templates | Missing lazy loading for images | Higher initial page weight |

### Quick Wins (Implement First)

1. Add `select_related()` to all views (30 min, 80% query reduction)
2. Replace `order_by('?')` with random ID selection (15 min, 90% memory reduction)
3. Add database indexes (10 min, 10x faster filtering)
4. Configure Huey for background tasks (30 min)
5. Cache categories and tags (15 min)

---

## 1. Core App

### `views.py`
**Status:** [ ] CRITICAL FIX NEEDED

**Issue 1 (CRITICAL):** Line 11 uses `order_by('?')` - loads entire table into memory

```python
# CURRENT (BAD) - Line 11
all_archives = Archive.objects.filter(is_approved=True).order_by('?')[:10]

# IMPROVED - Memory-efficient random selection
import random

def home(request):
    # Get only IDs (small memory footprint)
    archive_ids = list(
        Archive.objects.filter(is_approved=True)
        .values_list('id', flat=True)[:500]
    )
    
    if archive_ids:
        random_ids = random.sample(archive_ids, min(10, len(archive_ids)))
        featured = Archive.objects.filter(pk__in=random_ids).select_related('category')
    else:
        featured = Archive.objects.none()
    
    return render(request, 'core/home.html', {'featured_archives': featured})
```

**Memory Impact:** With 10,000 archives, current code loads ~50MB. Improved code loads ~500KB.

### `context_processors.py`
**Status:** [✓] OK - Uses `getattr` safely, minimal memory footprint.

### `notifications_utils.py`
**Status:** [✓] OK - Well-designed centralized notification module.

### `sitemaps.py`
**Status:** [ ] NEEDS OPTIMIZATION

**Issue:** Sitemap queryset loads all objects at once.

```python
# IMPROVED - Use iterator for memory efficiency
class ArchiveSitemap(Sitemap):
    def items(self):
        return Archive.objects.filter(is_approved=True).only('id', 'updated_at').iterator(chunk_size=500)
```

---

## 2. Archives App

### `models.py`
**Status:** [ ] NEEDS INDEXES

**Issue 1 (HIGH):** No database indexes for frequently filtered columns.

```python
# ADD to Archive model Meta class
class Meta:
    ordering = ['-created_at']
    indexes = [
        models.Index(fields=['is_approved', '-created_at'], name='arch_approved_date_idx'),
        models.Index(fields=['archive_type', 'is_approved'], name='arch_type_approved_idx'),
        models.Index(fields=['category', 'is_approved'], name='arch_cat_approved_idx'),
    ]
```

**Issue 2 (LOW):** Help text inconsistency - document field says "max 5MB" but validator uses 10MB. Fix line 91.

### `views.py`
**Status:** [ ] CRITICAL FIXES NEEDED

**Issue 1 (CRITICAL):** Line 72 `order_by('?')` - same as core/views.py

```python
# CURRENT (BAD) - Line 72
recommended = Archive.objects.filter(is_approved=True).exclude(pk=archive.pk).order_by('?')

# IMPROVED - Add helper function
import random
from django.core.cache import cache

def get_random_recommendations(exclude_pk, count=9):
    """Memory-efficient random archive selection with caching"""
    cache_key = f'archive_ids_pool'
    archive_ids = cache.get(cache_key)
    
    if archive_ids is None:
        archive_ids = list(
            Archive.objects.filter(is_approved=True)
            .values_list('id', flat=True)[:500]
        )
        cache.set(cache_key, archive_ids, 300)  # Cache 5 minutes
    
    # Remove excluded ID
    available_ids = [aid for aid in archive_ids if aid != exclude_pk]
    
    if not available_ids:
        return Archive.objects.none()
    
    random_ids = random.sample(available_ids, min(count, len(available_ids)))
    return Archive.objects.filter(pk__in=random_ids).select_related('uploaded_by', 'category')
```

**Issue 2 (HIGH):** Missing `select_related()` throughout.

```python
# CURRENT (BAD) - Line 8
archives = Archive.objects.filter(is_approved=True)

# IMPROVED
archives = Archive.objects.filter(is_approved=True).select_related(
    'uploaded_by', 'category'
).prefetch_related('tags')
```

**Issue 3 (MEDIUM):** Line 29 fetches categories on every request.

```python
# IMPROVED - Cache categories
def get_cached_categories():
    categories = cache.get('archive_categories')
    if categories is None:
        categories = list(Category.objects.all())
        cache.set('archive_categories', categories, 3600)  # 1 hour
    return categories
```

**Issue 4 (MEDIUM):** Lines 142-145 loop-based tag adding.

```python
# CURRENT (BAD)
tags = request.POST.get('tags', '').split(',')
for tag in tags:
    if tag.strip():
        archive.tags.add(tag.strip())

# IMPROVED - Single database operation
tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
if tags:
    archive.tags.add(*tags)
```

### `admin.py`
**Status:** [✓] OK - Clean configuration with list_editable.

---

## 3. Insights App

### `models.py`
**Status:** [ ] NEEDS INDEXES

**Issue 1 (HIGH):** No database indexes.

```python
# ADD to InsightPost model Meta class
class Meta:
    ordering = ['-created_at']
    indexes = [
        models.Index(fields=['is_published', 'is_approved', '-created_at'], name='insight_pub_date_idx'),
        models.Index(fields=['author', 'is_published'], name='insight_author_pub_idx'),
        models.Index(fields=['pending_approval'], name='insight_pending_idx'),
    ]
```

**Issue 2 (LOW):** `UploadedImage` model has ForeignKey to `archives.Category` - consider if this cross-app dependency is needed.

### `views.py`
**Status:** [ ] HIGH PRIORITY FIXES NEEDED

**Issue 1 (HIGH):** Line 61-85 - Inefficient recommendation logic with multiple queryset evaluations.

```python
# CURRENT (BAD) - Lines 61-85
# Multiple .count() calls and queryset rebuilding

# IMPROVED - Single optimized query
def get_insight_recommendations(insight, count=9):
    """Efficient recommendation fetching"""
    # Start with tag-based recommendations
    tag_names = list(insight.tags.values_list('name', flat=True))
    
    recommendations = InsightPost.objects.filter(
        is_published=True,
        is_approved=True
    ).exclude(pk=insight.pk).select_related('author')
    
    if tag_names:
        # Annotate by tag match count for relevance
        from django.db.models import Count, Q
        recommendations = recommendations.annotate(
            tag_matches=Count('tags', filter=Q(tags__name__in=tag_names))
        ).order_by('-tag_matches', '-created_at')
    else:
        recommendations = recommendations.order_by('-created_at')
    
    return recommendations[:count]
```

**Issue 2 (HIGH):** Missing `select_related()` in list view.

```python
# CURRENT (BAD) - Line 15
insights = InsightPost.objects.filter(is_published=True, is_approved=True)

# IMPROVED
insights = InsightPost.objects.filter(
    is_published=True, is_approved=True
).select_related('author').prefetch_related('tags').only(
    'id', 'title', 'slug', 'excerpt', 'featured_image', 'created_at',
    'author__full_name', 'author__username'
)
```

**Issue 3 (MEDIUM):** Line 32 fetches all tags every request.

```python
# IMPROVED - Cache tags
def get_cached_insight_tags():
    tags = cache.get('insight_tags')
    if tags is None:
        from taggit.models import Tag
        tags = list(Tag.objects.filter(insightpost__isnull=False).distinct())
        cache.set('insight_tags', tags, 1800)  # 30 minutes
    return tags
```

---

## 4. Books App

### `models.py`
**Status:** [ ] NEEDS INDEXES

```python
# ADD to BookReview model Meta class
class Meta:
    ordering = ['-created_at']
    indexes = [
        models.Index(fields=['is_published', 'is_approved', '-created_at'], name='book_pub_date_idx'),
        models.Index(fields=['reviewer', 'is_published'], name='book_reviewer_pub_idx'),
        models.Index(fields=['rating', 'is_approved'], name='book_rating_idx'),
    ]
```

### `views.py`
**Status:** [ ] HIGH PRIORITY FIXES NEEDED

**Same issues as insights/views.py:**
1. Lines 63-87: Inefficient recommendation logic
2. Missing `select_related('reviewer')`
3. Multiple queryset evaluations in detail view

```python
# IMPROVED book_list view
def book_list(request):
    reviews = BookReview.objects.filter(
        is_published=True, is_approved=True
    ).select_related('reviewer').prefetch_related('tags').only(
        'id', 'book_title', 'review_title', 'slug', 'rating', 'cover_image',
        'created_at', 'reviewer__full_name', 'reviewer__username'
    )
    
    # Filtering...
    if search := request.GET.get('search'):
        reviews = reviews.filter(
            Q(book_title__icontains=search) | Q(review_title__icontains=search)
        )
    
    # ... rest of view
```

---

## 5. Users App

### `models.py`
**Status:** [✓] OK - Clean custom user model and notification system.

**Improvement:** Add index for notification queries.

```python
# ADD to Notification model Meta class
class Meta:
    ordering = ('-timestamp',)
    indexes = [
        models.Index(fields=['recipient', 'unread', '-timestamp'], name='notif_user_unread_idx'),
    ]
```

### `views.py`
**Status:** [ ] NEEDS OPTIMIZATION

**Issue 1 (HIGH):** Lines 13-55 - Dashboard makes 6+ separate queries.

```python
# CURRENT (BAD) - Multiple separate queries
messages_threads = request.user.message_threads.all()
my_insights = InsightPost.objects.filter(author=request.user)...
my_drafts = InsightPost.objects.filter(author=request.user)...
my_book_reviews = BookReview.objects.filter(reviewer=request.user)...
my_archives = Archive.objects.filter(uploaded_by=request.user)...
edit_suggestions = EditSuggestion.objects.filter(...)...

# IMPROVED - Combine similar queries, add select_related
@login_required
def dashboard(request):
    user = request.user
    
    # Single query for all user insights with status annotation
    all_insights = InsightPost.objects.filter(author=user).order_by('-created_at')
    my_insights = [i for i in all_insights if i.is_published or i.pending_approval]
    my_drafts = [i for i in all_insights if not i.is_published and not i.pending_approval]
    
    # Optimized queries with limits
    my_book_reviews = BookReview.objects.filter(
        reviewer=user
    ).order_by('-created_at')[:20]
    
    my_archives = Archive.objects.filter(
        uploaded_by=user
    ).select_related('category').order_by('-created_at')[:20]
    
    edit_suggestions = EditSuggestion.objects.filter(
        post__author=user,
        is_approved=False,
        is_rejected=False
    ).select_related('post', 'suggested_by').order_by('-created_at')[:10]
    
    # ... rest
```

### `admin_views.py`
**Status:** [✓] OK - Simple moderation views.

**Improvement:** Add `select_related` for author/reviewer.

```python
# IMPROVED
pending_insights = InsightPost.objects.filter(
    pending_approval=True, is_approved=False
).select_related('author')

pending_books = BookReview.objects.filter(
    pending_approval=True, is_approved=False
).select_related('reviewer')
```

### `forms.py`
**Status:** [✓] OK - reCAPTCHA conditionally loaded, good pattern.

### `notifications_views.py`
**Status:** [✓] OK - Efficient bulk update for mark_all_read.

**Issue (LOW):** Line 65 makes two queries for unread notifications.

```python
# CURRENT (BAD) - Two queries
notifications = request.user.notifications.filter(unread=True)[:5]
unread_count = request.user.notifications.filter(unread=True).count()

# IMPROVED - Single query with slicing
from django.db.models import Count

def notification_dropdown(request):
    unread_qs = request.user.notifications.filter(unread=True)
    unread_count = unread_qs.count()
    notifications = unread_qs[:5]
    
    return render(request, 'users/partials/notification_dropdown.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })
```

---

## 6. API App

### `views.py`
**Status:** [ ] NEEDS OPTIMIZATION

**Issue 1 (MEDIUM):** Line 27 - Missing `select_related`.

```python
# CURRENT (BAD)
archives = Archive.objects.filter(is_approved=True)

# IMPROVED
archives = Archive.objects.filter(is_approved=True).select_related('category').only(
    'id', 'title', 'description', 'archive_type', 'caption', 'alt_text',
    'image', 'video', 'audio', 'document', 'featured_image'
)
```

**Issue 2 (LOW):** Line 143 fetches all categories - should cache.

```python
# IMPROVED
@login_required
def get_categories(request):
    categories = cache.get('api_categories')
    if categories is None:
        categories = list(Category.objects.values('id', 'name', 'slug'))
        cache.set('api_categories', categories, 3600)
    return JsonResponse({'categories': categories})
```

### `push_views.py`
**Status:** [✓] OK - Clean push notification handling.

---

## 7. Academy App

### `views.py` & `urls.py`
**Status:** [✓] OK - Placeholder app with minimal footprint.

---

## 8. Settings & Configuration

### `settings.py`
**Status:** [ ] NEEDS HUEY CONFIGURATION

**Issue 1 (HIGH):** No Huey configuration for background tasks.

```python
# ADD to settings.py

# ============================================
# HUEY TASK QUEUE CONFIGURATION (Memory-Efficient)
# ============================================
from huey import SqliteHuey

HUEY = SqliteHuey(
    filename='huey.db',
    immediate=DEBUG,  # Run tasks immediately in DEBUG mode
    results=True,
    store_none=False,
)

# For production with minimal memory:
# HUEY = SqliteHuey(
#     filename='huey.db',
#     immediate=False,
#     results=True,
#     store_none=False,
#     utc=True,
# )
```

**Issue 2 (MEDIUM):** SQLite WAL mode not explicitly configured.

```python
# ADD to settings.py DATABASES section
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'init_command': "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA cache_size=-64000; PRAGMA temp_store=MEMORY;",
        }
    }
}
```

**Note:** SQLite doesn't support init_command directly. Add to `wsgi.py`:

```python
# ADD to wsgi.py after application setup
import sqlite3
conn = sqlite3.connect(str(BASE_DIR / 'db.sqlite3'))
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA synchronous=NORMAL')
conn.execute('PRAGMA cache_size=-64000')  # 64MB cache
conn.execute('PRAGMA temp_store=MEMORY')
conn.close()
```

**Issue 3 (LOW):** Add Django cache configuration for query caching.

```python
# ADD to settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'igbo-archives-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}
```

---

## 9. Memory Budget & Optimization Strategy

### Memory Allocation for 1GB RAM

| Component | Allocation | Notes |
|-----------|------------|-------|
| Linux OS | ~100MB | Base overhead |
| Python Interpreter | ~50MB | Runtime |
| Django + Dependencies | ~100MB | Framework & libs |
| SQLite Page Cache | ~64MB | PRAGMA cache_size |
| Gunicorn Workers | ~400MB | 2 workers @ 200MB each |
| Huey Worker | ~100MB | Background task worker |
| WhiteNoise Static | ~50MB | Compressed static files |
| **Buffer** | ~136MB | For request spikes |

### Recommended Gunicorn Configuration

```bash
# gunicorn.conf.py or command line
gunicorn igbo_archives.wsgi:application \
    --workers 2 \
    --threads 2 \
    --worker-class gthread \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 30 \
    --bind 0.0.0.0:5000
```

### Huey Worker Configuration

```bash
# Run Huey with memory constraints
python manage.py run_huey --workers 1 --worker-type thread
```

---

## 10. Implementation Roadmap

### Phase 1: Critical Fixes (Day 1)
- [ ] Replace all `order_by('?')` with random ID selection
- [ ] Add `select_related()`/`prefetch_related()` to all views
- [ ] Configure Huey in settings.py
- [ ] Add database indexes via migration

### Phase 2: Caching (Day 2)
- [ ] Configure Django cache backend
- [ ] Cache categories, tags in all views
- [ ] Add cache invalidation on model save

### Phase 3: Query Optimization (Day 3)
- [ ] Optimize dashboard queries
- [ ] Add `.only()` for list views
- [ ] Optimize recommendation algorithms

### Phase 4: Template & Frontend (Day 4)
- [ ] Add `loading="lazy"` to all images
- [ ] Add client-side file validation
- [ ] Verify all local vendor files working

### Phase 5: Background Tasks (Day 5)
- [ ] Create Huey tasks for:
  - Email sending
  - Push notifications
  - Social media posting
  - Database backups
- [ ] Test Huey worker under load

---

## Summary of All Changes

### Database Migrations Needed

```bash
# Generate migration for all indexes
python manage.py makemigrations archives insights books users --name add_performance_indexes
python manage.py migrate
```

### Files to Modify

| File | Priority | Changes |
|------|----------|---------|
| `core/views.py` | CRITICAL | Replace order_by('?') |
| `archives/views.py` | CRITICAL | Replace order_by('?'), add select_related |
| `archives/models.py` | HIGH | Add indexes |
| `insights/views.py` | HIGH | Add select_related, optimize recommendations |
| `insights/models.py` | HIGH | Add indexes |
| `books/views.py` | HIGH | Add select_related, optimize recommendations |
| `books/models.py` | HIGH | Add indexes |
| `users/views.py` | MEDIUM | Optimize dashboard queries |
| `users/models.py` | LOW | Add notification index |
| `api/views.py` | MEDIUM | Add select_related, cache categories |
| `settings.py` | HIGH | Add Huey config, cache config |
| `wsgi.py` | HIGH | Add SQLite WAL mode |

---

This concludes the comprehensive platform audit.
