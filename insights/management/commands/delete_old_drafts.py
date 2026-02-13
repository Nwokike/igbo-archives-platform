from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from insights.models import InsightPost


class Command(BaseCommand):
    help = 'Delete draft posts older than 30 days (excludes pending approval and rejected posts under revision)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=30)
        old_drafts = InsightPost.objects.filter(
            is_published=False,
            pending_approval=False,  # Don't delete posts waiting for admin review
            is_rejected=False,       # Don't delete rejected posts (may be under revision)
            created_at__lt=cutoff_date
        )
        count = old_drafts.count()
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would delete {count} old draft(s):'))
            for draft in old_drafts[:20]:
                self.stdout.write(f'  - "{draft.title}" by {draft.author} (created {draft.created_at.date()})')
            if count > 20:
                self.stdout.write(f'  ... and {count - 20} more')
        else:
            old_drafts.delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {count} old draft(s)'))
