from rest_framework import serializers
from django.contrib.auth import get_user_model
from archives.models import Archive, ArchiveItem, Category, Author
from books.models import BookRecommendation, UserBookRating
from insights.models import InsightPost

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'get_display_name', 'profile_picture', 'bio']
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
            'category', 'author', 'original_author', 'uploaded_by',
            'items',  # Added items here
            'views_count', 'is_featured', 'created_at', 'updated_at'
        ]

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
    class Meta:
        model = Archive
        fields = [
            'title', 'archive_type', 'category_id',
            'description', 'caption', 'alt_text',
            'circa_date', 'date_created', 'location',
            'copyright_holder', 'original_url', 'original_identity_number',
            'original_author',
            'image', 'video', 'audio', 'document', 'featured_image',
            'item_count'
        ]

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
            # 1. Create the Parent Archive
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

class BookRecommendationSerializer(serializers.ModelSerializer):
    added_by = UserSerializer(read_only=True)
    
    class Meta:
        model = BookRecommendation
        fields = [
            'id', 'book_title', 'author', 'slug',
            'title', 'cover_image', 'publication_year',
            'added_by', 'average_rating', 'rating_count', 'created_at'
        ]

class InsightPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = InsightPost
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt',
            'featured_image', 'author', 'views_count',
            'created_at'
        ]