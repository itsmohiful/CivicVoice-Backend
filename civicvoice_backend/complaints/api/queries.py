import graphene
from graphene_django.filter import DjangoFilterConnectionField
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg
from graphql import GraphQLError

from civicvoice_backend.complaints.models import (
    Complaint, ComplaintCategory, ComplaintSubCategory, ComplaintComment,
    ComplaintReaction, ComplaintTag, ComplaintAttachment, Location,
    ComplaintStatusHistory, ComplaintShare, ComplaintFollower, ComplaintReport,
    ComplaintStatus, ComplaintPrivacy
)
from civicvoice_backend.complaints.api.schema import (
    ComplaintObjectType, ComplaintCategoryObjectType, ComplaintSubCategoryObjectType,
    ComplaintCommentObjectType, ComplaintReactionObjectType, ComplaintTagObjectType,
    ComplaintAttachmentObjectType, LocationObjectType, ComplaintStatusHistoryObjectType,
    ComplaintFollowerObjectType, ComplaintReportObjectType
)

User = get_user_model()


# Statistics types
class ComplaintStatsType(graphene.ObjectType):
    total_complaints = graphene.Int()
    resolved_complaints = graphene.Int()
    pending_complaints = graphene.Int()
    overdue_complaints = graphene.Int()
    resolution_rate = graphene.Float()
    average_resolution_time = graphene.Float()  # in days


class CategoryStatsType(graphene.ObjectType):
    category = graphene.Field(ComplaintCategoryObjectType)
    total_complaints = graphene.Int()
    resolved_complaints = graphene.Int()
    pending_complaints = graphene.Int()
    resolution_rate = graphene.Float()


class MonthlyStatsType(graphene.ObjectType):
    month = graphene.String()
    year = graphene.Int()
    total_complaints = graphene.Int()
    resolved_complaints = graphene.Int()
    pending_complaints = graphene.Int()


class ComplaintQuery(graphene.ObjectType):
    """GraphQL queries for the complaints system"""
    
    # Single object queries
    complaint = graphene.Field(ComplaintObjectType, complaint_number=graphene.String(required=True))
    complaint_category = graphene.Field(ComplaintCategoryObjectType, id=graphene.ID(required=True))
    complaint_subcategory = graphene.Field(ComplaintSubCategoryObjectType, id=graphene.ID(required=True))
    complaint_tag = graphene.Field(ComplaintTagObjectType, id=graphene.ID(required=True))
    location = graphene.Field(LocationObjectType, id=graphene.ID(required=True))
    
    # List queries with filtering
    complaints = DjangoFilterConnectionField(ComplaintObjectType)
    complaint_categories = DjangoFilterConnectionField(ComplaintCategoryObjectType)
    complaint_subcategories = DjangoFilterConnectionField(ComplaintSubCategoryObjectType)
    complaint_tags = DjangoFilterConnectionField(ComplaintTagObjectType)
    complaint_comments = DjangoFilterConnectionField(ComplaintCommentObjectType)
    complaint_reactions = DjangoFilterConnectionField(ComplaintReactionObjectType)
    complaint_attachments = DjangoFilterConnectionField(ComplaintAttachmentObjectType)
    locations = DjangoFilterConnectionField(LocationObjectType)
    
    # User-specific queries
    my_complaints = DjangoFilterConnectionField(ComplaintObjectType)
    my_followed_complaints = DjangoFilterConnectionField(ComplaintObjectType)
    my_reactions = DjangoFilterConnectionField(ComplaintReactionObjectType)
    my_comments = DjangoFilterConnectionField(ComplaintCommentObjectType)
    
    # Public complaints (for non-authenticated users)
    public_complaints = DjangoFilterConnectionField(ComplaintObjectType)
    
    # Analytics and statistics
    complaint_stats = graphene.Field(ComplaintStatsType)
    category_stats = graphene.List(CategoryStatsType)
    monthly_stats = graphene.List(MonthlyStatsType, year=graphene.Int())
    
    # Search functionality
    search_complaints = graphene.List(
        ComplaintObjectType,
        query=graphene.String(required=True),
        limit=graphene.Int(default_value=10)
    )
    
    # Admin queries
    reported_complaints = DjangoFilterConnectionField(ComplaintReportObjectType)
    overdue_complaints = DjangoFilterConnectionField(ComplaintObjectType)
    
    def resolve_complaint(self, info, complaint_number):
        """Get a single complaint by complaint number"""
        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                is_deleted=False
            )
            
            # Check if user can view this complaint
            user = info.context.user if info.context.user.is_authenticated else None
            if not complaint.can_view(user):
                raise GraphQLError("You don't have permission to view this complaint")
            
            return complaint
        except Complaint.DoesNotExist:
            raise GraphQLError("Complaint not found")
    
    def resolve_complaint_category(self, info, id):
        """Get a single complaint category"""
        try:
            return ComplaintCategory.objects.get(id=id, is_deleted=False)
        except ComplaintCategory.DoesNotExist:
            raise GraphQLError("Category not found")
    
    def resolve_complaint_subcategory(self, info, id):
        """Get a single complaint subcategory"""
        try:
            return ComplaintSubCategory.objects.get(id=id, is_deleted=False)
        except ComplaintSubCategory.DoesNotExist:
            raise GraphQLError("Subcategory not found")
    
    def resolve_complaint_tag(self, info, id):
        """Get a single complaint tag"""
        try:
            return ComplaintTag.objects.get(id=id, is_deleted=False)
        except ComplaintTag.DoesNotExist:
            raise GraphQLError("Tag not found")
    
    def resolve_location(self, info, id):
        """Get a single location"""
        try:
            return Location.objects.get(id=id, is_deleted=False)
        except Location.DoesNotExist:
            raise GraphQLError("Location not found")
    
    def resolve_complaints(self, info, **kwargs):
        """Get all complaints with proper filtering"""
        user = info.context.user
        
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            # Admin users can see all complaints
            return Complaint.objects.filter(is_deleted=False).order_by('-created_at')
        else:
            # Regular users can only see public and anonymous complaints
            return Complaint.objects.filter(
                privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS],
                status__in=[
                    ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW,
                    ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED
                ],
                is_deleted=False
            ).order_by('-created_at')
    
    def resolve_complaint_categories(self, info, **kwargs):
        """Get all active complaint categories"""
        return ComplaintCategory.objects.filter(
            is_active=True, 
            is_deleted=False
        ).order_by('sort_order', 'name')
    
    def resolve_complaint_subcategories(self, info, **kwargs):
        """Get all active complaint subcategories"""
        return ComplaintSubCategory.objects.filter(
            is_active=True,
            is_deleted=False
        ).order_by('category__sort_order', 'sort_order', 'name')
    
    def resolve_complaint_tags(self, info, **kwargs):
        """Get all active complaint tags"""
        return ComplaintTag.objects.filter(
            is_active=True,
            is_deleted=False
        ).order_by('name')
    
    def resolve_complaint_comments(self, info, **kwargs):
        """Get complaint comments"""
        return ComplaintComment.objects.filter(
            is_deleted=False,
            complaint__privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS]
        ).order_by('-created_at')
    
    def resolve_complaint_reactions(self, info, **kwargs):
        """Get complaint reactions"""
        return ComplaintReaction.objects.filter(
            is_deleted=False,
            complaint__privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS]
        ).order_by('-created_at')
    
    def resolve_complaint_attachments(self, info, **kwargs):
        """Get complaint attachments"""
        return ComplaintAttachment.objects.filter(
            is_deleted=False,
            complaint__privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS]
        ).order_by('-created_at')
    
    def resolve_locations(self, info, **kwargs):
        """Get all locations"""
        return Location.objects.filter(is_deleted=False).order_by('country', 'state', 'city')
    
    def resolve_my_complaints(self, info, **kwargs):
        """Get current user's complaints"""
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        return Complaint.objects.filter(
            created_by=user,
            is_deleted=False
        ).order_by('-created_at')
    
    def resolve_my_followed_complaints(self, info, **kwargs):
        """Get complaints followed by current user"""
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        followed_complaint_ids = ComplaintFollower.objects.filter(
            user=user
        ).values_list('complaint_id', flat=True)
        
        return Complaint.objects.filter(
            id__in=followed_complaint_ids,
            is_deleted=False
        ).order_by('-created_at')
    
    def resolve_my_reactions(self, info, **kwargs):
        """Get current user's reactions"""
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        return ComplaintReaction.objects.filter(
            user=user,
            is_deleted=False
        ).order_by('-created_at')
    
    def resolve_my_comments(self, info, **kwargs):
        """Get current user's comments"""
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        return ComplaintComment.objects.filter(
            created_by=user,
            is_deleted=False
        ).order_by('-created_at')
    
    def resolve_public_complaints(self, info, **kwargs):
        """Get public complaints for non-authenticated users"""
        return Complaint.objects.filter(
            privacy=ComplaintPrivacy.PUBLIC,
            status__in=[
                ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW,
                ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED
            ],
            is_deleted=False
        ).order_by('-created_at')
    
    def resolve_search_complaints(self, info, query, limit=10):
        """Search complaints by title, description, or complaint number"""
        if len(query.strip()) < 3:
            return []
        
        complaints = Complaint.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(complaint_number__icontains=query),
            privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS],
            is_deleted=False
        )[:limit]
        
        return complaints
    
    def resolve_reported_complaints(self, info, **kwargs):
        """Get reported complaints (admin only)"""
        user = info.context.user
        if not user.is_authenticated or not (user.is_staff or user.is_superuser):
            raise GraphQLError("Admin access required")
        
        return ComplaintReport.objects.filter(
            is_resolved=False,
            is_deleted=False
        ).order_by('-created_at')
    
    def resolve_overdue_complaints(self, info, **kwargs):
        """Get overdue complaints (admin only)"""
        from django.utils import timezone
        
        user = info.context.user
        if not user.is_authenticated or not (user.is_staff or user.is_superuser):
            raise GraphQLError("Admin access required")
        
        return Complaint.objects.filter(
            due_date__lt=timezone.now(),
            status__in=[
                ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW,
                ComplaintStatus.IN_PROGRESS
            ],
            is_deleted=False
        ).order_by('due_date')


complaint_schema_query = graphene.Schema(query=ComplaintQuery)
