import graphene
from graphql import GraphQLError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied

from civicvoice_backend.complaints.models import (
    Complaint, ComplaintCategory, ComplaintSubCategory, ComplaintComment,
    ComplaintReaction, ComplaintTag, ComplaintAttachment, Location,
    ComplaintStatusHistory, ComplaintShare, ComplaintFollower, ComplaintReport,
    ComplaintStatus, ComplaintPrivacy, ComplaintPriority
)
from civicvoice_backend.complaints.api.schema import (
    ComplaintObjectType, ComplaintCategoryObjectType, ComplaintSubCategoryObjectType,
    ComplaintCommentObjectType, ComplaintReactionObjectType, ComplaintTagObjectType,
    ComplaintAttachmentObjectType, LocationObjectType, ComplaintFollowerObjectType,
    ComplaintReportObjectType
)
from civicvoice_backend.complaints.api.inputs import (
    CreateComplaintInput, UpdateComplaintInput, AdminUpdateComplaintInput,
    CreateCommentInput, UpdateCommentInput, ReactToComplaintInput,
    FollowComplaintInput, ReportComplaintInput, ShareComplaintInput,
    UploadAttachmentInput, CreateCategoryInput, UpdateCategoryInput,
    CreateSubCategoryInput, CreateTagInput, BulkActionInput
)

User = get_user_model()


class CreateComplaintMutation(graphene.Mutation):
    """Create a new complaint"""
    
    class Arguments:
        input = CreateComplaintInput(required=True)
    
    complaint = graphene.Field(ComplaintObjectType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, input):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        try:
            with transaction.atomic():
                # Validate category and subcategory
                try:
                    category = ComplaintCategory.objects.get(
                        id=input.category_id, 
                        is_active=True, 
                        is_deleted=False
                    )
                except ComplaintCategory.DoesNotExist:
                    raise GraphQLError("Invalid category")
                
                subcategory = None
                if input.subcategory_id:
                    try:
                        subcategory = ComplaintSubCategory.objects.get(
                            id=input.subcategory_id,
                            category=category,
                            is_active=True,
                            is_deleted=False
                        )
                    except ComplaintSubCategory.DoesNotExist:
                        raise GraphQLError("Invalid subcategory")
                
                # Create location if provided
                location = None
                if input.location:
                    location = Location.objects.create(
                        country=input.location.country,
                        state=input.location.state,
                        city=input.location.city,
                        area=input.location.area or '',
                        postal_code=input.location.postal_code or '',
                        address=input.location.address or '',
                        latitude=input.location.latitude,
                        longitude=input.location.longitude,
                        created_by=user
                    )
                
                # Create complaint
                complaint = Complaint.objects.create(
                    title=input.title,
                    description=input.description,
                    category=category,
                    subcategory=subcategory,
                    priority=input.priority,
                    privacy=input.privacy,
                    allow_comments=input.allow_comments,
                    allow_sharing=input.allow_sharing,
                    incident_date=input.incident_date,
                    location=location,
                    created_by=user,
                    status=ComplaintStatus.DRAFT
                )
                
                # Add tags
                if input.tag_ids:
                    tags = ComplaintTag.objects.filter(
                        id__in=input.tag_ids,
                        is_active=True,
                        is_deleted=False
                    )
                    complaint.tags.set(tags)
                
                return CreateComplaintMutation(
                    complaint=complaint,
                    success=True,
                    message="Complaint created successfully"
                )
                
        except ValidationError as e:
            raise GraphQLError(str(e))
        except Exception as e:
            raise GraphQLError(f"Error creating complaint: {str(e)}")


class UpdateComplaintMutation(graphene.Mutation):
    """Update an existing complaint"""
    
    class Arguments:
        complaint_number = graphene.String(required=True)
        input = UpdateComplaintInput(required=True)
    
    complaint = graphene.Field(ComplaintObjectType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, complaint_number, input):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                is_deleted=False
            )
            
            if not complaint.can_edit(user):
                raise GraphQLError("You don't have permission to edit this complaint")
            
            with transaction.atomic():
                # Update fields
                if input.title is not None:
                    complaint.title = input.title
                if input.description is not None:
                    complaint.description = input.description
                if input.priority is not None:
                    complaint.priority = input.priority
                if input.privacy is not None:
                    complaint.privacy = input.privacy
                if input.allow_comments is not None:
                    complaint.allow_comments = input.allow_comments
                if input.allow_sharing is not None:
                    complaint.allow_sharing = input.allow_sharing
                if input.incident_date is not None:
                    complaint.incident_date = input.incident_date
                
                # Update category and subcategory
                if input.category_id:
                    try:
                        category = ComplaintCategory.objects.get(
                            id=input.category_id,
                            is_active=True,
                            is_deleted=False
                        )
                        complaint.category = category
                    except ComplaintCategory.DoesNotExist:
                        raise GraphQLError("Invalid category")
                
                if input.subcategory_id:
                    try:
                        subcategory = ComplaintSubCategory.objects.get(
                            id=input.subcategory_id,
                            category=complaint.category,
                            is_active=True,
                            is_deleted=False
                        )
                        complaint.subcategory = subcategory
                    except ComplaintSubCategory.DoesNotExist:
                        raise GraphQLError("Invalid subcategory")
                
                # Update tags
                if input.tag_ids is not None:
                    tags = ComplaintTag.objects.filter(
                        id__in=input.tag_ids,
                        is_active=True,
                        is_deleted=False
                    )
                    complaint.tags.set(tags)
                
                complaint.updated_by = user
                complaint.save()
                
                return UpdateComplaintMutation(
                    complaint=complaint,
                    success=True,
                    message="Complaint updated successfully"
                )
                
        except Complaint.DoesNotExist:
            raise GraphQLError("Complaint not found")
        except Exception as e:
            raise GraphQLError(f"Error updating complaint: {str(e)}")


class SubmitComplaintMutation(graphene.Mutation):
    """Submit a complaint (change status from draft to submitted)"""
    
    class Arguments:
        complaint_number = graphene.String(required=True)
    
    complaint = graphene.Field(ComplaintObjectType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, complaint_number):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                created_by=user,
                is_deleted=False
            )
            
            if complaint.status != ComplaintStatus.DRAFT:
                raise GraphQLError("Only draft complaints can be submitted")
            
            complaint.status = ComplaintStatus.SUBMITTED
            complaint.submitted_at = timezone.now()
            complaint.save()
            
            return SubmitComplaintMutation(
                complaint=complaint,
                success=True,
                message="Complaint submitted successfully"
            )
            
        except Complaint.DoesNotExist:
            raise GraphQLError("Complaint not found")


class AdminUpdateComplaintMutation(graphene.Mutation):
    """Admin/Staff update complaint status and assignment"""
    
    class Arguments:
        complaint_number = graphene.String(required=True)
        input = AdminUpdateComplaintInput(required=True)
    
    complaint = graphene.Field(ComplaintObjectType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, complaint_number, input):
        user = info.context.user
        if not user.is_authenticated or not (user.is_staff or user.is_superuser):
            raise GraphQLError("Admin access required")
        
        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                is_deleted=False
            )
            
            with transaction.atomic():
                # Track status change
                if input.status and complaint.status != input.status:
                    ComplaintStatusHistory.objects.create(
                        complaint=complaint,
                        previous_status=complaint.status,
                        new_status=input.status,
                        reason=input.reason or '',
                        changed_by=user
                    )
                    complaint.status = input.status
                
                # Update assignment
                if input.assigned_to_id:
                    try:
                        assigned_user = User.objects.get(
                            id=input.assigned_to_id,
                            is_active=True
                        )
                        complaint.assigned_to = assigned_user
                    except User.DoesNotExist:
                        raise GraphQLError("Invalid assigned user")
                
                # Update reference number
                if input.reference_number is not None:
                    complaint.reference_number = input.reference_number
                
                complaint.updated_by = user
                complaint.save()
                
                return AdminUpdateComplaintMutation(
                    complaint=complaint,
                    success=True,
                    message="Complaint updated successfully"
                )
                
        except Complaint.DoesNotExist:
            raise GraphQLError("Complaint not found")


class CreateCommentMutation(graphene.Mutation):
    """Add a comment to a complaint"""
    
    class Arguments:
        complaint_number = graphene.String(required=True)
        input = CreateCommentInput(required=True)
    
    comment = graphene.Field(ComplaintCommentObjectType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, complaint_number, input):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                is_deleted=False
            )
            
            if not complaint.allow_comments:
                raise GraphQLError("Comments are not allowed on this complaint")
            
            # Check if it's a reply to another comment
            parent_comment = None
            if input.parent_id:
                try:
                    parent_comment = ComplaintComment.objects.get(
                        id=input.parent_id,
                        complaint=complaint,
                        is_deleted=False
                    )
                except ComplaintComment.DoesNotExist:
                    raise GraphQLError("Parent comment not found")
            
            comment = ComplaintComment.objects.create(
                complaint=complaint,
                parent=parent_comment,
                content=input.content,
                is_anonymous=input.is_anonymous,
                is_official=input.is_official and (user.is_staff or user.is_superuser),
                created_by=user
            )
            
            return CreateCommentMutation(
                comment=comment,
                success=True,
                message="Comment added successfully"
            )
            
        except Complaint.DoesNotExist:
            raise GraphQLError("Complaint not found")


class ReactToComplaintMutation(graphene.Mutation):
    """React to a complaint (like, support, etc.)"""
    
    class Arguments:
        complaint_number = graphene.String(required=True)
        input = ReactToComplaintInput(required=True)
    
    reaction = graphene.Field(ComplaintReactionObjectType)
    success = graphene.Boolean()
    message = graphene.String()
    action = graphene.String()  # 'added', 'updated', 'removed'
    
    @staticmethod
    def mutate(root, info, complaint_number, input):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                is_deleted=False
            )
            
            with transaction.atomic():
                reaction, created = ComplaintReaction.objects.get_or_create(
                    complaint=complaint,
                    user=user,
                    defaults={'reaction_type': input.reaction_type}
                )
                
                if not created:
                    if reaction.reaction_type == input.reaction_type:
                        # Remove reaction if same type
                        reaction.delete()
                        return ReactToComplaintMutation(
                            reaction=None,
                            success=True,
                            message="Reaction removed",
                            action="removed"
                        )
                    else:
                        # Update reaction type
                        reaction.reaction_type = input.reaction_type
                        reaction.save()
                        action = "updated"
                else:
                    action = "added"
                
                return ReactToComplaintMutation(
                    reaction=reaction,
                    success=True,
                    message=f"Reaction {action} successfully",
                    action=action
                )
                
        except Complaint.DoesNotExist:
            raise GraphQLError("Complaint not found")


class FollowComplaintMutation(graphene.Mutation):
    """Follow/unfollow a complaint"""
    
    class Arguments:
        complaint_number = graphene.String(required=True)
        input = FollowComplaintInput()
    
    follower = graphene.Field(ComplaintFollowerObjectType)
    success = graphene.Boolean()
    message = graphene.String()
    following = graphene.Boolean()
    
    @staticmethod
    def mutate(root, info, complaint_number, input=None):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                is_deleted=False
            )
            
            follower, created = ComplaintFollower.objects.get_or_create(
                complaint=complaint,
                user=user,
                defaults={
                    'notify_status_change': input.notify_status_change if input else True,
                    'notify_new_comment': input.notify_new_comment if input else True,
                    'notify_resolution': input.notify_resolution if input else True,
                }
            )
            
            if not created:
                # If already following, unfollow
                follower.delete()
                return FollowComplaintMutation(
                    follower=None,
                    success=True,
                    message="Unfollowed complaint",
                    following=False
                )
            
            return FollowComplaintMutation(
                follower=follower,
                success=True,
                message="Following complaint",
                following=True
            )
            
        except Complaint.DoesNotExist:
            raise GraphQLError("Complaint not found")


class ShareComplaintMutation(graphene.Mutation):
    """Share a complaint"""
    
    class Arguments:
        complaint_number = graphene.String(required=True)
        input = ShareComplaintInput()
    
    success = graphene.Boolean()
    message = graphene.String()
    share_count = graphene.Int()
    
    @staticmethod
    def mutate(root, info, complaint_number, input=None):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                is_deleted=False
            )
            
            if not complaint.allow_sharing:
                raise GraphQLError("Sharing is not allowed for this complaint")
            
            share, created = ComplaintShare.objects.get_or_create(
                complaint=complaint,
                shared_by=user,
                defaults={'platform': input.platform if input else ''}
            )
            
            return ShareComplaintMutation(
                success=True,
                message="Complaint shared successfully",
                share_count=complaint.shares.count()
            )
            
        except Complaint.DoesNotExist:
            raise GraphQLError("Complaint not found")


class ReportComplaintMutation(graphene.Mutation):
    """Report a complaint for inappropriate content"""
    
    class Arguments:
        complaint_number = graphene.String(required=True)
        input = ReportComplaintInput(required=True)
    
    report = graphene.Field(ComplaintReportObjectType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, complaint_number, input):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                is_deleted=False
            )
            
            # Check if user already reported this complaint
            existing_report = ComplaintReport.objects.filter(
                complaint=complaint,
                reported_by=user
            ).first()
            
            if existing_report:
                raise GraphQLError("You have already reported this complaint")
            
            report = ComplaintReport.objects.create(
                complaint=complaint,
                reported_by=user,
                reason=input.reason,
                description=input.description or ''
            )
            
            return ReportComplaintMutation(
                report=report,
                success=True,
                message="Complaint reported successfully"
            )
            
        except Complaint.DoesNotExist:
            raise GraphQLError("Complaint not found")


class DeleteComplaintMutation(graphene.Mutation):
    """Soft delete a complaint"""
    
    class Arguments:
        complaint_number = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, complaint_number):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        try:
            complaint = Complaint.objects.get(
                complaint_number=complaint_number,
                is_deleted=False
            )
            
            # Only owner or admin can delete
            if complaint.created_by != user and not (user.is_staff or user.is_superuser):
                raise GraphQLError("You don't have permission to delete this complaint")
            
            complaint.soft_delete()
            
            return DeleteComplaintMutation(
                success=True,
                message="Complaint deleted successfully"
            )
            
        except Complaint.DoesNotExist:
            raise GraphQLError("Complaint not found")


# Category Management Mutations
class CreateCategoryMutation(graphene.Mutation):
    """Create a new complaint category (admin only)"""
    
    class Arguments:
        input = CreateCategoryInput(required=True)
    
    category = graphene.Field(ComplaintCategoryObjectType)
    success = graphene.Boolean()
    message = graphene.String()
    
    @staticmethod
    def mutate(root, info, input):
        user = info.context.user
        if not user.is_authenticated or not (user.is_staff or user.is_superuser):
            raise GraphQLError("Admin access required")
        
        try:
            category = ComplaintCategory.objects.create(
                name=input.name,
                description=input.description or '',
                icon=input.icon or '',
                color=input.color,
                department_email=input.department_email or '',
                department_phone=input.department_phone or '',
                escalation_days=input.escalation_days,
                sort_order=input.sort_order,
                created_by=user
            )
            
            return CreateCategoryMutation(
                category=category,
                success=True,
                message="Category created successfully"
            )
            
        except Exception as e:
            raise GraphQLError(f"Error creating category: {str(e)}")


# Aggregate all mutations
class ComplaintMutation(graphene.ObjectType):
    """All complaint-related mutations"""
    
    # Complaint mutations
    create_complaint = CreateComplaintMutation.Field()
    update_complaint = UpdateComplaintMutation.Field()
    submit_complaint = SubmitComplaintMutation.Field()
    admin_update_complaint = AdminUpdateComplaintMutation.Field()
    delete_complaint = DeleteComplaintMutation.Field()
    
    # Interaction mutations
    create_comment = CreateCommentMutation.Field()
    react_to_complaint = ReactToComplaintMutation.Field()
    follow_complaint = FollowComplaintMutation.Field()
    share_complaint = ShareComplaintMutation.Field()
    report_complaint = ReportComplaintMutation.Field()
    
    # Category management
    create_category = CreateCategoryMutation.Field()


complaint_schema_mutation = graphene.Schema(mutation=ComplaintMutation)
