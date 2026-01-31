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
    
    class Meta:
        model = Archive
        # Exclude file fields and archive_type (inferred from first item)
        fields = [
            'title', 'description', 'category',
            'item_count', 
            'copyright_holder', 
            'original_author', 'original_url', 'original_identity_number',
            'location', 'date_created', 'circa_date', 
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
        
        # Apply utility classes to all fields
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get('class', '')
            if isinstance(field.widget, (forms.TextInput, forms.URLInput, forms.DateInput)):
                field.widget.attrs['class'] = f'form-input {current_class}'.strip()
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = f'form-textarea {current_class}'.strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = f'form-select {current_class}'.strip()


class ArchiveItemForm(forms.ModelForm):
    """
    Form for individual Archive Items (File + Caption).
    """
    class Meta:
        model = ArchiveItem
        fields = ['item_type', 'image', 'video', 'audio', 'document', 'caption', 'alt_text']
        widgets = {
            'item_type': forms.Select(attrs={'class': 'form-select item-type-select'}),
            'caption': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Caption for this specific item'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Accessibility description'}),
            'image': forms.FileInput(attrs={'class': 'form-input item-file-input', 'accept': '.jpg,.jpeg,.png,.webp'}),
            'video': forms.FileInput(attrs={'class': 'form-input item-file-input', 'accept': '.mp4,.webm,.ogg,.mov'}),
            'audio': forms.FileInput(attrs={'class': 'form-input item-file-input', 'accept': '.mp3,.wav,.ogg,.m4a'}),
            'document': forms.FileInput(attrs={'class': 'form-input item-file-input', 'accept': '.pdf,.doc,.docx,.txt'}),
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

        if item_type == 'image':
            if not image:
                raise ValidationError('Image file is required for image type items.')
            if not cleaned_data.get('alt_text'):
                raise ValidationError('Alt text is required for images.')
        elif item_type == 'video' and not video:
            raise ValidationError('Video file is required for video type items.')
        elif item_type == 'audio' and not audio:
            raise ValidationError('Audio file is required for audio type items.')
        elif item_type == 'document' and not document:
            raise ValidationError('Document file is required for document type items.')
            
        return cleaned_data


# Formset to manage multiple ArchiveItems attached to one Archive
ArchiveItemFormSet = inlineformset_factory(
    Archive,
    ArchiveItem,
    form=ArchiveItemForm,
    extra=5,       # Allow up to 5 blank forms (JS will hide/show them)
    max_num=5,     # Maximum 5 items
    can_delete=True,
    validate_max=True
)