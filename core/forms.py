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
    """Custom threaded comment form with reCAPTCHA for guest comments"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field only if keys are configured (same as signup/login)
        if RECAPTCHA_ENABLED:
            self.fields['captcha'] = ReCaptchaField(widget=ReCaptchaV2Checkbox())
        
        # Style the existing fields
        self.fields['name'].widget.attrs.update({'class': 'modern-input', 'placeholder': 'Your name *'})
        self.fields['name'].label = 'Name'
        self.fields['email'].widget.attrs.update({'class': 'modern-input', 'placeholder': 'Email (optional)'})
        self.fields['email'].label = 'Email'
        self.fields['email'].required = False
        self.fields['comment'].widget.attrs.update({'class': 'modern-comment-input', 'rows': 3, 'placeholder': 'Share your thoughts...'})
        self.fields['comment'].label = 'Comment'
