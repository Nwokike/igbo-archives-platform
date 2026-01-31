from django.core.management.base import BaseCommand
from django.utils.text import slugify
from archives.models import Category

class Command(BaseCommand):
    help = 'Setup default categories for Archives and Insights'

    def handle(self, *args, **kwargs):
        # 1. Archive Categories
        archive_cats = [
            'Alusi/Arushi',
            'Architecture',
            'Artifacts',
            'Arts',
            'Daily Life',
            'Dibia',
            'Fashion',
            'Festivals',
            'Historical Events',
            'Masks',
            'Masquerades',
            'Portraits',
        ]

        # 2. Insight Categories
        insight_cats = [
            'Architectural Insights',
            'Artistic Insights',
            'Contemporary Issues',
            'Cultural Insights',
            'Fashion Insights',
            'Historical Insights',
            'Personality Profiles',
        ]

        self.stdout.write("Setting up Archive Categories...")
        for name in archive_cats:
            slug = slugify(name)
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'type': 'archive'}
            )
            if not created and cat.type != 'archive':
                cat.type = 'archive'
                cat.save()
                self.stdout.write(f"Updated {name} to Archive type")
            elif created:
                self.stdout.write(f"Created {name}")

        self.stdout.write("\nSetting up Insight Categories...")
        for name in insight_cats:
            slug = slugify(name)
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'type': 'insight'}
            )
            if not created and cat.type != 'insight':
                cat.type = 'insight'
                cat.save()
                self.stdout.write(f"Updated {name} to Insight type")
            elif created:
                self.stdout.write(f"Created {name}")

        self.stdout.write(self.style.SUCCESS('Successfully setup categories'))