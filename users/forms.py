from allauth.account.forms import SignupForm, LoginForm
from django import forms
from django.conf import settings
from .models import CustomUser
import re

# Only import reCAPTCHA if keys are configured
if getattr(settings, 'RECAPTCHA_PUBLIC_KEY', '') and getattr(settings, 'RECAPTCHA_PRIVATE_KEY', ''):
    from django_recaptcha.fields import ReCaptchaField
    from django_recaptcha.widgets import ReCaptchaV2Checkbox
    RECAPTCHA_ENABLED = True
else:
    RECAPTCHA_ENABLED = False


class CustomSignupForm(SignupForm):
    full_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    accept_terms = forms.BooleanField(
        required=True,
        label='I agree to the Terms of Service and Privacy Policy',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']
        
        # Add reCAPTCHA field only if keys are configured
        if RECAPTCHA_ENABLED:
            self.fields['captcha'] = ReCaptchaField(widget=ReCaptchaV2Checkbox())
        
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    
    def save(self, request):
        email = self.cleaned_data['email']
        username = re.sub(r'[^a-zA-Z0-9]', '', email.split('@')[0])[:30]
        
        from users.models import CustomUser
        counter = 1
        original_username = username
        while CustomUser.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        self.cleaned_data['username'] = username
        
        user = super().save(request)
        user.full_name = self.cleaned_data.get('full_name', '')
        user.save()
        
        return user


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add reCAPTCHA field only if keys are configured
        if RECAPTCHA_ENABLED:
            self.fields['captcha'] = ReCaptchaField(widget=ReCaptchaV2Checkbox())
        
        self.fields['login'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
        self.fields['login'].label = 'Email'
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })


class ProfileEditForm(forms.ModelForm):
    twitter = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://twitter.com/username'
    }))
    facebook = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://facebook.com/username'
    }))
    linkedin = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://linkedin.com/in/username'
    }))
    instagram = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://instagram.com/username'
    }))
    youtube = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://youtube.com/@username'
    }))
    academia = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://academia.edu/username'
    }))
    researchgate = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://researchgate.net/profile/username'
    }))
    orcid = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://orcid.org/0000-0000-0000-0000'
    }))
    website = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://yourwebsite.com'
    }))
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'bio', 'profile_picture']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.social_links:
            self.fields['twitter'].initial = self.instance.social_links.get('twitter', '')
            self.fields['facebook'].initial = self.instance.social_links.get('facebook', '')
            self.fields['linkedin'].initial = self.instance.social_links.get('linkedin', '')
            self.fields['instagram'].initial = self.instance.social_links.get('instagram', '')
            self.fields['youtube'].initial = self.instance.social_links.get('youtube', '')
            self.fields['academia'].initial = self.instance.social_links.get('academia', '')
            self.fields['researchgate'].initial = self.instance.social_links.get('researchgate', '')
            self.fields['orcid'].initial = self.instance.social_links.get('orcid', '')
            self.fields['website'].initial = self.instance.social_links.get('website', '')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        social_links = {
            'twitter': self.cleaned_data.get('twitter', ''),
            'facebook': self.cleaned_data.get('facebook', ''),
            'linkedin': self.cleaned_data.get('linkedin', ''),
            'instagram': self.cleaned_data.get('instagram', ''),
            'youtube': self.cleaned_data.get('youtube', ''),
            'academia': self.cleaned_data.get('academia', ''),
            'researchgate': self.cleaned_data.get('researchgate', ''),
            'orcid': self.cleaned_data.get('orcid', ''),
            'website': self.cleaned_data.get('website', ''),
        }
        user.social_links = {k: v for k, v in social_links.items() if v}
        if commit:
            user.save()
        return user
