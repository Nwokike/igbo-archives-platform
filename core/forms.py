from django import forms
from django.core.exceptions import ValidationError
from threadedcomments.forms import ThreadedCommentForm
from django.conf import settings
from .turnstile import verify_turnstile


class TurnstileCommentForm(ThreadedCommentForm):
    """Comment form with Cloudflare Turnstile for ALL users."""
    
    # Hidden field to receive the Turnstile token
    cf_turnstile_response = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        # Extract request from kwargs if passed
        self.request = kwargs.pop('request', None)
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
        cleaned_data = super().clean()
        
        # Get Turnstile token from form data
        token = cleaned_data.get('cf_turnstile_response') or self.data.get('cf-turnstile-response', '')
        
        # Get client IP
        remote_ip = None
        if self.request:
            remote_ip = self.request.META.get('HTTP_CF_CONNECTING_IP') or \
                       self.request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
                       self.request.META.get('REMOTE_ADDR')
        
        # Verify with Cloudflare
        result = verify_turnstile(token, remote_ip)
        if not result.get('success'):
            raise ValidationError('Please complete the verification challenge.')
        
        return cleaned_data


class ContactForm(forms.Form):
    """Contact form with proper validation, honeypot protection, and Turnstile."""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your email address'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 6,
            'placeholder': 'Your message'
        })
    )
    # Honeypot field - should remain empty
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'hidden',
            'style': 'display: none;',
            'autocomplete': 'off',
            'tabindex': '-1'
        })
    )
    # Hidden field for Turnstile token
    cf_turnstile_response = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
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
    
    def clean(self):
        """Validate Turnstile token"""
        cleaned_data = super().clean()
        
        # Get Turnstile token from form data
        token = cleaned_data.get('cf_turnstile_response') or self.data.get('cf-turnstile-response', '')
        
        # Get client IP
        remote_ip = None
        if self.request:
            remote_ip = self.request.META.get('HTTP_CF_CONNECTING_IP') or \
                       self.request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
                       self.request.META.get('REMOTE_ADDR')
        
        # Verify with Cloudflare
        result = verify_turnstile(token, remote_ip)
        if not result.get('success'):
            raise ValidationError('Please complete the security verification.')
        
        return cleaned_data
