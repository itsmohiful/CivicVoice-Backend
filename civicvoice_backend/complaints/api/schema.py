import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.contrib.auth import get_user_model
from civicvoice_backend.complaints.models import (
    Complaint, ComplaintCategory, ComplaintSubCategory, ComplaintComment,
    ComplaintReaction, ComplaintTag, ComplaintAttachment, Location,
    ComplaintStatusHistory, ComplaintShare, ComplaintFollower, ComplaintReport
)
from civicvoice_backend.complaints.api.filters import (
    ComplaintFilter, ComplaintCategoryFilter, ComplaintCommentFilter,
    ComplaintReactionFilter, ComplaintAttachmentFilter, ComplaintSubCategoryFilter,
    ComplaintTagFilter, LocationFilter, ComplaintReportFilter, ComplaintStatusHistoryFilter
)

User = get_user_model()


class LocationObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)

    class Meta:
        model = Location
        fields = ['id', 'country', 'state', 'city', 'area', 'postal_code', 
                 'address', 'latitude', 'longitude']
        filterset_class = LocationFilter
        interfaces = (graphene.relay.Node,)


class ComplaintCategoryObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)
    complaint_count = graphene.Int()

    class Meta:
        model = ComplaintCategory
        fields = ['id', 'name', 'description', 'icon', 'color', 'is_active', 
                 'sort_order', 'department_email', 'department_phone', 'escalation_days']
        filterset_class = ComplaintCategoryFilter
        interfaces = (graphene.relay.Node,)

    def resolve_complaint_count(self, info):
        return self.complaints.filter(is_deleted=False).count()


class ComplaintSubCategoryObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)

    class Meta:
        model = ComplaintSubCategory
        fields = ['id', 'name', 'description', 'is_active', 'sort_order', 'category']
        filterset_class = ComplaintSubCategoryFilter
        interfaces = (graphene.relay.Node,)


class ComplaintTagObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)

    class Meta:
        model = ComplaintTag
        fields = ['id', 'name', 'color', 'is_active']
        filterset_class = ComplaintTagFilter
        interfaces = (graphene.relay.Node,)


class ComplaintAttachmentObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)
    file_url = graphene.String()

    class Meta:
        model = ComplaintAttachment
        fields = ['id', 'original_name', 'file_size', 'file_type', 'description', 'created_at']
        filterset_class = ComplaintAttachmentFilter
        interfaces = (graphene.relay.Node,)

    def resolve_file_url(self, info):
        if self.file:
            return info.context.build_absolute_uri(self.file.url)
        return None


class ComplaintReactionObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)

    class Meta:
        model = ComplaintReaction
        fields = ['id', 'reaction_type', 'user', 'created_at']
        filterset_class = ComplaintReactionFilter
        interfaces = (graphene.relay.Node,)


class ComplaintCommentObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)
    author_name = graphene.String()
    replies_count = graphene.Int()

    class Meta:
        model = ComplaintComment
        fields = ['id', 'content', 'is_official', 'is_anonymous', 'created_by', 
                 'parent', 'created_at', 'updated_at']
        filterset_class = ComplaintCommentFilter
        interfaces = (graphene.relay.Node,)

    def resolve_author_name(self, info):
        if self.is_anonymous:
            return "Anonymous"
        return self.created_by.name if self.created_by else "Unknown"

    def resolve_replies_count(self, info):
        return self.replies.filter(is_deleted=False).count()


class ComplaintStatusHistoryObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)

    class Meta:
        model = ComplaintStatusHistory
        fields = ['id', 'previous_status', 'new_status', 'reason', 'changed_by', 'created_at']
        filterset_class = ComplaintStatusHistoryFilter
        interfaces = (graphene.relay.Node,)


class ComplaintObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)
    can_edit = graphene.Boolean()
    can_view = graphene.Boolean()
    is_following = graphene.Boolean()
    user_reaction = graphene.Field(ComplaintReactionObjectType)
    reaction_counts = graphene.JSONString()
    is_overdue = graphene.Boolean()
    comments = DjangoFilterConnectionField(ComplaintCommentObjectType)
    attachments = DjangoFilterConnectionField(ComplaintAttachmentObjectType)
    reactions = DjangoFilterConnectionField(ComplaintReactionObjectType)
    status_history = DjangoFilterConnectionField(ComplaintStatusHistoryObjectType)

    class Meta:
        model = Complaint
        fields = [
            'id', 'title', 'description', 'complaint_number', 'status', 'priority',
            'privacy', 'allow_comments', 'allow_sharing', 'location', 'category',
            'subcategory', 'tags', 'incident_date', 'submitted_at', 'due_date',
            'resolved_at', 'view_count', 'reaction_count', 'comment_count',
            'share_count', 'created_by', 'assigned_to', 'reference_number',
            'escalated_from', 'escalation_reason', 'created_at', 'updated_at'
        ]
        filterset_class = ComplaintFilter
        interfaces = (graphene.relay.Node,)

    def resolve_can_edit(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return False
        return self.can_edit(user)

    def resolve_can_view(self, info):
        user = info.context.user
        return self.can_view(user if user.is_authenticated else None)

    def resolve_is_following(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return False
        return self.followers.filter(user=user).exists()

    def resolve_user_reaction(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return None
        return self.reactions.filter(user=user).first()

    def resolve_reaction_counts(self, info):
        from django.db.models import Count
        reaction_counts = self.reactions.values('reaction_type').annotate(
            count=Count('id')
        )
        return {r['reaction_type']: r['count'] for r in reaction_counts}

    def resolve_is_overdue(self, info):
        return self.is_overdue

    def resolve_comments(self, info, **kwargs):
        return self.comments.filter(parent__isnull=True, is_deleted=False).order_by('created_at')

    def resolve_attachments(self, info, **kwargs):
        return self.attachments.filter(is_deleted=False).order_by('created_at')

    def resolve_reactions(self, info, **kwargs):
        return self.reactions.all().order_by('-created_at')

    def resolve_status_history(self, info, **kwargs):
        return self.status_history.all().order_by('-created_at')


class ComplaintFollowerObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)

    class Meta:
        model = ComplaintFollower
        fields = ['id', 'user', 'notify_status_change', 'notify_new_comment', 
                 'notify_resolution', 'created_at']
        interfaces = (graphene.relay.Node,)


class ComplaintReportObjectType(DjangoObjectType):
    id = graphene.ID(source='pk', required=True)

    class Meta:
        model = ComplaintReport
        fields = ['id', 'reason', 'description', 'is_resolved', 'reported_by',
                 'resolved_by', 'resolved_at', 'created_at']
        filterset_class = ComplaintReportFilter
        interfaces = (graphene.relay.Node,)
