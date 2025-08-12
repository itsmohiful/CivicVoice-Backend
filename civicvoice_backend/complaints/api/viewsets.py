from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone

from civicvoice_backend.complaints.models import (
    ComplaintCategory, ComplaintSubCategory, ComplaintTag, Location,
    Complaint, ComplaintComment, ComplaintReaction, ComplaintAttachment,
    ComplaintShare, ComplaintFollower, ComplaintReport, ComplaintStatusHistory,
    ComplaintPrivacy, ComplaintStatus
)
from civicvoice_backend.complaints.api.serializers import (
    ComplaintCategorySerializer, ComplaintSubCategorySerializer,
    ComplaintTagSerializer, LocationSerializer, ComplaintSerializer,
    ComplaintListSerializer, ComplaintCommentSerializer, ComplaintReactionSerializer,
    ComplaintAttachmentSerializer, ComplaintShareSerializer, ComplaintFollowerSerializer,
    ComplaintReportSerializer, ComplaintStatusHistorySerializer
)
from civicvoice_backend.complaints.api.filters import (
    ComplaintFilter, ComplaintCategoryFilter, ComplaintCommentFilter,
    ComplaintReactionFilter, ComplaintAttachmentFilter, ComplaintSubCategoryFilter,
    ComplaintTagFilter, LocationFilter, ComplaintReportFilter, ComplaintStatusHistoryFilter
)
from civicvoice_backend.complaints.api.permissions import (
    IsOwnerOrReadOnly, IsComplaintOwnerOrReadOnly, IsAdminOrReadOnly,
    CanReportComplaint, CanFollowComplaint, CanReactToComplaint
)


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
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'reported_by'):
            return obj.reported_by == request.user
        elif hasattr(obj, 'shared_by'):
            return obj.shared_by == request.user
        
        return False


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff to edit.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff


class ComplaintCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplaintCategory model"""
    queryset = ComplaintCategory.objects.filter(is_deleted=False).order_by('sort_order', 'name')
    serializer_class = ComplaintCategorySerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ComplaintCategoryFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['sort_order', 'name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            # Only show active categories for list view
            queryset = queryset.filter(is_active=True)
        return queryset
    
    @action(detail=True, methods=['get'])
    def complaints(self, request, pk=None):
        """Get complaints for this category"""
        category = self.get_object()
        complaints = category.complaints.filter(is_deleted=False).order_by('-created_at')
        
        # Apply privacy filter for non-staff users
        if not (request.user.is_authenticated and request.user.is_staff):
            complaints = complaints.filter(
                privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS]
            )
        
        page = self.paginate_queryset(complaints)
        if page is not None:
            serializer = ComplaintListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ComplaintListSerializer(complaints, many=True, context={'request': request})
        return Response(serializer.data)


class ComplaintSubCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplaintSubCategory model"""
    queryset = ComplaintSubCategory.objects.filter(is_deleted=False).order_by('category__sort_order', 'sort_order', 'name')
    serializer_class = ComplaintSubCategorySerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ComplaintSubCategoryFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['category__sort_order', 'sort_order', 'name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            # Only show active subcategories for list view
            queryset = queryset.filter(is_active=True)
        return queryset


class ComplaintTagViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplaintTag model"""
    queryset = ComplaintTag.objects.filter(is_deleted=False).order_by('name')
    serializer_class = ComplaintTagSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ComplaintTagFilter
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            # Only show active tags for list view
            queryset = queryset.filter(is_active=True)
        return queryset


class LocationViewSet(viewsets.ModelViewSet):
    """ViewSet for Location model"""
    queryset = Location.objects.filter(is_deleted=False).order_by('country', 'state', 'city')
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LocationFilter
    search_fields = ['country', 'state', 'city', 'area', 'address']
    ordering_fields = ['country', 'state', 'city', 'area', 'created_at']
    ordering = ['country', 'state', 'city']


class ComplaintViewSet(viewsets.ModelViewSet):
    """ViewSet for Complaint model"""
    queryset = Complaint.objects.filter(is_deleted=False).order_by('-created_at')
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ComplaintFilter
    search_fields = ['title', 'description', 'complaint_number']
    ordering_fields = ['created_at', 'updated_at', 'submitted_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ComplaintListSerializer
        return ComplaintSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            # Admin users can see all complaints
            return queryset
        else:
            # Regular users can only see public and anonymous complaints
            return queryset.filter(
                privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS],
                status__in=[
                    ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW,
                    ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED
                ]
            )
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Follow a complaint"""
        complaint = self.get_object()
        follower, created = ComplaintFollower.objects.get_or_create(
            complaint=complaint,
            user=request.user,
            defaults={
                'notify_status_change': True,
                'notify_new_comment': True,
                'notify_resolution': True
            }
        )
        
        if created:
            return Response({'message': 'Now following this complaint'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Already following this complaint'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        """Unfollow a complaint"""
        complaint = self.get_object()
        try:
            follower = ComplaintFollower.objects.get(complaint=complaint, user=request.user)
            follower.delete()
            return Response({'message': 'Unfollowed complaint'}, status=status.HTTP_200_OK)
        except ComplaintFollower.DoesNotExist:
            return Response({'message': 'Not following this complaint'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """React to a complaint"""
        complaint = self.get_object()
        reaction_type = request.data.get('reaction_type')
        
        if not reaction_type:
            return Response({'error': 'reaction_type is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove existing reaction if any
        ComplaintReaction.objects.filter(complaint=complaint, user=request.user).delete()
        
        # Create new reaction
        reaction = ComplaintReaction.objects.create(
            complaint=complaint,
            user=request.user,
            reaction_type=reaction_type
        )
        
        serializer = ComplaintReactionSerializer(reaction, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def unreact(self, request, pk=None):
        """Remove reaction from a complaint"""
        complaint = self.get_object()
        try:
            reaction = ComplaintReaction.objects.get(complaint=complaint, user=request.user)
            reaction.delete()
            return Response({'message': 'Reaction removed'}, status=status.HTTP_200_OK)
        except ComplaintReaction.DoesNotExist:
            return Response({'message': 'No reaction found'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share a complaint"""
        complaint = self.get_object()
        platform = request.data.get('platform', 'other')
        
        share, created = ComplaintShare.objects.get_or_create(
            complaint=complaint,
            shared_by=request.user,
            defaults={'platform': platform}
        )
        
        if created:
            # Update share count
            complaint.share_count = complaint.shares.count()
            complaint.save(update_fields=['share_count'])
            
            serializer = ComplaintShareSerializer(share, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Already shared this complaint'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def report(self, request, pk=None):
        """Report a complaint"""
        complaint = self.get_object()
        reason = request.data.get('reason')
        description = request.data.get('description', '')
        
        if not reason:
            return Response({'error': 'reason is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        report, created = ComplaintReport.objects.get_or_create(
            complaint=complaint,
            reported_by=request.user,
            defaults={
                'reason': reason,
                'description': description
            }
        )
        
        if created:
            serializer = ComplaintReportSerializer(report, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Already reported this complaint'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_complaints(self, request):
        """Get current user's complaints"""
        queryset = self.get_queryset().filter(created_by=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_followed(self, request):
        """Get complaints followed by current user"""
        followed_complaint_ids = ComplaintFollower.objects.filter(
            user=request.user
        ).values_list('complaint_id', flat=True)
        
        queryset = self.get_queryset().filter(id__in=followed_complaint_ids)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """Get public complaints"""
        queryset = self.get_queryset().filter(privacy=ComplaintPrivacy.PUBLIC)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def overdue(self, request):
        """Get overdue complaints (admin only)"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        
        queryset = self.get_queryset().filter(
            due_date__lt=timezone.now(),
            status__in=[
                ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW,
                ComplaintStatus.IN_PROGRESS
            ]
        ).order_by('due_date')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ComplaintCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplaintComment model"""
    queryset = ComplaintComment.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = ComplaintCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ComplaintCommentFilter
    search_fields = ['content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only show comments for public/anonymous complaints for non-staff users
        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.is_superuser)):
            queryset = queryset.filter(
                complaint__privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS]
            )
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ComplaintReactionViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplaintReaction model"""
    queryset = ComplaintReaction.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = ComplaintReactionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ComplaintReactionFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only show reactions for public/anonymous complaints for non-staff users
        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.is_superuser)):
            queryset = queryset.filter(
                complaint__privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS]
            )
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ComplaintAttachmentViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplaintAttachment model"""
    queryset = ComplaintAttachment.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = ComplaintAttachmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ComplaintAttachmentFilter
    search_fields = ['original_name', 'description']
    ordering_fields = ['created_at', 'original_name', 'file_size']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only show attachments for public/anonymous complaints for non-staff users
        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.is_superuser)):
            queryset = queryset.filter(
                complaint__privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS]
            )
        return queryset


class ComplaintShareViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplaintShare model"""
    queryset = ComplaintShare.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = ComplaintShareSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Users can only see their own shares
        return super().get_queryset().filter(shared_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(shared_by=self.request.user)


class ComplaintFollowerViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplaintFollower model"""
    queryset = ComplaintFollower.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = ComplaintFollowerSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Users can only see their own follows
        return super().get_queryset().filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ComplaintReportViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplaintReport model"""
    queryset = ComplaintReport.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = ComplaintReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ComplaintReportFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Staff can see all reports
            return super().get_queryset()
        else:
            # Regular users can only see their own reports
            return super().get_queryset().filter(reported_by=user)
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def resolve(self, request, pk=None):
        """Resolve a report (staff only)"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Staff access required'}, status=status.HTTP_403_FORBIDDEN)
        
        report = self.get_object()
        report.is_resolved = True
        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)


class ComplaintStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ComplaintStatusHistory model (read-only)"""
    queryset = ComplaintStatusHistory.objects.filter(is_deleted=False).order_by('-created_at')
    serializer_class = ComplaintStatusHistorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ComplaintStatusHistoryFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only show status history for public/anonymous complaints for non-staff users
        user = self.request.user
        if not (user.is_authenticated and (user.is_staff or user.is_superuser)):
            queryset = queryset.filter(
                complaint__privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS]
            )
        return queryset
