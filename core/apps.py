from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        # Override threadedcomments to use our custom CAPTCHA form
        import threadedcomments
        from django.utils.module_loading import import_string
        from django.conf import settings
        
        def get_custom_form():
            """Return the custom comment form defined in settings.COMMENT_FORM"""
            form_path = getattr(settings, 'COMMENT_FORM', 'threadedcomments.forms.ThreadedCommentForm')
            return import_string(form_path)
        
        threadedcomments.get_form = get_custom_form
