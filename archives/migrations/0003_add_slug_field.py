# Generated migration for adding slug field to Archive model

from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    """Populate slugs for existing archives from their titles."""
    Archive = apps.get_model('archives', 'Archive')
    for archive in Archive.objects.all():
        if not archive.slug and archive.title:
            base_slug = slugify(archive.title)[:255]
            slug = base_slug
            counter = 1
            while Archive.objects.filter(slug=slug).exclude(pk=archive.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                if counter > 100:
                    import uuid
                    slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                    break
            archive.slug = slug
            archive.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0002_alter_archive_audio_alter_archive_document_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='archive',
            name='slug',
            field=models.SlugField(blank=True, help_text='URL-friendly version of title', max_length=255, null=True, unique=True),
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
    ]
