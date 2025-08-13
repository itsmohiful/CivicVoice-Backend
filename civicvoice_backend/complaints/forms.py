from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .models import (
    Complaint, ComplaintComment, ComplaintCategory, ComplaintSubCategory,
    ComplaintTag, ComplaintAttachment, ComplaintReport, Location,
    ComplaintStatus, ComplaintPriority, ComplaintPrivacy
)


class ComplaintCreateForm(forms.ModelForm):
    """
    Form for creating new complaints
    """
    tags = forms.ModelMultipleChoiceField(
        queryset=ComplaintTag.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text=_("Select relevant tags for your complaint")
    )
    
    # Location fields
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': _('e.g., Bangladesh')})
    )
    state = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': _('e.g., Dhaka Division')})
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': _('e.g., Dhaka')})
    )
    area = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('e.g., Dhanmondi (optional)')})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': _('Full address (optional)')}),
        required=False
    )
    
    class Meta:
        model = Complaint
        fields = [
            'title', 'description', 'category', 'subcategory', 'priority',
            'privacy', 'allow_comments', 'allow_sharing', 'incident_date', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': _('Brief, descriptive title for your complaint'),
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': _('Provide detailed information about your complaint...'),
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subcategory': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'privacy': forms.Select(attrs={'class': 'form-control'}),
            'incident_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'allow_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_sharing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'title': _('Keep it concise but descriptive (10-200 characters)'),
            'description': _('Provide as much detail as possible (minimum 50 characters)'),
            'priority': _('Select the urgency level of your complaint'),
            'privacy': _('Control who can see your complaint'),
            'incident_date': _('When did this incident occur? (optional)'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make subcategory field dynamic based on category
        self.fields['subcategory'].queryset = ComplaintSubCategory.objects.none()
        
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = ComplaintSubCategory.objects.filter(
                    category_id=category_id, is_active=True
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = self.instance.category.subcategories.filter(
                is_active=True
            )
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 10:
            raise ValidationError(_('Title must be at least 10 characters long.'))
        return title
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 50:
            raise ValidationError(_('Description must be at least 50 characters long.'))
        return description
    
    def save(self, commit=True):
        complaint = super().save(commit=False)
        
        # Create location if provided
        if any([self.cleaned_data.get('country'), self.cleaned_data.get('city')]):
            location = Location.objects.create(
                country=self.cleaned_data.get('country', ''),
                state=self.cleaned_data.get('state', ''),
                city=self.cleaned_data.get('city', ''),
                area=self.cleaned_data.get('area', ''),
                address=self.cleaned_data.get('address', ''),
                created_by=complaint.created_by
            )
            complaint.location = location
        
        if commit:
            complaint.save()
            self.save_m2m()  # Save tags
        
        return complaint


class ComplaintUpdateForm(forms.ModelForm):
    """
    Form for updating existing complaints (limited fields)
    """
    class Meta:
        model = Complaint
        fields = [
            'title', 'description', 'category', 'subcategory', 'priority',
            'privacy', 'allow_comments', 'allow_sharing', 'incident_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subcategory': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'privacy': forms.Select(attrs={'class': 'form-control'}),
            'incident_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only allow editing if complaint is in editable state
        if self.instance and self.instance.status not in [ComplaintStatus.DRAFT, ComplaintStatus.SUBMITTED]:
            for field in self.fields:
                self.fields[field].disabled = True


class ComplaintCommentForm(forms.ModelForm):
    """
    Form for adding comments to complaints
    """
    class Meta:
        model = ComplaintComment
        fields = ['content', 'is_anonymous']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': _('Share your thoughts or additional information...'),
                'class': 'form-control'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        help_texts = {
            'content': _('Minimum 5 characters required'),
            'is_anonymous': _('Post this comment anonymously')
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
       
        return content


class ComplaintSearchForm(forms.Form):
    """
    Form for searching and filtering complaints
    """
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search complaints...'),
            'class': 'form-control'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=ComplaintCategory.objects.filter(is_active=True),
        required=False,
        empty_label=_('All Categories'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Status'))] + list(ComplaintStatus.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=[('', _('All Priorities'))] + list(ComplaintPriority.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Filter by location...'),
            'class': 'form-control'
        })
    )
    
    sort = forms.ChoiceField(
        choices=[
            ('-created_at', _('Newest First')),
            ('created_at', _('Oldest First')),
            ('-view_count', _('Most Viewed')),
            ('-reaction_count', _('Most Reactions')),
            ('priority', _('Priority')),
        ],
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ComplaintReportForm(forms.ModelForm):
    """
    Form for reporting inappropriate complaints
    """
    class Meta:
        model = ComplaintReport
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': _('Please provide additional details about why you are reporting this complaint...'),
                'class': 'form-control'
            })
        }
        help_texts = {
            'reason': _('Select the primary reason for reporting'),
            'description': _('Provide specific details to help us review this report')
        }


class ComplaintAttachmentForm(forms.ModelForm):
    """
    Form for uploading attachments to complaints
    """
    class Meta:
        model = ComplaintAttachment
        fields = ['file', 'description']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf,.doc,.docx,.txt'
            }),
            'description': forms.TextInput(attrs={
                'placeholder': _('Brief description of this file (optional)'),
                'class': 'form-control'
            })
        }
        help_texts = {
            'file': _('Supported formats: Images, PDF, DOC, DOCX, TXT (Max: 10MB)'),
            'description': _('Help others understand what this file contains')
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError(_('File size cannot exceed 10MB.'))
            
            # Check file type
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'application/pdf', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain'
            ]
            
            if file.content_type not in allowed_types:
                raise ValidationError(_('File type not supported. Please upload images, PDF, DOC, DOCX, or TXT files.'))
        
        return file


class AdminComplaintStatusForm(forms.ModelForm):
    """
    Form for admin/staff to update complaint status
    """
    status_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Reason for status change (optional)'),
            'class': 'form-control'
        }),
        required=False,
        help_text=_('Explain why the status is being changed')
    )
    
    class Meta:
        model = Complaint
        fields = ['status', 'assigned_to', 'reference_number']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={
                'placeholder': _('External reference number (optional)'),
                'class': 'form-control'
            })
        }


class BulkActionForm(forms.Form):
    """
    Form for bulk actions on complaints
    """
    ACTION_CHOICES = [
        ('mark_reviewed', _('Mark as Under Review')),
        ('mark_resolved', _('Mark as Resolved')),
        ('assign_user', _('Assign to User')),
        ('change_priority', _('Change Priority')),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned_user = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=ComplaintPriority.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Reason for this action (optional)'),
            'class': 'form-control'
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        super().__init__(*args, **kwargs)
        
        # Set queryset for assigned_user
        self.fields['assigned_user'].queryset = User.objects.filter(
            is_staff=True, is_active=True
        )


# AJAX Forms for dynamic loading
class SubCategoryForm(forms.Form):
    """
    Form for loading subcategories based on category selection
    """
    category = forms.ModelChoiceField(
        queryset=ComplaintCategory.objects.filter(is_active=True)
    )
    
    def get_subcategories(self):
        if self.is_valid():
            category = self.cleaned_data['category']
            return category.subcategories.filter(is_active=True)
        return ComplaintSubCategory.objects.none()
