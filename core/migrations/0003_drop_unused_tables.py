from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_digestqueue_content_type'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
                DROP TABLE IF EXISTS "insights_editsuggestion";
                DROP TABLE IF EXISTS "insights_uploadedimage";
                DROP TABLE IF EXISTS "insights_insightpost";
                DROP TABLE IF EXISTS "taggit_taggeditem";
                DROP TABLE IF EXISTS "taggit_tag";
                
                DELETE FROM "django_migrations" WHERE "app" IN ('insights', 'taggit');
            ''',
            reverse_sql='''
                -- No reverse mapping for dropped tables
            '''
        ),
    ]
