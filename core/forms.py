from django import forms
from threadedcomments.forms import ThreadedCommentForm
from django.conf import settings

# Only import reCAPTCHA if keys are configured
if getattr(settings, 'RECAPTCHA_PUBLIC_KEY', '') and getattr(settings, 'RECAPTCHA_PRIVATE_KEY', ''):
    from django_recaptcha.fields import ReCaptchaField
    from django_recaptcha.widgets import ReCaptchaV2Checkbox
    RECAPTCHA_ENABLED = True
else:
    RECAPTCHA_ENABLED = False


class CaptchaThreadedCommentForm(ThreadedCommentForm):
    """Custom threaded comment form with reCAPTCHA for anonymous users only"""
    
    # Add CAPTCHA as class field for anonymous users
    if RECAPTCHA_ENABLED:
        captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox(), required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Style the existing fields
        self.fields['name'].widget.attrs.update({'class': 'modern-input', 'placeholder': 'Your name *'})
        self.fields['name'].label = 'Name'
        self.fields['email'].widget.attrs.update({'class': 'modern-input', 'placeholder': 'Email (optional)'})
        self.fields['email'].label = 'Email'
        self.fields['email'].required = False
        self.fields['comment'].widget.attrs.update({'class': 'modern-comment-input', 'rows': 3, 'placeholder': 'Share your thoughts...'})
        self.fields['comment'].label = 'Comment'
    
    def clean(self):
        """Only require CAPTCHA for anonymous users"""
        from django.core.exceptions import ValidationError
        cleaned_data = super().clean()
        
        # Check if user is authenticated by looking at the user_name field
        # If user_name is empty, user is logged in (name comes from user object)
        # If user_name has value, user is anonymous (filling out the form)
        if RECAPTCHA_ENABLED and cleaned_data.get('name'):
            # Anonymous user - require CAPTCHA
            if 'captcha' in self.fields and not cleaned_data.get('captcha'):
                raise ValidationError('Please complete the CAPTCHA verification.')
        
        return cleaned_data
