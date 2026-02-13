import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Archive, ArchiveItem

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ArchiveItem)
@receiver(post_delete, sender=ArchiveItem)
def sync_archive_header(sender, instance, **kwargs):
    """
    Automatic Sync:
    Whenever an ArchiveItem is created, updated, or deleted:
    1. Update the Parent Archive's 'item_count'.
    2. Find the new 'Item #1' and copy its media to the Parent Archive.
    This ensures the website lists/cards always show the correct thumbnail
    and the data stays consistent even if edited via Admin.
    """
    try:
        archive = instance.archive
        update_parent_archive(archive)
    except Archive.DoesNotExist:
        # If the parent archive itself is being deleted, do nothing
        pass
    except Exception as e:
        logger.error(f"Failed to sync archive header for item {instance.pk}: {e}")

def update_parent_archive(archive):
    """Helper function to perform the sync."""
    try:
        # 1. Update Count
        current_count = archive.items.count()
        archive.item_count = current_count
        
        # 2. Get the first item (lowest item_number)
        first_item = archive.items.order_by('item_number').first()
        
        if first_item:
            # Copy metadata from Item 1
            archive.archive_type = first_item.item_type
            
            # We only auto-update the parent caption if it's currently empty
            if not archive.caption:
                archive.caption = first_item.caption
                
            # Reset all media fields on the parent to clean state
            archive.image = None
            archive.video = None
            archive.audio = None
            archive.document = None
            
            # Copy the specific file from Item 1 to the Parent
            if first_item.item_type == 'image':
                archive.image = first_item.image
            elif first_item.item_type == 'video':
                archive.video = first_item.video
            elif first_item.item_type == 'audio':
                archive.audio = first_item.audio
            elif first_item.item_type == 'document':
                archive.document = first_item.document
                
            # Save specific fields to avoid recursion
            archive.save(update_fields=[
                'item_count', 'archive_type', 'image', 'video', 
                'audio', 'document', 'caption'
            ])
        
        else:
            # If NO items exist (e.g. user deleted the last item)
            archive.image = None
            archive.video = None
            archive.audio = None
            archive.document = None
            archive.save(update_fields=['item_count', 'image', 'video', 'audio', 'document'])
    except Exception as e:
        logger.error(f"Failed to update parent archive {archive.pk}: {e}")