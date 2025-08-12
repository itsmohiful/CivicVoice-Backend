import graphene
from graphene_file_upload.scalars import Upload
from django.core.exceptions import ValidationError


class LocationInput(graphene.InputObjectType):
    """Input for location information"""
    country = graphene.String(required=True)
    state = graphene.String(required=True)
    city = graphene.String(required=True)
    area = graphene.String()
    postal_code = graphene.String()
    address = graphene.String()
    latitude = graphene.Float()
    longitude = graphene.Float()


class CreateComplaintInput(graphene.InputObjectType):
    """Input for creating a new complaint"""
    title = graphene.String(required=True)
    description = graphene.String(required=True)
    category_id = graphene.ID(required=True)
    subcategory_id = graphene.ID()
    priority = graphene.String(required=True)
    privacy = graphene.String(required=True)
    allow_comments = graphene.Boolean(default_value=True)
    allow_sharing = graphene.Boolean(default_value=True)
    incident_date = graphene.DateTime()
    location = graphene.Field(LocationInput)
    tag_ids = graphene.List(graphene.ID)


class UpdateComplaintInput(graphene.InputObjectType):
    """Input for updating an existing complaint"""
    title = graphene.String()
    description = graphene.String()
    category_id = graphene.ID()
    subcategory_id = graphene.ID()
    priority = graphene.String()
    privacy = graphene.String()
    allow_comments = graphene.Boolean()
    allow_sharing = graphene.Boolean()
    incident_date = graphene.DateTime()
    tag_ids = graphene.List(graphene.ID)


class AdminUpdateComplaintInput(graphene.InputObjectType):
    """Input for admin/staff to update complaint status"""
    status = graphene.String()
    assigned_to_id = graphene.ID()
    reference_number = graphene.String()
    reason = graphene.String()


class CreateCommentInput(graphene.InputObjectType):
    """Input for creating a comment"""
    content = graphene.String(required=True)
    parent_id = graphene.ID()
    is_anonymous = graphene.Boolean(default_value=False)
    is_official = graphene.Boolean(default_value=False)


class UpdateCommentInput(graphene.InputObjectType):
    """Input for updating a comment"""
    content = graphene.String(required=True)


class ReactToComplaintInput(graphene.InputObjectType):
    """Input for reacting to a complaint"""
    reaction_type = graphene.String(required=True)


class FollowComplaintInput(graphene.InputObjectType):
    """Input for following a complaint"""
    notify_status_change = graphene.Boolean(default_value=True)
    notify_new_comment = graphene.Boolean(default_value=True)
    notify_resolution = graphene.Boolean(default_value=True)


class ReportComplaintInput(graphene.InputObjectType):
    """Input for reporting a complaint"""
    reason = graphene.String(required=True)
    description = graphene.String()


class ShareComplaintInput(graphene.InputObjectType):
    """Input for sharing a complaint"""
    platform = graphene.String()


class UploadAttachmentInput(graphene.InputObjectType):
    """Input for uploading attachments"""
    file = Upload(required=True)
    description = graphene.String()


class CreateCategoryInput(graphene.InputObjectType):
    """Input for creating a complaint category"""
    name = graphene.String(required=True)
    description = graphene.String()
    icon = graphene.String()
    color = graphene.String(default_value="#007bff")
    department_email = graphene.String()
    department_phone = graphene.String()
    escalation_days = graphene.Int(default_value=7)
    sort_order = graphene.Int(default_value=0)


class UpdateCategoryInput(graphene.InputObjectType):
    """Input for updating a complaint category"""
    name = graphene.String()
    description = graphene.String()
    icon = graphene.String()
    color = graphene.String()
    department_email = graphene.String()
    department_phone = graphene.String()
    escalation_days = graphene.Int()
    sort_order = graphene.Int()
    is_active = graphene.Boolean()


class CreateSubCategoryInput(graphene.InputObjectType):
    """Input for creating a complaint subcategory"""
    category_id = graphene.ID(required=True)
    name = graphene.String(required=True)
    description = graphene.String()
    sort_order = graphene.Int(default_value=0)


class CreateTagInput(graphene.InputObjectType):
    """Input for creating a complaint tag"""
    name = graphene.String(required=True)
    color = graphene.String(default_value="#6c757d")


class ComplaintSearchInput(graphene.InputObjectType):
    """Input for searching complaints"""
    search = graphene.String()
    category_id = graphene.ID()
    subcategory_id = graphene.ID()
    status = graphene.String()
    priority = graphene.String()
    privacy = graphene.String()
    location_country = graphene.String()
    location_state = graphene.String()
    location_city = graphene.String()
    created_after = graphene.DateTime()
    created_before = graphene.DateTime()
    submitted_after = graphene.DateTime()
    submitted_before = graphene.DateTime()
    tag_ids = graphene.List(graphene.ID)
    has_attachments = graphene.Boolean()
    is_overdue = graphene.Boolean()
    allow_comments = graphene.Boolean()
    allow_sharing = graphene.Boolean()
    min_view_count = graphene.Int()
    min_reaction_count = graphene.Int()
    sort_by = graphene.String(default_value="-created_at")


class BulkActionInput(graphene.InputObjectType):
    """Input for bulk actions on complaints"""
    complaint_ids = graphene.List(graphene.ID, required=True)
    action = graphene.String(required=True)
    assigned_user_id = graphene.ID()
    priority = graphene.String()
    status = graphene.String()
    reason = graphene.String()
