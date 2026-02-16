import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.tasks import (
    daily_database_backup, 
    cleanup_old_notifications, 
    cleanup_old_messages, 
    send_weekly_digest
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs scheduled tasks based on the current time (intended for use with Cron)'

    def handle(self, *args, **options):
        now = timezone.now()
        hour = now.hour
        day = now.day
        
        self.stdout.write(f"Checking scheduled tasks for hour: {hour}, day: {day}")

        # 03:00 AM - Daily backup
        if hour == 3:
            self.stdout.write("Triggering daily_database_backup...")
            daily_database_backup.enqueue()

        # 04:00 AM - Monthly Notification Cleanup (1st of month)
        if hour == 4 and day == 1:
            self.stdout.write("Triggering cleanup_old_notifications...")
            cleanup_old_notifications.enqueue()

        # 04:30 AM - Monthly Message Cleanup (1st of month)
        # Since we only check by hour here, we might need more precision or just run them together at 4 AM
        if hour == 4 and day == 1:
            self.stdout.write("Triggering cleanup_old_messages...")
            cleanup_old_messages.enqueue()

        # 06:00 AM - Weekly Digest (Runs daily to handle batching)
        if hour == 6:
            self.stdout.write("Triggering send_weekly_digest batch...")
            send_weekly_digest.enqueue()

        self.stdout.write("Task check complete.")
