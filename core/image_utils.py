"""
Image compression utilities for automatic size reduction on upload.
Compresses large images to reduce storage and improve load times.
"""
import io
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile


def compress_image(image_file, max_size_mb=1.5, quality=85, max_dimension=2400):
    """
    Compress an image file to reduce size.
    
    Args:
        image_file: Django UploadedFile or file-like object
        max_size_mb: Target maximum size in MB (default 1.5MB)
        quality: JPEG quality 1-100 (default 85)
        max_dimension: Max width or height (default 2400px)
    
    Returns:
        InMemoryUploadedFile: Compressed image or original if already small
    """
    if not image_file:
        return image_file
    
    max_size_bytes = max_size_mb * 1024 * 1024
    
    # Check if compression is needed
    if hasattr(image_file, 'size') and image_file.size <= max_size_bytes:
        return image_file
    
    try:
        # Open image
        img = Image.open(image_file)
        
        # Convert RGBA to RGB for JPEG compatibility
        if img.mode in ('RGBA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if len(img.split()) == 4 else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large
        width, height = img.size
        if width > max_dimension or height > max_dimension:
            ratio = min(max_dimension / width, max_dimension / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Compress with iterative quality reduction
        output = io.BytesIO()
        current_quality = quality
        
        while current_quality >= 50:
            output.seek(0)
            output.truncate()
            img.save(output, format='JPEG', quality=current_quality, optimize=True)
            
            if output.tell() <= max_size_bytes:
                break
            current_quality -= 10
        
        output.seek(0)
        
        # Get original filename, ensure .jpg extension
        original_name = getattr(image_file, 'name', 'image.jpg')
        if not original_name.lower().endswith(('.jpg', '.jpeg')):
            name_parts = original_name.rsplit('.', 1)
            original_name = name_parts[0] + '.jpg'
        
        return InMemoryUploadedFile(
            file=output,
            field_name=getattr(image_file, 'field_name', 'image'),
            name=original_name,
            content_type='image/jpeg',
            size=output.tell(),
            charset=None
        )
        
    except Exception as e:
        # Return original on any error
        import logging
        logging.getLogger(__name__).warning(f"Image compression failed: {e}")
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        return image_file


def compress_model_images(instance, *field_names, max_size_mb=1.5):
    """
    Compress multiple image fields on a model instance.
    Call this in the model's save() method before super().save().
    
    Usage:
        def save(self, *args, **kwargs):
            compress_model_images(self, 'image', 'featured_image', max_size_mb=1.5)
            super().save(*args, **kwargs)
    """
    for field_name in field_names:
        field = getattr(instance, field_name, None)
        if field and hasattr(field, 'file'):
            try:
                # Only compress if it's a new upload (not saved yet)
                if hasattr(field.file, 'seek'):
                    field.file.seek(0, 2)  # Seek to end
                    size = field.file.tell()
                    field.file.seek(0)
                    
                    if size > max_size_mb * 1024 * 1024:
                        compressed = compress_image(field.file, max_size_mb=max_size_mb)
                        if compressed and compressed != field.file:
                            setattr(instance, field_name, compressed)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Image compression skipped for field '{field_name}': {e}")
