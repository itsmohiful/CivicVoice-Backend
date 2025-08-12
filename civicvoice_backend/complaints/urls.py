from django.urls import path, include
from django.views.generic import TemplateView

from . import views

app_name = 'complaints'

urlpatterns = [
    # Main complaint URLs
    path('', views.ComplaintListView.as_view(), name='list'),
    path('create/', views.ComplaintCreateView.as_view(), name='create'),
    path('my-complaints/', views.MyComplaintsView.as_view(), name='my_complaints'),
    path('stats/', views.ComplaintStatsView.as_view(), name='stats'),
    
    # Complaint detail and actions
    path('<str:complaint_number>/', views.ComplaintDetailView.as_view(), name='detail'),
    path('<str:complaint_number>/edit/', views.ComplaintUpdateView.as_view(), name='update'),
    path('<str:complaint_number>/analytics/', views.complaint_analytics, name='analytics'),
    
    # AJAX endpoints
    path('<str:complaint_number>/comment/', views.add_comment, name='add_comment'),
    path('<str:complaint_number>/react/', views.toggle_reaction, name='toggle_reaction'),
    path('<str:complaint_number>/follow/', views.toggle_follow, name='toggle_follow'),
    path('<str:complaint_number>/share/', views.share_complaint, name='share_complaint'),
    path('<str:complaint_number>/report/', views.report_complaint, name='report_complaint'),
    
    # Category-based URLs
    path('category/<int:category_id>/', views.CategoryComplaintsView.as_view(), name='category_complaints'),
    
    # API endpoints
    path('api/search/', views.complaint_search_api, name='search_api'),
    
    # Additional pages
    path('help/', TemplateView.as_view(template_name='complaints/help.html'), name='help'),
    path('guidelines/', TemplateView.as_view(template_name='complaints/guidelines.html'), name='guidelines'),
]
