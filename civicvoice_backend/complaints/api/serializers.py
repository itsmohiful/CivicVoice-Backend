from rest_framework import serializers
from django.contrib.auth import get_user_model
from civicvoice_backend.complaints.models import (
    ComplaintCategory, ComplaintSubCategory, ComplaintTag, Location,
    Complaint, ComplaintComment, ComplaintReaction, ComplaintAttachment,
    ComplaintShare, ComplaintFollower, ComplaintReport, ComplaintStatusHistory
)
from civicvoice_backend.users.api.serializers import UserSerializer

User = get_user_model()


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model"""
    
    class Meta:
        model = Location
        fields = [
            'id', 'country', 'state', 'city', 'area', 'postal_code',
            'address', 'latitude', 'longitude', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplaintCategorySerializer(serializers.ModelSerializer):
    """Serializer for ComplaintCategory model"""
    complaint_count = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplaintCategory
        fields = [
            'id', 'name', 'description', 'icon', 'color', 'is_active',
            'sort_order', 'department_email', 'department_phone',
            'escalation_days', 'complaint_count', 'subcategories',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'complaint_count', 'subcategories']
    
    def get_complaint_count(self, obj):
        return obj.complaints.filter(is_deleted=False).count()
    
    def get_subcategories(self, obj):
        subcategories = obj.subcategories.filter(is_active=True, is_deleted=False)
        return ComplaintSubCategorySerializer(subcategories, many=True).data


class ComplaintSubCategorySerializer(serializers.ModelSerializer):
    """Serializer for ComplaintSubCategory model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ComplaintSubCategory
        fields = [
            'id', 'category', 'category_name', 'name', 'description',
            'is_active', 'sort_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'category_name']


class ComplaintTagSerializer(serializers.ModelSerializer):
    """Serializer for ComplaintTag model"""
    
    class Meta:
        model = ComplaintTag
        fields = [
            'id', 'name', 'color', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplaintAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for ComplaintAttachment model"""
    file_url = serializers.SerializerMethodField()
    complaint_number = serializers.CharField(source='complaint.complaint_number', read_only=True)
    
    class Meta:
        model = ComplaintAttachment
        fields = [
            'id', 'complaint', 'complaint_number', 'file', 'file_url',
            'original_name', 'file_size', 'file_type', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'file_url', 'complaint_number']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def validate_file(self, value):
        """Validate file upload"""
        if value:
            # Check file size (max 10MB)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("File size cannot exceed 10MB")
            
            # Store file metadata
            if hasattr(value, 'name'):
                self.validated_file_data = {
                    'original_name': value.name,
                    'file_size': value.size,
                    'file_type': value.content_type if hasattr(value, 'content_type') else 'unknown'
                }
        return value
    
    def create(self, validated_data):
        # Add file metadata if available
        if hasattr(self, 'validated_file_data'):
            validated_data.update(self.validated_file_data)
        return super().create(validated_data)


class ComplaintReactionSerializer(serializers.ModelSerializer):
    """Serializer for ComplaintReaction model"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    complaint_number = serializers.CharField(source='complaint.complaint_number', read_only=True)
    
    class Meta:
        model = ComplaintReaction
        fields = [
            'id', 'complaint', 'complaint_number', 'user', 'user_name',
            'reaction_type', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_name', 'complaint_number']
    
    def create(self, validated_data):
        # Set the user from request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ComplaintCommentSerializer(serializers.ModelSerializer):
    """Serializer for ComplaintComment model"""
    author_name = serializers.SerializerMethodField()
    complaint_number = serializers.CharField(source='complaint.complaint_number', read_only=True)
    replies = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplaintComment
        fields = [
            'id', 'complaint', 'complaint_number', 'content', 'is_official',
            'is_anonymous', 'created_by', 'author_name', 'parent',
            'replies', 'replies_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'author_name',
            'complaint_number', 'replies', 'replies_count'
        ]
    
    def get_author_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.created_by.name if obj.created_by else "Unknown"
    
    def get_replies(self, obj):
        if obj.replies.exists():
            replies = obj.replies.filter(is_deleted=False).order_by('created_at')
            return ComplaintCommentSerializer(replies, many=True, context=self.context).data
        return []
    
    def get_replies_count(self, obj):
        return obj.replies.filter(is_deleted=False).count()
    
    def create(self, validated_data):
        # Set the user from request
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ComplaintStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for ComplaintStatusHistory model"""
    complaint_number = serializers.CharField(source='complaint.complaint_number', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.name', read_only=True)
    previous_status_display = serializers.CharField(source='get_previous_status_display', read_only=True)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)
    
    class Meta:
        model = ComplaintStatusHistory
        fields = [
            'id', 'complaint', 'complaint_number', 'previous_status',
            'previous_status_display', 'new_status', 'new_status_display',
            'reason', 'changed_by', 'changed_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'complaint_number', 'changed_by_name',
            'previous_status_display', 'new_status_display'
        ]


class ComplaintShareSerializer(serializers.ModelSerializer):
    """Serializer for ComplaintShare model"""
    shared_by_name = serializers.CharField(source='shared_by.name', read_only=True)
    complaint_number = serializers.CharField(source='complaint.complaint_number', read_only=True)
    
    class Meta:
        model = ComplaintShare
        fields = [
            'id', 'complaint', 'complaint_number', 'shared_by',
            'shared_by_name', 'platform', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'shared_by_name', 'complaint_number']
    
    def create(self, validated_data):
        # Set the user from request
        validated_data['shared_by'] = self.context['request'].user
        return super().create(validated_data)


class ComplaintFollowerSerializer(serializers.ModelSerializer):
    """Serializer for ComplaintFollower model"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    complaint_number = serializers.CharField(source='complaint.complaint_number', read_only=True)
    
    class Meta:
        model = ComplaintFollower
        fields = [
            'id', 'complaint', 'complaint_number', 'user', 'user_name',
            'notify_status_change', 'notify_new_comment', 'notify_resolution',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_name', 'complaint_number']
    
    def create(self, validated_data):
        # Set the user from request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ComplaintReportSerializer(serializers.ModelSerializer):
    """Serializer for ComplaintReport model"""
    reported_by_name = serializers.CharField(source='reported_by.name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.name', read_only=True)
    complaint_number = serializers.CharField(source='complaint.complaint_number', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    
    class Meta:
        model = ComplaintReport
        fields = [
            'id', 'complaint', 'complaint_number', 'reported_by',
            'reported_by_name', 'reason', 'reason_display', 'description',
            'is_resolved', 'resolved_by', 'resolved_by_name', 'resolved_at',
            'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'reported_by_name', 'resolved_by_name',
            'complaint_number', 'reason_display'
        ]
    
    def create(self, validated_data):
        # Set the user from request
        validated_data['reported_by'] = self.context['request'].user
        return super().create(validated_data)


class ComplaintSerializer(serializers.ModelSerializer):
    """Serializer for Complaint model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    location_display = serializers.SerializerMethodField()
    tags_display = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    privacy_display = serializers.CharField(source='get_privacy_display', read_only=True)
    
    # Related data
    attachments = ComplaintAttachmentSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    reactions = ComplaintReactionSerializer(many=True, read_only=True)
    status_history = ComplaintStatusHistorySerializer(many=True, read_only=True)
    
    # Simplified file upload field
    attachment_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        help_text="List of files to attach to the complaint"
    )
    
    # Computed fields
    can_edit = serializers.SerializerMethodField()
    can_view = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    reaction_counts = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Complaint
        fields = [
            'id', 'title', 'description', 'complaint_number', 'status',
            'status_display', 'priority', 'priority_display', 'privacy',
            'privacy_display', 'allow_comments', 'allow_sharing',
            'location', 'location_display', 'category', 'category_name',
            'subcategory', 'subcategory_name', 'tags', 'tags_display',
            'incident_date', 'submitted_at', 'due_date', 'resolved_at',
            'view_count', 'reaction_count', 'comment_count', 'share_count',
            'created_by', 'created_by_name', 'assigned_to', 'assigned_to_name',
            'reference_number', 'escalated_from', 'escalation_reason',
            'created_at', 'updated_at',
            # Related data
            'attachments', 'comments', 'reactions', 'status_history',
            # File upload field
            'attachment_files',
            # Computed fields
            'can_edit', 'can_view', 'is_following', 'user_reaction',
            'reaction_counts', 'is_overdue'
        ]
        read_only_fields = [
            'id', 'complaint_number', 'submitted_at', 'view_count',
            'reaction_count', 'comment_count', 'share_count', 'created_at',
            'updated_at', 'category_name', 'subcategory_name', 'location_display',
            'tags_display', 'created_by_name', 'assigned_to_name',
            'status_display', 'priority_display', 'privacy_display',
            'attachments', 'comments', 'reactions', 'status_history',
            'can_edit', 'can_view', 'is_following', 'user_reaction',
            'reaction_counts', 'is_overdue'
        ]
    
    def validate_attachment_files(self, files):
        """Validate uploaded files"""
        if len(files) > 10:  # Maximum 10 files per complaint
            raise serializers.ValidationError("Maximum 10 files allowed per complaint")
        
        for file in files:
            # Check file size (max 10MB per file)
            if file.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(f"File '{file.name}' exceeds 10MB limit")
        
        return files
    
    def get_location_display(self, obj):
        if obj.location:
            return f"{obj.location.area}, {obj.location.city}, {obj.location.state}"
        return None
    
    def get_tags_display(self, obj):
        return [tag.name for tag in obj.tags.all()]
    
    def get_comments(self, obj):
        comments = obj.comments.filter(parent__isnull=True, is_deleted=False).order_by('created_at')
        return ComplaintCommentSerializer(comments, many=True, context=self.context).data
    
    def get_can_edit(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.can_edit(user)
    
    def get_can_view(self, obj):
        user = self.context['request'].user
        return obj.can_view(user if user.is_authenticated else None)
    
    def get_is_following(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.followers.filter(user=user).exists()
    
    def get_user_reaction(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return None
        reaction = obj.reactions.filter(user=user).first()
        return ComplaintReactionSerializer(reaction).data if reaction else None
    
    def get_reaction_counts(self, obj):
        from django.db.models import Count
        reaction_counts = obj.reactions.values('reaction_type').annotate(
            count=Count('id')
        )
        return {r['reaction_type']: r['count'] for r in reaction_counts}
    
    def get_is_overdue(self, obj):
        return obj.is_overdue
    
    def create(self, validated_data):
        # Extract attachment files
        attachment_files = validated_data.pop('attachment_files', [])
        
        # Set the user from request
        validated_data['created_by'] = self.context['request'].user
        
        # Remove tags from validated_data if present (will be set separately)
        tags_data = validated_data.pop('tags', [])
        
        # Create the complaint
        complaint = super().create(validated_data)
        
        # Set tags if provided
        if tags_data:
            complaint.tags.set(tags_data)
        
        # Create attachments if files were uploaded
        if attachment_files:
            self._create_attachments(complaint, attachment_files)
        
        return complaint
    
    def _create_attachments(self, complaint, files):
        """Create attachment objects for uploaded files"""
        for file in files:
            # Create attachment with minimal data
            ComplaintAttachment.objects.create(
                complaint=complaint,
                file=file,
                original_name=file.name,
                file_size=file.size,
                file_type=getattr(file, 'content_type', 'unknown'),
                created_by=complaint.created_by
            )


# Summary/List serializers for better performance
class ComplaintListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for complaint lists"""
    # category_name = serializers.CharField(source='category.name', read_only=True)
    # location_display = serializers.SerializerMethodField()
    # status_display = serializers.CharField(source='get_status_display', read_only=True)
    # priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    # created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    # created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    # category = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = UserSerializer(read_only=True)
    category = ComplaintCategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    tags = ComplaintTagSerializer(many=True, read_only=True)

   
    class Meta:
        model = Complaint
        fields = '__all__'
       
    
    def get_location_display(self, obj):
        if obj.location:
            return f"{obj.location.area}, {obj.location.city}"
        return None


class ComplaintCreateSerializer(serializers.ModelSerializer):
    """Specialized serializer for creating complaints with attachments"""
    # Simplified file upload field
    attachment_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        help_text="List of files to attach to the complaint (max 10 files, 10MB each)"
    )
    
    # Read-only fields for response
    complaint_number = serializers.CharField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    attachments = ComplaintAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Complaint
        fields = [
            # Basic fields
            'id', 'title', 'description', 'complaint_number', 'status',
            'priority', 'privacy', 'allow_comments', 'allow_sharing',
            'category', 'category_name', 'subcategory', 'subcategory_name',
            'tags', 'location', 'incident_date', 'reference_number',
            # File upload field
            'attachment_files',
            # Response fields
            'created_by', 'created_by_name', 'attachments',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'complaint_number', 'created_by', 'created_by_name',
            'category_name', 'subcategory_name', 'attachments',
            'created_at', 'updated_at'
        ]
    
    def validate_attachment_files(self, files):
        """Validate uploaded files"""
        if len(files) > 10:
            raise serializers.ValidationError("Maximum 10 files allowed per complaint")
        
        total_size = 0
        for file in files:
            # Check individual file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(f"File '{file.name}' exceeds 10MB limit")
            
            total_size += file.size
            
            # Check total size (max 50MB total)
            if total_size > 50 * 1024 * 1024:
                raise serializers.ValidationError("Total file size cannot exceed 50MB")
        
        return files
    
    def create(self, validated_data):
        # Extract attachment files
        attachment_files = validated_data.pop('attachment_files', [])
        
        # Set the user from request
        validated_data['created_by'] = self.context['request'].user
        
        # Remove tags from validated_data if present (will be set separately)
        tags_data = validated_data.pop('tags', [])
        
        # Create the complaint
        complaint = super().create(validated_data)
        
        # Set tags if provided
        if tags_data:
            complaint.tags.set(tags_data)
        
        # Create attachments if files were uploaded
        if attachment_files:
            self._create_attachments(complaint, attachment_files)
        
        return complaint
    
    def _create_attachments(self, complaint, files):
        """Create attachment objects for uploaded files"""
        attachments = []
        for file in files:
            # Create attachment with minimal required data
            attachment = ComplaintAttachment.objects.create(
                complaint=complaint,
                file=file,
                original_name=file.name,
                file_size=file.size,
                file_type=getattr(file, 'content_type', 'unknown'),
                created_by=complaint.created_by
            )
            attachments.append(attachment)
        
        return attachments
