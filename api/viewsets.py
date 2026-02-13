"""
Django REST Framework ViewSets for Igbo Archives API.
Provides RESTful API endpoints for Archive and BookRecommendation models.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import Q, Avg, Count

from archives.models import Archive, Category
from books.models import BookRecommendation, UserBookRating
from .serializers import (
    CategorySerializer,
    ArchiveListSerializer, ArchiveSerializer, ArchiveCreateSerializer,
    BookRecommendationListSerializer, BookRecommendationSerializer, BookRecommendationCreateSerializer,
    UserBookRatingSerializer, UserBookRatingCreateSerializer
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission: read-only for unauthenticated, write for owner."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Handle different model ownership fields
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
        if hasattr(obj, 'added_by'):
            return obj.added_by == request.user
        return False


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for archive categories.
    GET /api/v1/categories/ - List all categories
    GET /api/v1/categories/{slug}/ - Category detail
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'


class ArchiveViewSet(viewsets.ModelViewSet):
    """
    API endpoint for archives.
    
    GET /api/v1/archives/ - List approved archives
    GET /api/v1/archives/{slug}/ - Archive detail
    POST /api/v1/archives/ - Create archive (auth required)
    PUT/PATCH /api/v1/archives/{slug}/ - Update archive (owner only)
    DELETE /api/v1/archives/{slug}/ - Delete archive (owner only)
    """
    # authentication_classes inherited from DEFAULT_AUTHENTICATION_CLASSES in settings
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Filter archives based on authentication and query params."""
        queryset = Archive.objects.filter(is_approved=True)
        
        # Filter by type
        archive_type = self.request.query_params.get('type')
        if archive_type:
            queryset = queryset.filter(archive_type=archive_type)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(caption__icontains=search)
            )
        
        queryset = queryset.select_related('category', 'uploaded_by')
        
        # Only add prefetch_related for detail/retrieve (list doesn't need items/tags)
        if self.action in ('retrieve', 'update', 'partial_update'):
            queryset = queryset.prefetch_related('tags', 'items')
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArchiveListSerializer
        if self.action == 'create':
            return ArchiveCreateSerializer
        return ArchiveSerializer
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured archives — cached random selection (avoids ORDER BY RANDOM)."""
        cache_key = 'api_featured_archives'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        
        import random
        image_ids = list(
            Archive.objects.filter(is_approved=True, archive_type='image')
            .values_list('id', flat=True)
        )
        selected_ids = random.sample(image_ids, min(10, len(image_ids))) if image_ids else []
        featured = Archive.objects.filter(id__in=selected_ids).select_related('category', 'uploaded_by')
        serializer = ArchiveListSerializer(featured, many=True)
        cache.set(cache_key, serializer.data, 600)  # Cache for 10 minutes
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get most recent archives."""
        recent = self.get_queryset().order_by('-created_at')[:20]
        serializer = ArchiveListSerializer(recent, many=True)
        return Response(serializer.data)


class BookRecommendationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for book recommendations.
    
    GET /api/v1/books/ - List approved books
    GET /api/v1/books/{slug}/ - Book detail
    POST /api/v1/books/ - Create book recommendation (auth required)
    PUT/PATCH /api/v1/books/{slug}/ - Update book (owner only)
    DELETE /api/v1/books/{slug}/ - Delete book (owner only)
    
    Special endpoints:
    GET /api/v1/books/top_rated/ - Top rated books
    POST /api/v1/books/{slug}/rate/ - Rate a book (auth required)
    GET /api/v1/books/{slug}/ratings/ - Get book ratings
    """
    # authentication_classes inherited from DEFAULT_AUTHENTICATION_CLASSES in settings
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = BookRecommendation.objects.filter(
            is_published=True, is_approved=True
        ).annotate(
            avg_rating=Avg('ratings__rating'),
            num_ratings=Count('ratings')
        )
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(book_title__icontains=search) |
                Q(author__icontains=search) |
                Q(title__icontains=search)
            )
        
        return queryset.select_related('added_by')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BookRecommendationListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return BookRecommendationCreateSerializer
        return BookRecommendationSerializer
    
    def perform_create(self, serializer):
        """Create with pending approval status."""
        serializer.save(
            added_by=self.request.user,
            is_published=False,
            is_approved=False,
            pending_approval=True
        )
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get top-rated books (minimum 3 ratings to qualify)."""
        top = self.get_queryset().filter(
            num_ratings__gte=3
        ).order_by('-avg_rating')[:10]
        serializer = BookRecommendationListSerializer(top, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rate(self, request, slug=None):
        """Rate a book (create or update rating)."""
        book = self.get_object()
        serializer = UserBookRatingCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            rating, created = UserBookRating.objects.update_or_create(
                book=book,
                user=request.user,
                defaults=serializer.validated_data
            )
            response_serializer = UserBookRatingSerializer(rating)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(response_serializer.data, status=status_code)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def ratings(self, request, slug=None):
        """Get all ratings for a book."""
        book = self.get_object()
        ratings = book.ratings.select_related('user').order_by('-created_at')
        serializer = UserBookRatingSerializer(ratings, many=True)
        return Response(serializer.data)