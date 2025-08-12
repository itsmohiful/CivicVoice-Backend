from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from civicvoice_backend.utils.models import BaseModel

User = get_user_model()


class ComplaintCategory(BaseModel):
    """
    Categories for complaints (e.g., Police, Government, Municipal, Healthcare, etc.)
    """
    name = models.CharField(_("Category Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    icon = models.CharField(_("Icon Class"), max_length=50, blank=True, help_text=_("Font Awesome icon class"))
    color = models.CharField(_("Color Code"), max_length=7, default="#007bff", help_text=_("Hex color code"))
    is_active = models.BooleanField(_("Is Active"), default=True)
    sort_order = models.PositiveIntegerField(_("Sort Order"), default=0)
    
    # Department/Authority specific fields
    department_email = models.EmailField(_("Department Email"), blank=True, null=True)
    department_phone = models.CharField(_("Department Phone"), max_length=20, blank=True)
    escalation_days = models.PositiveIntegerField(_("Auto Escalation Days"), default=7, 
                                                help_text=_("Days after which complaint will be auto-escalated"))
    
    class Meta:
        verbose_name = _("Complaint Category")
        verbose_name_plural = _("Complaint Categories")
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('complaints:category_detail', kwargs={'pk': self.pk})


class ComplaintSubCategory(BaseModel):
    """
    Sub-categories for more specific complaint types
    """
    category = models.ForeignKey(ComplaintCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(_("Sub-Category Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    sort_order = models.PositiveIntegerField(_("Sort Order"), default=0)
    
    class Meta:
        verbose_name = _("Complaint Sub-Category")
        verbose_name_plural = _("Complaint Sub-Categories")
        ordering = ['sort_order', 'name']
        unique_together = ['category', 'name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class ComplaintPriority(models.TextChoices):
    """Priority levels for complaints"""
    LOW = 'low', _('Low')
    MEDIUM = 'medium', _('Medium')
    HIGH = 'high', _('High')
    URGENT = 'urgent', _('Urgent')
    CRITICAL = 'critical', _('Critical')


class ComplaintStatus(models.TextChoices):
    """Status options for complaints"""
    DRAFT = 'draft', _('Draft')
    SUBMITTED = 'submitted', _('Submitted')
    UNDER_REVIEW = 'under_review', _('Under Review')
    IN_PROGRESS = 'in_progress', _('In Progress')
    PENDING_INFO = 'pending_info', _('Pending Information')
    RESOLVED = 'resolved', _('Resolved')
    CLOSED = 'closed', _('Closed')
    REJECTED = 'rejected', _('Rejected')
    ESCALATED = 'escalated', _('Escalated')


class ComplaintPrivacy(models.TextChoices):
    """Privacy settings for complaints"""
    PUBLIC = 'public', _('Public')
    PRIVATE = 'private', _('Private')
    ANONYMOUS = 'anonymous', _('Anonymous')


class Location(BaseModel):
    """Location information for complaints"""
    country = models.CharField(_("Country"), max_length=100)
    state = models.CharField(_("State/Province"), max_length=100)
    city = models.CharField(_("City"), max_length=100)
    area = models.CharField(_("Area/Locality"), max_length=100, blank=True)
    postal_code = models.CharField(_("Postal Code"), max_length=20, blank=True)
    address = models.TextField(_("Full Address"), blank=True)
    latitude = models.DecimalField(_("Latitude"), max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(_("Longitude"), max_digits=11, decimal_places=8, null=True, blank=True)
    
    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")
    
    def __str__(self):
        return f"{self.city}, {self.state}, {self.country}"


class Complaint(BaseModel):
    """
    Main complaint model with comprehensive fields
    """
    # Basic Information
    title = models.CharField(_("Title"), max_length=200, validators=[MinLengthValidator(10)])
    description = models.TextField(_("Description"), validators=[MinLengthValidator(50)])
    category = models.ForeignKey(ComplaintCategory, on_delete=models.PROTECT, related_name='complaints')
    subcategory = models.ForeignKey(ComplaintSubCategory, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='complaints')
    
    # Status and Priority
    status = models.CharField(_("Status"), max_length=20, choices=ComplaintStatus.choices, 
                            default=ComplaintStatus.DRAFT)
    priority = models.CharField(_("Priority"), max_length=20, choices=ComplaintPriority.choices, 
                              default=ComplaintPriority.MEDIUM)
    
    # Privacy and Permissions
    privacy = models.CharField(_("Privacy"), max_length=20, choices=ComplaintPrivacy.choices, 
                             default=ComplaintPrivacy.PUBLIC)
    allow_comments = models.BooleanField(_("Allow Comments"), default=True)
    allow_sharing = models.BooleanField(_("Allow Sharing"), default=True)
    
    # Location
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='complaints')
    
    # Dates and Tracking
    incident_date = models.DateTimeField(_("Incident Date"), null=True, blank=True)
    submitted_at = models.DateTimeField(_("Submitted At"), null=True, blank=True)
    due_date = models.DateTimeField(_("Due Date"), null=True, blank=True)
    resolved_at = models.DateTimeField(_("Resolved At"), null=True, blank=True)
    
    # Reference and Tracking
    complaint_number = models.CharField(_("Complaint Number"), max_length=20, unique=True, editable=False)
    reference_number = models.CharField(_("External Reference"), max_length=50, blank=True,
                                      help_text=_("Reference from government/police system"))
    
    # Analytics and Engagement
    view_count = models.PositiveIntegerField(_("View Count"), default=0)
    reaction_count = models.PositiveIntegerField(_("Total Reactions"), default=0)
    comment_count = models.PositiveIntegerField(_("Comment Count"), default=0)
    share_count = models.PositiveIntegerField(_("Share Count"), default=0)
    
    # Additional Information
    tags = models.ManyToManyField('ComplaintTag', blank=True, related_name='complaints')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='assigned_complaints', 
                                  help_text=_("Authority/Officer assigned to handle this complaint"))
    
    # Escalation
    escalated_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='escalated_complaints')
    escalation_reason = models.TextField(_("Escalation Reason"), blank=True)
    
    class Meta:
        verbose_name = _("Complaint")
        verbose_name_plural = _("Complaints")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['complaint_number']),
            models.Index(fields=['privacy', 'status']),
        ]
    
    def __str__(self):
        return f"{self.complaint_number} - {self.title[:50]}"
    
    def save(self, *args, **kwargs):
        if not self.complaint_number:
            self.complaint_number = self.generate_complaint_number()
        
        # Auto-set submitted_at when status changes to submitted
        if self.status == ComplaintStatus.SUBMITTED and not self.submitted_at:
            self.submitted_at = timezone.now()
            if self.category.escalation_days:
                self.due_date = self.submitted_at + timedelta(days=self.category.escalation_days)
        
        # Set resolved_at when status changes to resolved
        if self.status == ComplaintStatus.RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_complaint_number(self):
        """Generate unique complaint number"""
        from django.utils import timezone
        now = timezone.now()
        prefix = f"CMP{now.year}{now.month:02d}"
        
        # Get the last complaint number for this month
        last_complaint = Complaint.objects.filter(
            complaint_number__startswith=prefix
        ).order_by('-complaint_number').first()
        
        if last_complaint:
            last_number = int(last_complaint.complaint_number[-6:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:06d}"
    
    def get_absolute_url(self):
        return reverse('complaints:detail', kwargs={'complaint_number': self.complaint_number})
    
    def can_view(self, user):
        """Check if user can view this complaint"""
        if self.privacy == ComplaintPrivacy.PUBLIC:
            return True
        elif self.privacy == ComplaintPrivacy.PRIVATE:
            return user == self.created_by or user.is_staff
        elif self.privacy == ComplaintPrivacy.ANONYMOUS:
            return True
        return False
    
    def can_edit(self, user):
        """Check if user can edit this complaint"""
        return user == self.created_by and self.status in [ComplaintStatus.DRAFT, ComplaintStatus.SUBMITTED]
    
    def increment_view_count(self):
        """Increment view count atomically"""
        from django.db.models import F
        Complaint.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)
    
    @property
    def is_overdue(self):
        """Check if complaint is overdue"""
        if self.due_date and self.status not in [ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED]:
            return timezone.now() > self.due_date
        return False
    
    @property
    def like_count(self):
        """Count of like reactions"""
        return self.reactions.filter(reaction_type='like').count()
    
    @property
    def support_count(self):
        """Count of support reactions"""
        return self.reactions.filter(reaction_type='support').count()
    
    @property
    def concern_count(self):
        """Count of concern reactions"""
        return self.reactions.filter(reaction_type='concern').count()
    
    @property
    def angry_count(self):
        """Count of angry reactions"""
        return self.reactions.filter(reaction_type='angry').count()
    
    @property
    def sad_count(self):
        """Count of sad reactions"""
        return self.reactions.filter(reaction_type='sad').count()
    
    @property
    def total_reactions(self):
        """Total count of all reactions"""
        return self.reactions.count()


class ComplaintTag(BaseModel):
    """Tags for categorizing complaints"""
    name = models.CharField(_("Tag Name"), max_length=50, unique=True)
    color = models.CharField(_("Color"), max_length=7, default="#6c757d")
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    class Meta:
        verbose_name = _("Complaint Tag")
        verbose_name_plural = _("Complaint Tags")
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ComplaintAttachment(BaseModel):
    """File attachments for complaints"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(_("File"), upload_to='complaints/attachments/%Y/%m/')
    original_name = models.CharField(_("Original Name"), max_length=255)
    file_size = models.PositiveIntegerField(_("File Size"), help_text=_("Size in bytes"))
    file_type = models.CharField(_("File Type"), max_length=100)
    description = models.CharField(_("Description"), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _("Complaint Attachment")
        verbose_name_plural = _("Complaint Attachments")
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.complaint.complaint_number} - {self.original_name}"
    
    def clean(self):
        # Validate file size (max 10MB)
        if self.file and self.file.size > 10 * 1024 * 1024:
            raise ValidationError(_("File size cannot exceed 10MB"))


class ComplaintReaction(BaseModel):
    """User reactions to complaints (like, support, etc.)"""
    
    class ReactionType(models.TextChoices):
        LIKE = 'like', _('Like')
        SUPPORT = 'support', _('Support')
        CONCERN = 'concern', _('Concern')
        ANGRY = 'angry', _('Angry')
        SAD = 'sad', _('Sad')
    
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaint_reactions')
    reaction_type = models.CharField(_("Reaction Type"), max_length=20, choices=ReactionType.choices)
    
    class Meta:
        verbose_name = _("Complaint Reaction")
        verbose_name_plural = _("Complaint Reactions")
        unique_together = ['complaint', 'user']  # One reaction per user per complaint
        indexes = [
            models.Index(fields=['complaint', 'reaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.reaction_type} - {self.complaint.complaint_number}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update complaint reaction count
        self.complaint.reaction_count = self.complaint.reactions.count()
        self.complaint.save(update_fields=['reaction_count'])


class ComplaintComment(BaseModel):
    """Comments on complaints"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                             related_name='replies')
    content = models.TextField(_("Content"), validators=[MinLengthValidator(5)])
    is_official = models.BooleanField(_("Official Response"), default=False,
                                    help_text=_("Mark as official response from authority"))
    
    # Privacy for anonymous comments
    is_anonymous = models.BooleanField(_("Anonymous Comment"), default=False)
    
    class Meta:
        verbose_name = _("Complaint Comment")
        verbose_name_plural = _("Complaint Comments")
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['complaint', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment on {self.complaint.complaint_number} by {self.created_by.name if not self.is_anonymous else 'Anonymous'}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update complaint comment count
        if not self.parent:  # Only count top-level comments
            self.complaint.comment_count = self.complaint.comments.filter(parent__isnull=True).count()
            self.complaint.save(update_fields=['comment_count'])


class ComplaintCommentReaction(BaseModel):
    """Reactions to comments"""
    
    class ReactionType(models.TextChoices):
        LIKE = 'like', _('Like')
        DISLIKE = 'dislike', _('Dislike')
        HELPFUL = 'helpful', _('Helpful')
    
    comment = models.ForeignKey(ComplaintComment, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_reactions')
    reaction_type = models.CharField(_("Reaction Type"), max_length=20, choices=ReactionType.choices)
    
    class Meta:
        verbose_name = _("Comment Reaction")
        verbose_name_plural = _("Comment Reactions")
        unique_together = ['comment', 'user']
    
    def __str__(self):
        return f"{self.user.name} - {self.reaction_type} - Comment #{self.comment.id}"


class ComplaintStatusHistory(BaseModel):
    """Track status changes of complaints"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(_("Previous Status"), max_length=20, choices=ComplaintStatus.choices)
    new_status = models.CharField(_("New Status"), max_length=20, choices=ComplaintStatus.choices)
    reason = models.TextField(_("Reason for Change"), blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='status_changes')
    
    class Meta:
        verbose_name = _("Status History")
        verbose_name_plural = _("Status Histories")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.complaint.complaint_number}: {self.previous_status} → {self.new_status}"


class ComplaintShare(BaseModel):
    """Track complaint shares"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_complaints')
    platform = models.CharField(_("Platform"), max_length=50, blank=True,
                               help_text=_("Platform where it was shared (email, social media, etc.)"))
    
    class Meta:
        verbose_name = _("Complaint Share")
        verbose_name_plural = _("Complaint Shares")
        ordering = ['-created_at']
        unique_together = ['complaint', 'shared_by']  # Prevent duplicate shares by same user
    
    def __str__(self):
        return f"{self.complaint.complaint_number} shared by {self.shared_by.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update complaint share count
        self.complaint.share_count = self.complaint.shares.count()
        self.complaint.save(update_fields=['share_count'])


class ComplaintFollower(BaseModel):
    """Users following complaints for updates"""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='followers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_complaints')
    notify_status_change = models.BooleanField(_("Notify Status Change"), default=True)
    notify_new_comment = models.BooleanField(_("Notify New Comment"), default=True)
    notify_resolution = models.BooleanField(_("Notify Resolution"), default=True)
    
    class Meta:
        verbose_name = _("Complaint Follower")
        verbose_name_plural = _("Complaint Followers")
        unique_together = ['complaint', 'user']
    
    def __str__(self):
        return f"{self.user.name} following {self.complaint.complaint_number}"


class ComplaintReport(BaseModel):
    """Reports for inappropriate complaints"""
    
    class ReportReason(models.TextChoices):
        SPAM = 'spam', _('Spam')
        INAPPROPRIATE = 'inappropriate', _('Inappropriate Content')
        FALSE_INFO = 'false_info', _('False Information')
        DUPLICATE = 'duplicate', _('Duplicate')
        OTHER = 'other', _('Other')
    
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaint_reports')
    reason = models.CharField(_("Reason"), max_length=20, choices=ReportReason.choices)
    description = models.TextField(_("Description"), blank=True)
    is_resolved = models.BooleanField(_("Is Resolved"), default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='resolved_reports')
    resolved_at = models.DateTimeField(_("Resolved At"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Complaint Report")
        verbose_name_plural = _("Complaint Reports")
        unique_together = ['complaint', 'reported_by']
    
    def __str__(self):
        return f"Report: {self.complaint.complaint_number} by {self.reported_by.name}"

