"""
Django REST Framework Serializers for Igbo Archives API.
Provides serialization for Archive and BookRecommendation models.
"""
from rest_framework import serializers
from archives.models import Archive, Category
from books.models import BookRecommendation


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for archive categories."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['id', 'slug']


class ArchiveListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for archive listings."""
    category = serializers.StringRelatedField()
    uploaded_by = serializers.StringRelatedField()
    archive_type_display = serializers.CharField(source='get_archive_type_display', read_only=True)
    
    class Meta:
        model = Archive
        fields = [
            'id', 'title', 'slug', 'archive_type', 'archive_type_display',
            'category', 'uploaded_by', 'caption', 'circa_date', 'location',
            'image', 'created_at'
        ]
        read_only_fields = fields


class ArchiveDetailSerializer(serializers.ModelSerializer):
    """Full serializer for archive details."""
    category = CategorySerializer(read_only=True)
    uploaded_by = serializers.StringRelatedField()
    tags = serializers.StringRelatedField(many=True)
    archive_type_display = serializers.CharField(source='get_archive_type_display', read_only=True)
    
    class Meta:
        model = Archive
        fields = [
            'id', 'title', 'slug', 'archive_type', 'archive_type_display',
            'description', 'caption', 'alt_text', 'circa_date', 'location',
            'copyright_holder', 'original_url', 'original_identity_number',
            'category', 'uploaded_by', 'tags',
            'image', 'video', 'audio', 'document',
            'is_approved', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'uploaded_by', 'created_at', 'updated_at']


class ArchiveCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating archives via API."""
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Archive
        fields = [
            'title', 'archive_type', 'description', 'caption', 'alt_text',
            'circa_date', 'location', 'copyright_holder', 'original_url',
            'original_identity_number', 'category_id', 'tags',
            'image', 'video', 'audio', 'document'
        ]
    
    def create(self, validated_data):
        # Handle category
        category_id = validated_data.pop('category_id', None)
        tags_str = validated_data.pop('tags', '')
        
        archive = Archive.objects.create(**validated_data)
        
        if category_id:
            try:
                archive.category = Category.objects.get(id=category_id)
                archive.save()
            except Category.DoesNotExist:
                pass
        
        # Handle tags
        if tags_str:
            from taggit.models import Tag
            tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
            archive.tags.add(*tag_names)
        
        return archive


class BookRecommendationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for book listings."""
    added_by = serializers.StringRelatedField()
    avg_rating = serializers.FloatField(read_only=True)
    
    class Meta:
        model = BookRecommendation
        fields = [
            'id', 'book_title', 'author', 'slug', 'title',
            'added_by', 'cover_image', 'publication_year',
            'avg_rating', 'created_at'
        ]
        read_only_fields = fields


class BookRecommendationDetailSerializer(serializers.ModelSerializer):
    """Full serializer for book recommendation details."""
    added_by = serializers.StringRelatedField()
    tags = serializers.StringRelatedField(many=True)
    avg_rating = serializers.FloatField(read_only=True)
    num_ratings = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = BookRecommendation
        fields = [
            'id', 'book_title', 'author', 'slug', 'title',
            'added_by', 'publisher', 'publication_year', 'isbn',
            'cover_image', 'cover_image_back', 'alternate_cover',
            'content_json', 'tags',
            'avg_rating', 'num_ratings',
            'is_published', 'is_approved',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'added_by', 'created_at', 'updated_at']
