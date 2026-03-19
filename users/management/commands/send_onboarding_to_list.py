"""
One-time management command to send onboarding emails to former WordPress subscribers.
Usage: python manage.py send_onboarding_to_list email1 email2 ...
       python manage.py send_onboarding_to_list --from-email onyeka@igboarchives.com.ng email1
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Send onboarding emails to a list of email addresses (creates placeholder accounts if needed).'

    def add_arguments(self, parser):
        parser.add_argument('emails', nargs='+', type=str, help='Email addresses to send to')
        parser.add_argument('--dry-run', action='store_true', help='Preview without sending')
        parser.add_argument('--from-email', type=str, default=None, help='Override the FROM email address')

    def handle(self, *args, **options):
        from users.utils import send_claim_profile_email

        emails = options['emails']
        dry_run = options['dry_run']
        from_email = options['from_email']
        sent = 0
        skipped = 0

        if from_email:
            self.stdout.write(f"  Using FROM: {from_email}")

        for email in emails:
            email = email.strip().lower()
            if not email:
                continue

            # Find or create a placeholder user
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                username = email.split('@')[0].replace('.', '_').replace('+', '_')
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    is_active=True,
                )
                user.set_unusable_password()
                user.save()
                self.stdout.write(f"  Created placeholder account: {username} ({email})")

            if dry_run:
                self.stdout.write(self.style.WARNING(f"  [DRY RUN] Would send to: {email}"))
                continue

            try:
                name = user.full_name.split()[0] if user.full_name else None
                result = send_claim_profile_email(user, name=name, mode='onboarding', from_email=from_email)
                if result:
                    sent += 1
                    self.stdout.write(self.style.SUCCESS(f"  Sent to: {email}"))
                else:
                    skipped += 1
                    self.stdout.write(self.style.ERROR(f"  Failed: {email}"))
            except Exception as e:
                skipped += 1
                self.stdout.write(self.style.ERROR(f"  Error for {email}: {e}"))

        self.stdout.write(f"\nDone. Sent: {sent}, Skipped/Failed: {skipped}")
