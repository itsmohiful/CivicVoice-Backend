from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q

from .models import (
    ComplaintCategory, ComplaintSubCategory, Complaint, ComplaintTag,
    ComplaintAttachment, ComplaintReaction, ComplaintComment, 
    ComplaintCommentReaction, ComplaintStatusHistory, ComplaintShare,
    ComplaintFollower, ComplaintReport, Location
)


class ComplaintSubCategoryInline(admin.TabularInline):
    model = ComplaintSubCategory
    extra = 0
    fields = ('name', 'description', 'is_active', 'sort_order')


@admin.register(ComplaintCategory)
class ComplaintCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'complaint_count', 'is_active', 'escalation_days', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'name')
    prepopulated_fields = {"name": ("name",)}
    inlines = [ComplaintSubCategoryInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description', 'icon', 'color', 'is_active', 'sort_order')
        }),
        (_('Department Details'), {
            'fields': ('department_email', 'department_phone', 'escalation_days'),
            'classes': ('collapse',)
        }),
    )
    
    def complaint_count(self, obj):
        return obj.complaints.count()
    complaint_count.short_description = _('Complaints')
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            complaint_count=Count('complaints')
        )


class ComplaintAttachmentInline(admin.TabularInline):
    model = ComplaintAttachment
    extra = 0
    readonly_fields = ('file_size', 'file_type', 'original_name')
    fields = ('file', 'description', 'original_name', 'file_size', 'file_type')


class ComplaintStatusHistoryInline(admin.TabularInline):
    model = ComplaintStatusHistory
    extra = 0
    readonly_fields = ('created_at', 'changed_by')
    fields = ('previous_status', 'new_status', 'reason', 'changed_by', 'created_at')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'complaint_number', 'title_short', 'category', 'status', 'priority', 
        'privacy', 'created_by', 'view_count', 'reaction_count', 'created_at'
    )
    list_filter = (
        'status', 'priority', 'privacy', 'category', 'created_at', 
        'submitted_at', 'is_deleted'
    )
    search_fields = ('complaint_number', 'title', 'description', 'created_by__email')
    readonly_fields = (
        'complaint_number', 'created_at', 'updated_at', 'view_count', 
        'reaction_count', 'comment_count', 'share_count', 'uuid'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('complaint_number', 'title', 'description', 'category', 'subcategory','tags', 'created_by')
        }),
        (_('Status & Priority'), {
            'fields': ('status', 'priority', 'assigned_to', 'reference_number')
        }),
        (_('Privacy & Permissions'), {
            'fields': ('privacy', 'allow_comments', 'allow_sharing')
        }),
        (_('Location & Dates'), {
            'fields': ('location', 'incident_date', 'submitted_at', 'due_date', 'resolved_at'),
            'classes': ('collapse',)
        }),
        (_('Engagement Analytics'), {
            'fields': ('view_count', 'reaction_count', 'comment_count', 'share_count'),
            'classes': ('collapse',)
        }),
        (_('Escalation'), {
            'fields': ('escalated_from', 'escalation_reason'),
            'classes': ('collapse',)
        }),
        (_('System Information'), {
            'fields': ('uuid', 'created_by', 'created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('tags',)
    inlines = [ComplaintAttachmentInline, ComplaintStatusHistoryInline]
    
    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = _('Title')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'subcategory', 'created_by', 'location'
        ).prefetch_related('tags')
    
    actions = ['mark_as_resolved', 'mark_as_under_review', 'escalate_complaint']
    
    def mark_as_resolved(self, request, queryset):
        from .models import ComplaintStatus
        updated = queryset.update(status=ComplaintStatus.RESOLVED)
        self.message_user(request, f'{updated} complaints marked as resolved.')
    mark_as_resolved.short_description = _('Mark selected complaints as resolved')
    
    def mark_as_under_review(self, request, queryset):
        from .models import ComplaintStatus
        updated = queryset.update(status=ComplaintStatus.UNDER_REVIEW)
        self.message_user(request, f'{updated} complaints marked as under review.')
    mark_as_under_review.short_description = _('Mark selected complaints as under review')


@admin.register(ComplaintComment)
class ComplaintCommentAdmin(admin.ModelAdmin):
    list_display = ('complaint_number', 'created_by_name', 'content_short', 'is_official', 'is_anonymous', 'created_at')
    list_filter = ('is_official', 'is_anonymous', 'created_at')
    search_fields = ('complaint__complaint_number', 'content', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def complaint_number(self, obj):
        return obj.complaint.complaint_number
    complaint_number.short_description = _('Complaint')
    
    def created_by_name(self, obj):
        return 'Anonymous' if obj.is_anonymous else obj.created_by.name
    created_by_name.short_description = _('Author')
    
    def content_short(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_short.short_description = _('Content')


@admin.register(ComplaintReaction)
class ComplaintReactionAdmin(admin.ModelAdmin):
    list_display = ('complaint_number', 'user', 'reaction_type', 'created_at')
    list_filter = ('reaction_type', 'created_at')
    search_fields = ('complaint__complaint_number', 'user__email')
    
    def complaint_number(self, obj):
        return obj.complaint.complaint_number
    complaint_number.short_description = _('Complaint')


@admin.register(ComplaintReport)
class ComplaintReportAdmin(admin.ModelAdmin):
    list_display = ('complaint_number', 'reported_by', 'reason', 'is_resolved', 'created_at')
    list_filter = ('reason', 'is_resolved', 'created_at')
    search_fields = ('complaint__complaint_number', 'reported_by__email', 'description')
    readonly_fields = ('created_at', 'resolved_at')
    
    actions = ['mark_as_resolved']
    
    def complaint_number(self, obj):
        url = reverse('admin:complaints_complaint_change', args=[obj.complaint.pk])
        return format_html('<a href="{}">{}</a>', url, obj.complaint.complaint_number)
    complaint_number.short_description = _('Complaint')
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            is_resolved=True, 
            resolved_by=request.user, 
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} reports marked as resolved.')
    mark_as_resolved.short_description = _('Mark selected reports as resolved')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('city', 'state', 'country', 'postal_code', 'complaint_count')
    list_filter = ('country', 'state')
    search_fields = ('city', 'state', 'country', 'area', 'postal_code')
    
    def complaint_count(self, obj):
        return obj.complaints.count()
    complaint_count.short_description = _('Complaints')


@admin.register(ComplaintTag)
class ComplaintTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_display', 'is_active', 'complaint_count')
    list_filter = ('is_active',)
    search_fields = ('name',)
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; color: white; border-radius: 3px;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = _('Color')
    
    def complaint_count(self, obj):
        return obj.complaints.count()
    complaint_count.short_description = _('Usage Count')


# Register remaining models with basic admin
admin.site.register(ComplaintSubCategory)
admin.site.register(ComplaintAttachment)
admin.site.register(ComplaintCommentReaction)
admin.site.register(ComplaintStatusHistory)
admin.site.register(ComplaintShare)
admin.site.register(ComplaintFollower)


# Customize admin site header
admin.site.site_header = _('CivicVoice Administration')
admin.site.site_title = _('CivicVoice Admin')
admin.site.index_title = _('Welcome to CivicVoice Administration')
