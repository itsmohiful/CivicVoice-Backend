import django_filters
from django.db.models import Q
from civicvoice_backend.complaints.models import (
    Complaint, ComplaintCategory, ComplaintSubCategory, ComplaintComment,
    ComplaintReaction, ComplaintTag, ComplaintAttachment, Location,
    ComplaintStatus, ComplaintPriority, ComplaintPrivacy, ComplaintReport,
    ComplaintStatusHistory
)


class ComplaintFilter(django_filters.FilterSet):
    """Advanced filtering for complaints"""
    
    # Text search
    search = django_filters.CharFilter(method='filter_search')
    
    # Status and priority
    status = django_filters.ChoiceFilter(choices=ComplaintStatus.choices)
    priority = django_filters.ChoiceFilter(choices=ComplaintPriority.choices)
    privacy = django_filters.ChoiceFilter(choices=ComplaintPrivacy.choices)
    
    # Category filtering
    category = django_filters.ModelChoiceFilter(queryset=ComplaintCategory.objects.filter(is_active=True))
    subcategory = django_filters.ModelChoiceFilter(queryset=ComplaintSubCategory.objects.filter(is_active=True))
    
    # Location filtering
    location_country = django_filters.CharFilter(field_name='location__country', lookup_expr='icontains')
    location_state = django_filters.CharFilter(field_name='location__state', lookup_expr='icontains')
    location_city = django_filters.CharFilter(field_name='location__city', lookup_expr='icontains')
    
    # Date filtering
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    submitted_after = django_filters.DateTimeFilter(field_name='submitted_at', lookup_expr='gte')
    submitted_before = django_filters.DateTimeFilter(field_name='submitted_at', lookup_expr='lte')
    
    # User filtering
    created_by = django_filters.CharFilter(field_name='created_by__email')
    assigned_to = django_filters.CharFilter(field_name='assigned_to__email')
    
    # Tags
    tags = django_filters.ModelMultipleChoiceFilter(queryset=ComplaintTag.objects.filter(is_active=True))
    
    # Analytics filtering
    min_view_count = django_filters.NumberFilter(field_name='view_count', lookup_expr='gte')
    min_reaction_count = django_filters.NumberFilter(field_name='reaction_count', lookup_expr='gte')
    
    # Boolean filters
    has_attachments = django_filters.BooleanFilter(method='filter_has_attachments')
    is_overdue = django_filters.BooleanFilter(method='filter_is_overdue')
    allow_comments = django_filters.BooleanFilter()
    allow_sharing = django_filters.BooleanFilter()
    
    class Meta:
        model = Complaint
        fields = {
            'complaint_number': ['exact', 'icontains'],
            'title': ['icontains'],
            'view_count': ['gte', 'lte'],
            'reaction_count': ['gte', 'lte'],
            'comment_count': ['gte', 'lte'],
        }

    def filter_search(self, queryset, name, value):
        """Search across multiple fields"""
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(description__icontains=value) |
                Q(complaint_number__icontains=value) |
                Q(category__name__icontains=value) |
                Q(tags__name__icontains=value)
            ).distinct()
        return queryset

    def filter_has_attachments(self, queryset, name, value):
        """Filter complaints with/without attachments"""
        if value is True:
            return queryset.filter(attachments__isnull=False).distinct()
        elif value is False:
            return queryset.filter(attachments__isnull=True)
        return queryset

    def filter_is_overdue(self, queryset, name, value):
        """Filter overdue complaints"""
        from django.utils import timezone
        if value is True:
            return queryset.filter(
                due_date__lt=timezone.now(),
                status__in=[ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.IN_PROGRESS]
            )
        elif value is False:
            return queryset.exclude(
                due_date__lt=timezone.now(),
                status__in=[ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.IN_PROGRESS]
            )
        return queryset


class ComplaintCategoryFilter(django_filters.FilterSet):
    """Filter for complaint categories"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = ComplaintCategory
        fields = ['is_active']


class ComplaintCommentFilter(django_filters.FilterSet):
    """Filter for complaint comments"""
    
    complaint = django_filters.ModelChoiceFilter(queryset=Complaint.objects.all())
    is_official = django_filters.BooleanFilter()
    is_anonymous = django_filters.BooleanFilter()
    parent = django_filters.ModelChoiceFilter(queryset=ComplaintComment.objects.all())
    
    class Meta:
        model = ComplaintComment
        fields = ['is_official', 'is_anonymous']


class ComplaintReactionFilter(django_filters.FilterSet):
    """Filter for complaint reactions"""
    
    complaint = django_filters.ModelChoiceFilter(queryset=Complaint.objects.all())
    reaction_type = django_filters.ChoiceFilter(choices=ComplaintReaction.ReactionType.choices)
    
    class Meta:
        model = ComplaintReaction
        fields = ['reaction_type']


class ComplaintAttachmentFilter(django_filters.FilterSet):
    """Filter for complaint attachments"""
    
    complaint = django_filters.ModelChoiceFilter(queryset=Complaint.objects.all())
    file_type = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = ComplaintAttachment
        fields = ['file_type']


class ComplaintSubCategoryFilter(django_filters.FilterSet):
    """Filter for complaint subcategories"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    category = django_filters.ModelChoiceFilter(queryset=ComplaintCategory.objects.all())
    
    class Meta:
        model = ComplaintSubCategory
        fields = ['is_active', 'category']


class ComplaintTagFilter(django_filters.FilterSet):
    """Filter for complaint tags"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = ComplaintTag
        fields = ['is_active']


class LocationFilter(django_filters.FilterSet):
    """Filter for locations"""
    
    country = django_filters.CharFilter(lookup_expr='icontains')
    state = django_filters.CharFilter(lookup_expr='icontains')
    city = django_filters.CharFilter(lookup_expr='icontains')
    area = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Location
        fields = ['country', 'state', 'city', 'area']


class ComplaintReportFilter(django_filters.FilterSet):
    """Filter for complaint reports"""
    
    reason = django_filters.ChoiceFilter(choices=ComplaintReport.ReportReason.choices)
    is_resolved = django_filters.BooleanFilter()
    
    class Meta:
        model = ComplaintReport
        fields = ['reason', 'is_resolved']


class ComplaintStatusHistoryFilter(django_filters.FilterSet):
    """Filter for complaint status history"""
    
    status = django_filters.ChoiceFilter(choices=ComplaintStatus.choices)
    complaint = django_filters.ModelChoiceFilter(queryset=Complaint.objects.all())
    
    class Meta:
        model = ComplaintStatusHistory
        fields = ['status']
