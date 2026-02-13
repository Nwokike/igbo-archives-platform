"""
Management command for database backups using django-dbbackup
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backup database and media files using django-dbbackup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database-only',
            action='store_true',
            help='Backup database only (skip media files)',
        )
        parser.add_argument(
            '--media-only',
            action='store_true',
            help='Backup media files only (skip database)',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean old backups after creating new ones',
        )

    def handle(self, *args, **options):
        # Compatibility patch for django-dbbackup with Django 5.1+
        import django.core.files.storage
        if not hasattr(django.core.files.storage, 'get_storage_class'):
            from django.utils.module_loading import import_string
            from django.conf import settings
            
            def get_storage_class(import_path=None, _cache={}):
                # If no path provided, use DBBACKUP_STORAGE or fallback to default
                if import_path is None:
                    import_path = getattr(settings, 'DBBACKUP_STORAGE', None)
                if not import_path:
                    if hasattr(settings, 'STORAGES'):
                        import_path = settings.STORAGES.get('default', {}).get('BACKEND')
                    else:
                        import_path = getattr(settings, 'DEFAULT_FILE_STORAGE', None)
                
                # Return cached version if available
                if import_path in _cache:
                    return _cache[import_path]
                
                cls = import_string(import_path)
                
                # Inject options for S3 storage
                if 'S3' in cls.__name__:
                    # Use direct backup options if available, else standard STORAGES
                    conf = getattr(settings, 'DBBACKUP_STORAGE_OPTIONS', {})
                    if not conf and hasattr(settings, 'STORAGES'):
                        conf = settings.STORAGES.get('dbbackup', {}).get('OPTIONS', {})
                    
                    class PatchedStorage(cls):
                        def __init__(self, *args, **kwargs):
                            # kwarg settings take precedence over default backup settings
                            merged = {**conf, **kwargs}
                            super().__init__(**merged)
                    _cache[import_path] = PatchedStorage
                    return PatchedStorage
                _cache[import_path] = cls
                return cls
                
            django.core.files.storage.get_storage_class = get_storage_class
            logger.info("Applied backup compatibility patch for Django 5.1+")

        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # We skip media backup entirely since live media is already in R2.
            # This avoids creating massive redundant archives.
            if options['media_only']:
                self.stdout.write(self.style.ERROR('Media backup is disabled (Redundant on R2 setup).'))
                return

            self.stdout.write(self.style.WARNING(f'[{timestamp}] Starting database backup to R2...'))
            call_command('dbbackup', clean=options['clean'])
            self.stdout.write(self.style.SUCCESS(f'[{timestamp}] Database backup completed successfully!'))
            
            self.stdout.write(self.style.SUCCESS('\n=== Backup Summary ==='))
            self.stdout.write(self.style.SUCCESS(f'Timestamp: {timestamp}'))
            self.stdout.write(self.style.SUCCESS(f'Database: YES'))
            self.stdout.write(self.style.SUCCESS(f'Media: SKIPPED (Redundant)'))
            self.stdout.write(self.style.SUCCESS(f'Cleanup: {"YES" if options["clean"] else "NO"}'))
            
        except Exception as e:
            logger.error(f'Backup failed: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Backup failed: {str(e)}'))
            raise
