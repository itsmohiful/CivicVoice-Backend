from django.urls import path, include
from rest_framework.routers import DefaultRouter
from civicvoice_backend.complaints.api.viewsets import (
    ComplaintCategoryViewSet, ComplaintSubCategoryViewSet, ComplaintTagViewSet,
    LocationViewSet, ComplaintViewSet, ComplaintCommentViewSet,
    ComplaintReactionViewSet, ComplaintAttachmentViewSet, ComplaintShareViewSet,
    ComplaintFollowerViewSet, ComplaintReportViewSet, ComplaintStatusHistoryViewSet
)
from civicvoice_backend.complaints.api.views import api_root

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'categories', ComplaintCategoryViewSet, basename='complaintcategory')
router.register(r'subcategories', ComplaintSubCategoryViewSet, basename='complaintsubcategory')
router.register(r'tags', ComplaintTagViewSet, basename='complainttag')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'complaints', ComplaintViewSet, basename='complaint')
router.register(r'comments', ComplaintCommentViewSet, basename='complaintcomment')
router.register(r'reactions', ComplaintReactionViewSet, basename='complaintreaction')
router.register(r'attachments', ComplaintAttachmentViewSet, basename='complaintattachment')
router.register(r'shares', ComplaintShareViewSet, basename='complaintshare')
router.register(r'followers', ComplaintFollowerViewSet, basename='complaintfollower')
router.register(r'reports', ComplaintReportViewSet, basename='complaintreport')
router.register(r'status-history', ComplaintStatusHistoryViewSet, basename='complaintstatushistory')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', api_root, name='api-root'),
    path('', include(router.urls)),
]
