import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'igbo_archives.settings')
django.setup()

from archives.models import Archive, Author
from django.db.models import Count

def migrate():
    print("Starting Author migration...")
    
    # Find unique author names that appear in archives
    existing_authors = Archive.objects.exclude(original_author='').values('original_author').annotate(c=Count('id'))
    
    migrated_count = 0
    linked_count = 0
    
    for item in existing_authors:
        name = item['original_author'].strip()
        if not name:
            continue
            
        # Get or create the Author profile
        author_obj, created = Author.objects.get_or_create(name=name)
        if created:
            print(f"Created profile for: {name}")
            migrated_count += 1
        
        # Link existing archives to this profile (case insensitive)
        # Note: Archive.save() logic will also handle this for future edits,
        # but here we do a bulk update or iterative update for existing ones.
        archives_to_link = Archive.objects.filter(original_author__iexact=name, author__isnull=True)
        count = archives_to_link.count()
        if count > 0:
            # We iterate to trigger save() or just bulk update
            # Bulk update is faster
            archives_to_link.update(author=author_obj)
            linked_count += count
            print(f"Linked {count} archives to {name}")

    print(f"Migration complete. Profiles created: {migrated_count}, Archives linked: {linked_count}")

if __name__ == "__main__":
    migrate()
