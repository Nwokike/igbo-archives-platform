from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from insights.models import InsightPost

class Command(BaseCommand):
    help = 'Delete draft posts older than 30 days'
    
    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=30)
        old_drafts = InsightPost.objects.filter(
            is_published=False,
            created_at__lt=cutoff_date
        )
        count = old_drafts.count()
        old_drafts.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} old draft(s)'))
