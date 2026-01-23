"""
Forms for Archive create and edit.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Archive, Category


class ArchiveForm(forms.ModelForm):
    """Form for creating and editing Archive entries."""
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'mask, ceremony, traditional'
        }),
        help_text='Comma-separated tags (max 20)'
    )
    
    date_created = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input'
        })
    )
    
    class Meta:
        model = Archive
        fields = [
            'title', 'description', 'archive_type', 'category',
            'caption', 'alt_text', 'original_author', 'location',
            'date_created', 'circa_date', 'image', 'video', 'audio',
            'document', 'featured_image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 5,
                'placeholder': 'Detailed description of the archive (plain text)'
            }),
            'archive_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'caption': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Photo by Northcote Thomas, 1910. Public Domain'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Describe the image for accessibility'
            }),
            'original_author': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Northcote Thomas'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Onitsha, Anambra State'
            }),
            'circa_date': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., c1910, around 1910s'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.jpg,.jpeg,.png,.webp'
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.mp4,.webm,.ogg,.mov'
            }),
            'audio': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.mp3,.wav,.ogg,.m4a'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.pdf,.doc,.docx,.txt'
            }),
            'featured_image': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.jpg,.jpeg,.png,.webp'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = 'Select category...'
        
        # Make archive_type required
        self.fields['archive_type'].empty_label = 'Select type...'
        
        # Conditionally require caption and alt_text for images
        if self.instance and self.instance.pk:
            if self.instance.archive_type == 'image':
                self.fields['caption'].required = True
                self.fields['alt_text'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        archive_type = cleaned_data.get('archive_type')
        
        # Validate that exactly one primary media file is provided based on archive_type
        image = cleaned_data.get('image') or (self.instance.image if self.instance.pk else None)
        video = cleaned_data.get('video') or (self.instance.video if self.instance.pk else None)
        audio = cleaned_data.get('audio') or (self.instance.audio if self.instance.pk else None)
        document = cleaned_data.get('document') or (self.instance.document if self.instance.pk else None)
        
        if archive_type == 'image':
            if not image and not self.instance.pk:
                raise ValidationError('Image file is required for image-type archives.')
            if not cleaned_data.get('caption'):
                raise ValidationError('Caption is required for images.')
            if not cleaned_data.get('alt_text'):
                raise ValidationError('Alt text is required for images.')
        elif archive_type == 'video':
            if not video and not self.instance.pk:
                raise ValidationError('Video file is required for video-type archives.')
        elif archive_type == 'audio':
            if not audio and not self.instance.pk:
                raise ValidationError('Audio file is required for audio-type archives.')
        elif archive_type == 'document':
            if not document and not self.instance.pk:
                raise ValidationError('Document file is required for document-type archives.')
        
        return cleaned_data
    
    def clean_tags(self):
        tags_str = self.cleaned_data.get('tags', '')
        if tags_str:
            tag_list = [t.strip()[:50] for t in tags_str.split(',') if t.strip()][:20]
            return tag_list
        return []
    
    def save(self, commit=True):
        archive = super().save(commit=False)
        if commit:
            archive.save()
            # Handle tags
            tags = self.cleaned_data.get('tags', [])
            if tags:
                archive.tags.clear()
                archive.tags.add(*tags)
        return archive
