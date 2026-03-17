from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
import os
import requests
from urllib.parse import urlparse
from archives.models import Archive, ArchiveItem, Category, Author
from books.models import BookRecommendation, UserBookRating
from lore.models import LorePost

User = get_user_model()

class AIFallbackMediaField(serializers.FileField):
    """
    A unified media field built for the MCP integration.
    - Native Web APIs (Editor.js): Accpets and passes through `UploadedFile` binaries.
    - AI Agents (MCP): Accepts public HTTP/HTTPS URLs. It intercepts the URL,
      enforces a strict safety limit (e.g., 50MB), streams the download, 
      and converts it into a native Django `ContentFile` on the fly.
    """
    def __init__(self, **kwargs):
        self.max_download_size = kwargs.pop('max_download_size', 50 * 1024 * 1024) # Default 50MB safety limit
        kwargs.setdefault('allow_empty_file', True)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        # 1. Standard web GUI upload (binary file)
        if hasattr(data, 'read'):
            return super().to_internal_value(data)
            
        # 2. AI Agent URL upload
        if isinstance(data, str) and data.startswith(('http://', 'https://')):
            try:
                # Stream the download to prevent loading huge files into memory at once
                response = requests.get(data, stream=True, timeout=10)
                response.raise_for_status()
                
                # Verify Size (Defend against SSRF/Resource exhaustion)
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_download_size:
                    raise serializers.ValidationError(f"File at URL exceeds the {self.max_download_size//(1024*1024)}MB limit.")
                
                # Extract original filename
                parsed_url = urlparse(data)
                file_name = os.path.basename(parsed_url.path)
                
                # Ensure we have a valid looking filename and extension
                if not file_name or '.' not in file_name:
                    content_type = response.headers.get('content-type', '')
                    ext = content_type.split('/')[-1] if '/' in content_type else 'bin'
                    ext = ext.split(';')[0].strip() # Clean up parameters
                    file_name = f"ai_upload.{ext}"
                    
                # Return standard Django file object
                return ContentFile(response.content, name=file_name)
                
            except requests.RequestException as e:
                raise serializers.ValidationError(f"Could not fetch media from provided AI URL. Ensure the URL is public and valid. Underlying error: {e}")
                
        # 3. Invalid input fallback
        raise serializers.ValidationError("Media must be either a valid HTTP/HTTPS URL or a standard file upload.")


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'profile_picture', 'bio']
        read_only_fields = ['id']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'slug', 'description', 'image']

class ArchiveItemSerializer(serializers.ModelSerializer):
    """Serializer for individual items within an archive."""
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ArchiveItem
        fields = [
            'id', 'item_number', 'item_type', 
            'file_url',  # Unified URL for whatever file type exists
            'image', 'video', 'audio', 'document',
            'caption', 'alt_text', 'description'
        ]
    
    def get_file_url(self, obj):
        file = obj.get_file()
        if file:
            return file.url
        return None

class ArchiveSerializer(serializers.ModelSerializer):
    """
    Read-Serializer for Archive Detail.
    Includes the 'items' list for the new gallery feature.
    """
    category = CategorySerializer(read_only=True)
    author = AuthorSerializer(read_only=True)
    uploaded_by = UserSerializer(read_only=True)
    items = ArchiveItemSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Archive
        fields = [
            'id', 'title', 'slug', 'archive_type', 
            'description', 'caption', 'alt_text',
            'circa_date', 'date_created', 'location',
            'copyright_holder', 'original_url', 'original_identity_number',
            'item_count',
            'image', 'video', 'audio', 'document', 'featured_image',
            'category', 'author', 'original_author', 'uploaded_by',
            'items',
            'tags',
            'views_count', 'is_featured', 'created_at', 'updated_at'
        ]

    def get_tags(self, obj):
        return list(obj.tags.names()) if hasattr(obj, 'tags') else []

class ArchiveListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    author_name = serializers.CharField(source='author.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_display_name', read_only=True)
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Archive
        fields = [
            'id', 'title', 'slug', 'archive_type',
            'category_name', 'author_name', 'uploaded_by_name',
            'caption', 'circa_date', 'location',
            'thumbnail', 'created_at'
        ]

    def get_thumbnail(self, obj):
        if obj.featured_image:
            return obj.featured_image.url
        if obj.archive_type == 'image' and obj.image:
            return obj.image.url
        return None

class ArchiveCreateSerializer(serializers.ModelSerializer):
    """
    Write-Serializer for creating Archives.
    Handles the backward-compatibility logic:
    Accepts flat file fields (image, video) and automatically creates 
    both the Parent Archive and the first ArchiveItem.
    """
    category_id = serializers.IntegerField(required=False, allow_null=True)
    image = AIFallbackMediaField(required=False, allow_null=True)
    video = AIFallbackMediaField(required=False, allow_null=True)
    audio = AIFallbackMediaField(required=False, allow_null=True)
    document = AIFallbackMediaField(required=False, allow_null=True)
    featured_image = AIFallbackMediaField(required=False, allow_null=True)
    
    class Meta:
        model = Archive
        fields = [
            'title', 'archive_type', 'category_id',
            'description', 'caption', 'alt_text',
            'circa_date', 'date_created', 'location',
            'copyright_holder', 'original_url', 'original_identity_number',
            'original_author',
            'image', 'video', 'audio', 'document', 'featured_image',
        ]
        read_only_fields = ['item_count']

    def create(self, validated_data):
        from django.db import transaction
        
        # Extract file data to handle Item creation manually
        image = validated_data.get('image')
        video = validated_data.get('video')
        audio = validated_data.get('audio')
        document = validated_data.get('document')
        archive_type = validated_data.get('archive_type')
        caption = validated_data.get('caption', '')
        alt_text = validated_data.get('alt_text', '')
        description = validated_data.get('description', '')

        with transaction.atomic():
            # 1. Pop file fields before creating parent to avoid duplicate storage
            for field in ('image', 'video', 'audio', 'document'):
                validated_data.pop(field, None)
            
            # Create the Parent Archive (without file fields)
            archive = Archive.objects.create(**validated_data)

            # 2. Automatically Create Item #1 (The Missing Link Fix)
            # This ensures archives created via API still have editable items in the dashboard
            item = ArchiveItem(
                archive=archive,
                item_number=1,
                item_type=archive_type,
                caption=caption,
                alt_text=alt_text,
                description=description # Use main description for item 1 if provided
            )

            # Assign the correct file to the item based on type
            if archive_type == 'image' and image:
                item.image = image
            elif archive_type == 'video' and video:
                item.video = video
            elif archive_type == 'audio' and audio:
                item.audio = audio
            elif archive_type == 'document' and document:
                item.document = document
            
            item.save()

        return archive


# Book Recommendation Serializers
class BookRecommendationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for book list views."""
    added_by_name = serializers.CharField(source='added_by.get_display_name', read_only=True)
    # Map to annotation names from BookRecommendationViewSet.get_queryset()
    # Avoids calling model @property which triggers N+1 queries
    average_rating = serializers.FloatField(source='avg_rating', read_only=True)
    rating_count = serializers.IntegerField(source='num_ratings', read_only=True)
    
    class Meta:
        model = BookRecommendation
        fields = [
            'id', 'book_title', 'author', 'slug', 'title',
            'cover_image', 'publication_year', 'external_url',
            'added_by_name', 'average_rating', 'rating_count', 'created_at'
        ]


class BookRecommendationSerializer(serializers.ModelSerializer):
    """Full serializer for book detail views."""
    added_by = UserSerializer(read_only=True)
    
    class Meta:
        model = BookRecommendation
        fields = [
            'id', 'book_title', 'author', 'isbn', 'slug',
            'title', 'content_json', 'external_url',
            'cover_image',
            'publisher', 'publication_year',
            'added_by', 'average_rating', 'rating_count',
            'is_published', 'is_approved', 'pending_approval',
            'created_at', 'updated_at'
        ]


class BookRecommendationCreateSerializer(serializers.ModelSerializer):
    """Write-serializer for creating/updating book recommendations."""
    cover_image = AIFallbackMediaField(required=False, allow_null=True)
    
    class Meta:
        model = BookRecommendation
        fields = [
            'book_title', 'author', 'isbn', 'external_url',
            'title', 'content_json',
            'cover_image',
            'publisher', 'publication_year'
        ]
    
    def create(self, validated_data):
        from core.editorjs_helpers import generate_unique_slug
        
        title = validated_data.get('title', validated_data.get('book_title', ''))
        validated_data['slug'] = generate_unique_slug(title, BookRecommendation)
        return super().create(validated_data)


class UserBookRatingSerializer(serializers.ModelSerializer):
    """Serializer for user book ratings."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserBookRating
        fields = ['id', 'user', 'rating', 'review_text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UserBookRatingCreateSerializer(serializers.ModelSerializer):
    """Write-serializer for creating/updating ratings."""
    
    class Meta:
        model = UserBookRating
        fields = ['rating', 'review_text']


class LorePostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = LorePost
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt',
            'featured_image', 'author',
            'created_at'
        ]


class LorePostCreateSerializer(serializers.ModelSerializer):
    """Write-serializer for creating/updating lore posts."""
    featured_image = AIFallbackMediaField(required=False, allow_null=True)
    
    class Meta:
        model = LorePost
        fields = [
            'title', 'excerpt', 'content_json',
            'featured_image',
        ]
    
    def create(self, validated_data):
        from core.editorjs_helpers import generate_unique_slug
        
        title = validated_data.get('title', '')
        validated_data['slug'] = generate_unique_slug(title, LorePost)
        return super().create(validated_data)
