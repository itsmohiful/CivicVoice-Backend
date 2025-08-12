"""
Custom permissions for the Complaints API.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.created_by == request.user


class IsComplaintOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a complaint to edit related objects.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the complaint
        if hasattr(obj, 'complaint'):
            return obj.complaint.created_by == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users
        return request.user and request.user.is_staff


class CanReportComplaint(permissions.BasePermission):
    """
    Custom permission to allow users to report complaints.
    """

    def has_object_permission(self, request, view, obj):
        # Users can report complaints that they didn't create
        if hasattr(obj, 'complaint'):
            return obj.complaint.created_by != request.user
        
        return obj.created_by != request.user


class CanFollowComplaint(permissions.BasePermission):
    """
    Custom permission to allow users to follow/unfollow complaints.
    """

    def has_object_permission(self, request, view, obj):
        # Users can follow any complaint including their own
        return True


class CanReactToComplaint(permissions.BasePermission):
    """
    Custom permission to allow users to react to complaints.
    """

    def has_object_permission(self, request, view, obj):
        # Users can react to any complaint including their own
        return True
