from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Archive, ArchiveItem

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

def update_parent_archive(archive):
    """Helper function to perform the sync."""
    # 1. Update Count
    # We count the actual items in the database to ensure accuracy
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
        # We clear the parent media so it doesn't show a broken link
        archive.image = None
        archive.video = None
        archive.audio = None
        archive.document = None
        archive.save(update_fields=['item_count', 'image', 'video', 'audio', 'document'])