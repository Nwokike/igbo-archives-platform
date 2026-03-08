"""
Forms for Archive create and edit.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from .models import Archive, ArchiveItem, Category


class ArchiveForm(forms.ModelForm):
    """
    Form for the 'Parent' Archive container.
    Handles metadata like Title, Category, Source.
    """
    
    date_created = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input'
        })
    )
    
    original_author_about = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 3,
            'placeholder': 'Provide a brief biography or description for the Original Author.'
        })
    )
    
    class Meta:
        model = Archive
        # Exclude file fields and archive_type (inferred from first item)
        fields = [
            'title', 'description', 'category',
            'item_count', 
            'copyright_holder', 
            'original_author', 'original_url', 'original_identity_number',
            'location', 'date_created', 'circa_date',
            'image_url', 'video_url', 'document_url', 'audio_url'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Detailed description of the archive context'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'item_count': forms.Select(attrs={'class': 'form-select', 'id': 'id_item_count'}, choices=[
                (1, '1 item'),
                (2, '2 items'),
                (3, '3 items'),
                (4, '4 items'),
                (5, '5 items'),
            ]),
            'copyright_holder': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., British Museum, Public Domain'
            }),
            'original_author': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Northcote Thomas',
                'list': 'author-list'
            }),
            'original_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://museum.org/collection/item123'
            }),
            'original_identity_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., BM-1234, NT.001'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Onitsha, Anambra State'
            }),
            'circa_date': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., c1910, around 1910s',
                'list': 'date-list'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FILTER: Only show 'archive' type categories in the dropdown
        self.fields['category'].queryset = Category.objects.filter(type='archive')
        self.fields['category'].empty_label = 'Select category...'
        
        # Apply utility classes to all fields (avoid duplicating if already set in widgets)
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get('class', '')
            if isinstance(field.widget, (forms.TextInput, forms.URLInput, forms.DateInput)):
                if 'form-input' not in current_class:
                    field.widget.attrs['class'] = f'form-input {current_class}'.strip()
            elif isinstance(field.widget, forms.Textarea):
                if 'form-textarea' not in current_class:
                    field.widget.attrs['class'] = f'form-textarea {current_class}'.strip()
            elif isinstance(field.widget, forms.Select):
                if 'form-select' not in current_class:
                    field.widget.attrs['class'] = f'form-select {current_class}'.strip()
    
    def clean_original_identity_number(self):
        """Validate that IDNO is unique, with graceful error message."""
        idno = self.cleaned_data.get('original_identity_number', '').strip()
        
        if not idno:
            return idno
        
        # Find existing archive with same IDNO
        existing = Archive.objects.filter(original_identity_number__iexact=idno)
        
        # Exclude current instance if editing
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        existing = existing.first()
        
        if existing:
            raise ValidationError(
                f'An archive with ID Number "{idno}" already exists.'
            )
        
        return idno

    def save(self, commit=True):
        """Overridden to handle Author creation linked to the original_author string."""
        instance = super().save(commit=False)
        
        # Try to match the original_author text to a true Author profile
        original_author_name = self.cleaned_data.get('original_author')
        author_about_text = self.cleaned_data.get('original_author_about')
        
        if original_author_name:
            from archives.models import Author
            # Safe case-insensitive author lookup — avoids MultipleObjectsReturned
            author_obj = Author.objects.filter(name__iexact=original_author_name).first()
            if not author_obj:
                author_obj = Author.objects.create(name=original_author_name)
            
            # If the user supplied a bio and the author doesn't have one, or just created it
            if author_about_text and not author_obj.description:
                author_obj.description = author_about_text
                author_obj.save()
            
            # Link the newly found/created author to the Archive explicitly
            instance.author = author_obj

        if commit:
            instance.save()
            
        return instance

class ArchiveItemForm(forms.ModelForm):
    """
    Form for individual Archive Items (File + Caption).
    """
    class Meta:
        model = ArchiveItem
        fields = [
            'item_type', 
            'image', 'video', 'audio', 'document',
            'image_url', 'video_url', 'audio_url', 'document_url',
            'caption', 'alt_text'
        ]
        widgets = {
            'item_type': forms.Select(attrs={'class': 'form-select item-type-select'}),
            'caption': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Caption for this specific item'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Accessibility description'}),
            'image': forms.FileInput(attrs={'class': 'form-input item-file-input', 'accept': '.jpg,.jpeg,.png,.webp'}),
            'video': forms.FileInput(attrs={'class': 'form-input item-file-input', 'accept': '.mp4,.webm,.ogg,.mov'}),
            'audio': forms.FileInput(attrs={'class': 'form-input item-file-input', 'accept': '.mp3,.wav,.ogg,.m4a'}),
            'document': forms.FileInput(attrs={'class': 'form-input item-file-input', 'accept': '.pdf,.doc,.docx,.txt'}),
            'image_url': forms.URLInput(attrs={'class': 'form-input item-url-input', 'placeholder': 'https://...'}),
            'video_url': forms.URLInput(attrs={'class': 'form-input item-url-input', 'placeholder': 'https://...'}),
            'audio_url': forms.URLInput(attrs={'class': 'form-input item-url-input', 'placeholder': 'https://...'}),
            'document_url': forms.URLInput(attrs={'class': 'form-input item-url-input', 'placeholder': 'https://...'}),
        }

    def clean(self):
        """Validate that the correct file is present for the selected item type."""
        cleaned_data = super().clean()
        item_type = cleaned_data.get('item_type')
        
        if not item_type:
            return cleaned_data # Let field validation handle required error

        # Check existing instance files (for edit mode) or new upload
        image = cleaned_data.get('image') or (self.instance.image if self.instance.pk else None)
        video = cleaned_data.get('video') or (self.instance.video if self.instance.pk else None)
        audio = cleaned_data.get('audio') or (self.instance.audio if self.instance.pk else None)
        document = cleaned_data.get('document') or (self.instance.document if self.instance.pk else None)
        
        # Check URL alternatives
        image_url = cleaned_data.get('image_url')
        video_url = cleaned_data.get('video_url')
        audio_url = cleaned_data.get('audio_url')
        document_url = cleaned_data.get('document_url')

        if item_type == 'image':
            if not image and not image_url:
                raise ValidationError('Image file OR URL is required for image type items.')
            if not cleaned_data.get('alt_text'):
                raise ValidationError('Alt text is required for images.')
        elif item_type == 'video' and not video and not video_url:
            raise ValidationError('Video file OR URL is required for video type items.')
        elif item_type == 'audio' and not audio and not audio_url:
            raise ValidationError('Audio file OR URL is required for audio type items.')
        elif item_type == 'document' and not document and not document_url:
            raise ValidationError('Document file OR URL is required for document type items.')
            
        return cleaned_data


# Formset to manage multiple ArchiveItems attached to one Archive
ArchiveItemFormSet = inlineformset_factory(
    Archive,
    ArchiveItem,
    form=ArchiveItemForm,
    extra=1,       # Start with 1 blank form (JS can add more)
    max_num=5,     # Maximum 5 items
    can_delete=True,
    validate_max=True
)

from .models import ArchiveNote, ArchiveNoteSuggestion

class ArchiveNoteForm(forms.ModelForm):
    """Form to add or edit Community Notes using the same Editor.js structure as Books."""
    
    # We don't strictly bind the Editor.js content_json directly to a Django widget
    # because Editor.js requires a specific DOM container. We parse the hidden input manually in the view.
    # Therefore, no specific fields are needed here besides what is handled via AJAX/templates.
    class Meta:
        model = ArchiveNote
        fields = []

class ArchiveNoteSuggestionForm(forms.ModelForm):
    class Meta:
        model = ArchiveNoteSuggestion
        fields = []

from .models import AuthorDescriptionRequest

class AuthorDescriptionRequestForm(forms.ModelForm):
    class Meta:
        model = AuthorDescriptionRequest
        fields = ['proposed_description']
        widgets = {
            'proposed_description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Provide a detailed biography or description for this author/creator.'
            })
        }
