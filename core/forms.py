from django import forms
from django_comments.forms import CommentForm
from django.conf import settings

# Only import reCAPTCHA if keys are configured
if getattr(settings, 'RECAPTCHA_PUBLIC_KEY', '') and getattr(settings, 'RECAPTCHA_PRIVATE_KEY', ''):
    from django_recaptcha.fields import ReCaptchaField
    from django_recaptcha.widgets import ReCaptchaV2Checkbox
    RECAPTCHA_ENABLED = True
else:
    RECAPTCHA_ENABLED = False


class CaptchaCommentForm(CommentForm):
    """Custom comment form with reCAPTCHA for guest comments"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field only if keys are configured
        if RECAPTCHA_ENABLED:
            self.fields['captcha'] = ReCaptchaField(
                widget=ReCaptchaV2Checkbox(),
                label='Verify you are human'
            )
        
        # Style the existing fields
        self.fields['name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Your name'})
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'your@email.com'})
        self.fields['comment'].widget.attrs.update({'class': 'form-control', 'rows': 4, 'placeholder': 'Enter your comment...'})
