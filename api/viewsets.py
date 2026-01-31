"""
Django REST Framework ViewSets for Igbo Archives API.
Provides RESTful API endpoints for Archive and BookRecommendation models.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.db.models import Q, Avg, Count

from archives.models import Archive, Category
from books.models import BookRecommendation
from .serializers import (
    CategorySerializer,
    ArchiveListSerializer, ArchiveSerializer, ArchiveCreateSerializer,
    BookRecommendationSerializer
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
    GET /api/v1/categories/{id}/ - Category detail
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
    authentication_classes = [TokenAuthentication, SessionAuthentication]
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
        
        return queryset.select_related('category', 'uploaded_by').prefetch_related('tags', 'items')
    
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
        """Get featured archives (random selection of images)."""
        featured = self.get_queryset().filter(archive_type='image').order_by('?')[:10]
        serializer = ArchiveListSerializer(featured, many=True)
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
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = 'slug'
    serializer_class = BookRecommendationSerializer
    
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
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get top-rated books."""
        top = self.get_queryset().order_by('-average_rating')[:10]
        serializer = self.get_serializer(top, many=True)
        return Response(serializer.data)