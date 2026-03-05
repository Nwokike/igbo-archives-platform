from django import forms
from .models import LorePost
from archives.models import Category

class LorePostForm(forms.ModelForm):
    """
    Form for creating and editing Lore properties.
    Note: Editor.js content is handled via a hidden input 'content_json' processed in the view.
    """
    original_author_about = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 3,
            'placeholder': 'Provide a brief biography or description for the Original Author.'
        })
    )

    class Meta:
        model = LorePost
        fields = [
            'title', 'category', 'excerpt', 
            'image_url', 'video_url', 'audio_url',
            'featured_image', 'featured_video', 'featured_audio',
            'alt_text', 'original_author', 'original_author_about'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., The Tortoise and the Birds'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'A brief summary of this lore...'}),
            'image_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'Optional: URL to stream image from'}),
            'video_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'Optional: URL to stream video from (YouTube, Vimeo, etc)'}),
            'audio_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'Optional: URL to stream audio from'}),
            'featured_image': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'featured_video': forms.FileInput(attrs={'class': 'form-input', 'accept': 'video/*'}),
            'featured_audio': forms.FileInput(attrs={'class': 'form-input', 'accept': 'audio/*'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Accessibility text for the image'}),
            'original_author': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional: Traditional source or writer'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit to lore categories
        self.fields['category'].queryset = Category.objects.filter(type='lore')
        self.fields['category'].empty_label = 'Select category...'
        
    def clean(self):
        cleaned_data = super().clean()
        
        # In the Lore app, media is optional, but if they provide media, validate that they don't provide BOTH url and file for the same type (or just let one override the other).
        # We'll keep it simple: no strict requirement on media, as Editor.js content is the core.
        
        return cleaned_data
