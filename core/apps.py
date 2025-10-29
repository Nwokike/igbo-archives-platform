from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        # Simple fix: Force django_comments to use our custom form
        import django_comments
        from core.forms import CaptchaThreadedCommentForm
        django_comments.get_form = lambda: CaptchaThreadedCommentForm
