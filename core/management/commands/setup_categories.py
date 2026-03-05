from django.core.management.base import BaseCommand
from django.utils.text import slugify
from archives.models import Category

class Command(BaseCommand):
    help = 'Setup default categories for Archives and Lore'

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

        # 2. Lore Categories
        lore_cats = [
            'Architectural Lore',
            'Artistic Lore',
            'Contemporary Issues',
            'Cultural Lore',
            'Fashion Lore',
            'Historical Lore',
            'Personality Profiles',
            'Proverbs and Sayings',
            'Others',
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

        self.stdout.write("\nSetting up Lore Categories...")
        for name in lore_cats:
            slug = slugify(name)
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'type': 'lore'}
            )
            if not created and cat.type != 'lore':
                cat.type = 'lore'
                cat.save()
                self.stdout.write(f"Updated {name} to Lore type")
            elif created:
                self.stdout.write(f"Created {name}")

        self.stdout.write(self.style.SUCCESS('Successfully setup categories'))
