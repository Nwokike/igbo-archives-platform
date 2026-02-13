"""
Management command to clean up old TTS audio files.
TTS files are generated to MEDIA_ROOT/tts/ and accumulate indefinitely — this command removes stale ones.

Usage:
    python manage.py cleanup_tts_files           # Remove files older than 24 hours
    python manage.py cleanup_tts_files --hours 48 # Remove files older than 48 hours
    python manage.py cleanup_tts_files --dry-run  # Preview what would be deleted
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Clean up old TTS audio files from MEDIA_ROOT/tts/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Max age in hours (default: 24)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview deletions without actually deleting',
        )

    def handle(self, *args, **options):
        import time
        from ai.services.tts_service import tts_service

        max_age_hours = options['hours']
        dry_run = options['dry_run']
        output_dir = tts_service.output_dir

        if not output_dir.exists():
            self.stdout.write('TTS output directory does not exist. Nothing to clean.')
            return

        now = time.time()
        max_age_seconds = max_age_hours * 3600
        count = 0

        for filepath in output_dir.glob('*.*'):
            if filepath.suffix in ('.mp3', '.wav') and now - filepath.stat().st_mtime > max_age_seconds:
                count += 1
                if dry_run:
                    self.stdout.write(f'  Would delete: {filepath.name}')
                else:
                    filepath.unlink()
                    self.stdout.write(f'  Deleted: {filepath.name}')

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\nDry run: {count} file(s) would be deleted.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nCleaned up {count} old TTS file(s).'))
