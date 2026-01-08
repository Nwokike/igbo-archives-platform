from django import forms
from django.core.exceptions import ValidationError
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
    
    # Add CAPTCHA field (not required - will validate based on user authentication)
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
    
    def clean_captcha(self):
        """Validate CAPTCHA only for anonymous users"""

        
        # If user is authenticated (has user attribute and is logged in), skip CAPTCHA validation
        if hasattr(self, 'user') and self.user and self.user.is_authenticated:
            return None
        
        # For anonymous users, CAPTCHA is required
        captcha_value = self.cleaned_data.get('captcha')
        if not captcha_value:
            raise ValidationError('Please complete the CAPTCHA verification.')
        
        return captcha_value


class ContactForm(forms.Form):
    """Contact form with proper validation and honeypot protection."""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message'
        })
    )
    # Honeypot field - should remain empty
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'hidden',
            'autocomplete': 'off',
            'tabindex': '-1'
        })
    )
    
    def clean_website(self):
        """Honeypot validation - reject if filled"""
        website = self.cleaned_data.get('website', '')
        if website:
            raise ValidationError('Spam detected.')
        return website
    
    def clean_message(self):
        """Basic content validation"""
        message = self.cleaned_data.get('message', '')
        if len(message) < 10:
            raise ValidationError('Message is too short.')
        return message
