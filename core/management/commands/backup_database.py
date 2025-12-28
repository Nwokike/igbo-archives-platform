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
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            if not options['media_only']:
                self.stdout.write(self.style.WARNING(f'[{timestamp}] Starting database backup...'))
                call_command('dbbackup', clean=options['clean'])
                self.stdout.write(self.style.SUCCESS(f'[{timestamp}] Database backup completed successfully!'))
            
            if not options['database_only']:
                self.stdout.write(self.style.WARNING(f'[{timestamp}] Starting media backup...'))
                call_command('mediabackup', clean=options['clean'])
                self.stdout.write(self.style.SUCCESS(f'[{timestamp}] Media backup completed successfully!'))
            
            self.stdout.write(self.style.SUCCESS('\n=== Backup Summary ==='))
            self.stdout.write(self.style.SUCCESS(f'Timestamp: {timestamp}'))
            self.stdout.write(self.style.SUCCESS(f'Database: {"✓" if not options["media_only"] else "✗"}'))
            self.stdout.write(self.style.SUCCESS(f'Media: {"✓" if not options["database_only"] else "✗"}'))
            self.stdout.write(self.style.SUCCESS(f'Cleanup: {"✓" if options["clean"] else "✗"}'))
            
        except Exception as e:
            logger.error(f'Backup failed: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Backup failed: {str(e)}'))
            raise
