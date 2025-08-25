from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, 
    DeleteView, FormView
)
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.exceptions import PermissionDenied

from .models import (
    Complaint, ComplaintCategory, ComplaintSubCategory, ComplaintComment,
    ComplaintReaction, ComplaintTag, ComplaintShare, ComplaintFollower,
    ComplaintReport, Location, ComplaintStatus, ComplaintPrivacy
)
from .forms import (
    ComplaintCreateForm, ComplaintUpdateForm, ComplaintCommentForm,
    ComplaintSearchForm, ComplaintReportForm
)


class ComplaintListView(ListView):
    """
    List all public complaints with filtering and pagination
    """
    model = Complaint
    template_name = 'complaints/complaint_list.html'
    context_object_name = 'complaints'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Complaint.objects.filter(
            status__in=[ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, 
                       ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED],
            privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS],
            is_deleted=False
        ).select_related(
            'category', 'subcategory', 'created_by'
        ).prefetch_related('tags', 'reactions')
        
        # Apply filters
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(complaint_number__icontains=search)
            )
        
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(
                Q(city__icontains=location) |
                Q(state__icontains=location)
            )
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['-created_at', 'created_at', '-view_count', '-reaction_count', 'priority']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ComplaintCategory.objects.filter(is_active=True)
        context['status_choices'] = ComplaintStatus.choices
        context['search_form'] = ComplaintSearchForm(self.request.GET or None)
        
        # Statistics
        context['stats'] = {
            'total_complaints': Complaint.objects.filter(is_deleted=False).count(),
            'resolved_complaints': Complaint.objects.filter(
                status=ComplaintStatus.RESOLVED, is_deleted=False
            ).count(),
            'pending_complaints': Complaint.objects.filter(
                status__in=[ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, 
                           ComplaintStatus.IN_PROGRESS], is_deleted=False
            ).count(),
        }
        
        return context


class ComplaintDetailView(DetailView):
    """
    Detail view for individual complaints
    """
    model = Complaint
    template_name = 'complaints/complaint_detail.html'
    context_object_name = 'complaint'
    slug_field = 'complaint_number'
    slug_url_kwarg = 'complaint_number'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Check privacy permissions
        if not obj.can_view(self.request.user if self.request.user.is_authenticated else None):
            raise Http404(_("Complaint not found"))
        
        # Increment view count for authenticated users (prevent spam)
        if self.request.user.is_authenticated and self.request.user != obj.created_by:
            obj.increment_view_count()
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        complaint = self.object
        
        # Comments with pagination
        comments = complaint.comments.filter(
            parent__isnull=True, is_deleted=False
        ).select_related('created_by').prefetch_related('replies', 'reactions')
        
        paginator = Paginator(comments, 10)
        page_number = self.request.GET.get('page')
        context['comments'] = paginator.get_page(page_number)
        
        # User's reaction
        if self.request.user.is_authenticated:
            context['user_reaction'] = complaint.reactions.filter(
                user=self.request.user
            ).first()
            context['is_following'] = complaint.followers.filter(
                user=self.request.user
            ).exists()
        
        # Forms
        context['comment_form'] = ComplaintCommentForm()
        context['report_form'] = ComplaintReportForm()
        
        # Related complaints
        context['related_complaints'] = Complaint.objects.filter(
            category=complaint.category,
            privacy=ComplaintPrivacy.PUBLIC,
            is_deleted=False
        ).exclude(pk=complaint.pk)[:5]
        
        return context


class ComplaintCreateView(LoginRequiredMixin, CreateView):
    """
    Create new complaint
    """
    model = Complaint
    form_class = ComplaintCreateForm
    template_name = 'complaints/complaint_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_tags'] = ComplaintTag.objects.filter(is_active=True).order_by('name')
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, _('Complaint created successfully!'))
        return response
    
    def get_success_url(self):
        return reverse('complaints:detail', kwargs={'complaint_number': self.object.complaint_number})


class ComplaintUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update existing complaint (only by owner)
    """
    model = Complaint
    form_class = ComplaintUpdateForm
    template_name = 'complaints/complaint_update.html'
    slug_field = 'complaint_number'
    slug_url_kwarg = 'complaint_number'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.can_edit(self.request.user):
            raise PermissionDenied(_("You don't have permission to edit this complaint"))
        return obj
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, _('Complaint updated successfully!'))
        return response


class MyComplaintsView(LoginRequiredMixin, ListView):
    """
    User's own complaints
    """
    model = Complaint
    template_name = 'complaints/my_complaints.html'
    context_object_name = 'complaints'
    paginate_by = 10
    
    def get_queryset(self):
        return Complaint.objects.filter(
            created_by=self.request.user,
            is_deleted=False
        ).select_related('category', 'subcategory').order_by('-created_at')


@login_required
@require_POST
def add_comment(request, complaint_number):
    """
    Add comment to complaint via AJAX
    """
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)
    
    if not complaint.allow_comments:
        return JsonResponse({'success': False, 'error': 'Comments not allowed'})
    
    form = ComplaintCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.complaint = complaint
        comment.created_by = request.user
        
        # Handle parent comment for replies
        parent_comment_id = request.POST.get('parent_comment')
        if parent_comment_id:
            try:
                parent_comment = ComplaintComment.objects.get(
                    id=parent_comment_id, 
                    complaint=complaint
                )
                comment.parent = parent_comment
            except ComplaintComment.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Parent comment not found'})
        
        comment.save()
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': (comment.created_by.get_full_name() if comment.created_by and comment.created_by.get_full_name() 
                          else comment.created_by.username if comment.created_by 
                          else 'Anonymous'),
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_official': comment.is_official,
                'is_reply': bool(comment.parent)
            }
        })
    
    return JsonResponse({'success': False, 'errors': form.errors})


@login_required
@require_POST
def toggle_reaction(request, complaint_number):
    """
    Toggle reaction on complaint via AJAX
    """
    try:
        complaint = get_object_or_404(Complaint, complaint_number=complaint_number)
        
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            reaction_type = data.get('reaction_type')
        else:
            reaction_type = request.POST.get('reaction_type')
        
        # Debug logging
        print(f"Received reaction_type: {reaction_type}")
        print(f"Available choices: {dict(ComplaintReaction.ReactionType.choices)}")
        
        # Validate reaction type
        valid_types = [choice[0] for choice in ComplaintReaction.ReactionType.choices]
        if reaction_type not in valid_types:
            return JsonResponse({
                'success': False, 
                'error': f'Invalid reaction type: {reaction_type}. Valid types: {valid_types}'
            })
        
        with transaction.atomic():
            reaction, created = ComplaintReaction.objects.get_or_create(
                complaint=complaint,
                user=request.user,
                defaults={'reaction_type': reaction_type}
            )
            
            user_reacted = True
            if not created:
                if reaction.reaction_type == reaction_type:
                    # Remove reaction if same type
                    reaction.delete()
                    user_reacted = False
                    action = 'removed'
                else:
                    # Update reaction type
                    reaction.reaction_type = reaction_type
                    reaction.save()
                    action = 'updated'
            else:
                action = 'added'
            
            # Get the specific count for this reaction type
            count = complaint.reactions.filter(reaction_type=reaction_type).count()
            
            # Get updated total counts
            reaction_counts = complaint.reactions.values('reaction_type').annotate(
                count=Count('id')
            )
            counts = {r['reaction_type']: r['count'] for r in reaction_counts}
        
        return JsonResponse({
            'success': True,
            'action': action,
            'count': count,
            'user_reacted': user_reacted,
            'counts': counts,
            'total_count': sum(counts.values())
        })
    
    except Exception as e:
        print(f"Error in toggle_reaction: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': f'Server error: {str(e)}'
        })


@login_required
@require_POST
def toggle_follow(request, complaint_number):
    """
    Toggle following a complaint
    """
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)
    
    follower, created = ComplaintFollower.objects.get_or_create(
        complaint=complaint,
        user=request.user
    )
    
    if not created:
        follower.delete()
        following = False
    else:
        following = True
    
    return JsonResponse({
        'success': True,
        'is_following': following,
        'follower_count': complaint.followers.count()
    })


@login_required
@require_POST
def share_complaint(request, complaint_number):
    """
    Track complaint sharing
    """
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)
    
    if not complaint.allow_sharing:
        return JsonResponse({'success': False, 'error': 'Sharing not allowed'})
    
    platform = request.POST.get('platform', '')
    
    share, created = ComplaintShare.objects.get_or_create(
        complaint=complaint,
        created_by=request.user,
        shared_by=request.user,
        defaults={'platform': platform}
    )
    
    return JsonResponse({
        'success': True,
        'share_count': complaint.shares.count()
    })


@login_required
@require_POST
def report_complaint(request, complaint_number):
    """
    Report inappropriate complaint
    """
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)
    
    # Handle both form and direct POST data
    reason = request.POST.get('reason', 'inappropriate')
    description = request.POST.get('description', '')
    
    # Check if user already reported this complaint
    existing_report = ComplaintReport.objects.filter(
        complaint=complaint,
        created_by=request.user,
        reported_by=request.user
    ).first()
    
    if existing_report:
        return JsonResponse({
            'success': False, 
            'error': 'You have already reported this complaint'
        })
    
    # Create the report
    report = ComplaintReport.objects.create(
        complaint=complaint,
        created_by=request.user,
        reported_by=request.user,
        reason=reason,
        description=description
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Thank you for your report. We will review it soon.'
    })


class CategoryComplaintsView(ListView):
    """
    Complaints by category
    """
    model = Complaint
    template_name = 'complaints/category_complaints.html'
    context_object_name = 'complaints'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(ComplaintCategory, pk=self.kwargs['category_id'])
        return Complaint.objects.filter(
            category=self.category,
            privacy=ComplaintPrivacy.PUBLIC,
            is_deleted=False
        ).select_related('created_by', 'location').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['subcategories'] = self.category.subcategories.filter(is_active=True)
        return context


@login_required
def complaint_analytics(request, complaint_number):
    """
    Analytics for complaint owner
    """
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number, created_by=request.user)
    
    # Reaction analytics
    reaction_stats = complaint.reactions.values('reaction_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Comment analytics
    comment_stats = complaint.comments.filter(parent__isnull=True).count()
    
    # View analytics (simplified - in real app, you'd track daily views)
    daily_views = [
        {'date': '2024-01-01', 'views': 10},  # Sample data
        {'date': '2024-01-02', 'views': 15},
        # Add real daily view tracking
    ]
    
    context = {
        'complaint': complaint,
        'reaction_stats': reaction_stats,
        'comment_stats': comment_stats,
        'daily_views': daily_views,
        'total_engagement': complaint.view_count + complaint.reaction_count + complaint.comment_count
    }
    
    return render(request, 'complaints/complaint_analytics.html', context)


def complaint_search_api(request):
    """
    API endpoint for complaint search with autocomplete
    """
    query = request.GET.get('q', '')
    if len(query) < 3:
        return JsonResponse({'results': []})
    
    complaints = Complaint.objects.filter(
        Q(title__icontains=query) | Q(complaint_number__icontains=query),
        privacy=ComplaintPrivacy.PUBLIC,
        is_deleted=False
    )[:10]
    
    results = [{
        'id': c.complaint_number,
        'title': c.title,
        'category': c.category.name,
        'status': c.get_status_display(),
        'url': reverse('complaints:detail', kwargs={'complaint_number': c.complaint_number})
    } for c in complaints]
    
    return JsonResponse({'results': results})


class ComplaintStatsView(ListView):
    """
    Public statistics and charts
    """
    template_name = 'complaints/stats.html'
    model = Complaint
    context_object_name = 'complaints'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Category-wise statistics
        category_stats = ComplaintCategory.objects.annotate(
            total_complaints=Count('complaints', filter=Q(complaints__is_deleted=False)),
            resolved_complaints=Count('complaints', filter=Q(
                complaints__status=ComplaintStatus.RESOLVED,
                complaints__is_deleted=False
            ))
        ).filter(is_active=True)
        
        # Monthly statistics
        from django.db.models import TruncMonth
        monthly_stats = Complaint.objects.filter(
            is_deleted=False,
            created_at__year=timezone.now().year
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Status distribution
        status_stats = Complaint.objects.filter(
            is_deleted=False
        ).values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        context.update({
            'category_stats': category_stats,
            'monthly_stats': list(monthly_stats),
            'status_stats': status_stats,
            'total_users': ComplaintFollower.objects.values('user').distinct().count(),
        })
        
        return context


class CategoryComplaintsView(ListView):
    """
    List complaints by category
    """
    template_name = 'complaints/category_complaints.html'
    context_object_name = 'complaints'
    paginate_by = 12
    
    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return Complaint.objects.filter(
            category_id=category_id,
            status__in=[ComplaintStatus.SUBMITTED, ComplaintStatus.UNDER_REVIEW, 
                       ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED],
            privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS],
            is_deleted=False
        ).select_related('category', 'subcategory', 'created_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs.get('category_id')
        context['category'] = get_object_or_404(ComplaintCategory, id=category_id)
        return context


@login_required
def complaint_analytics(request, complaint_number):
    """
    Analytics for individual complaints
    """
    complaint = get_object_or_404(Complaint, complaint_number=complaint_number)
    
    # Check permissions
    if not complaint.can_view(request.user):
        raise Http404(_("Complaint not found"))
    
    # Only complaint owner and staff can view analytics
    if request.user != complaint.created_by and not request.user.is_staff:
        raise PermissionDenied
    
    # Get analytics data
    analytics_data = {
        'view_count': complaint.view_count,
        'reaction_count': complaint.reactions.count(),
        'comment_count': complaint.comments.count(),
        'share_count': complaint.shares.count(),
        'follower_count': complaint.followers.count(),
    }
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse(analytics_data)
    
    return render(request, 'complaints/complaint_analytics.html', {
        'complaint': complaint,
        'analytics': analytics_data
    })


def complaint_search_api(request):
    """
    API endpoint for searching complaints
    """
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    
    complaints = Complaint.objects.filter(
        privacy__in=[ComplaintPrivacy.PUBLIC, ComplaintPrivacy.ANONYMOUS],
        is_deleted=False
    )
    
    if query:
        complaints = complaints.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        )
    
    if category:
        complaints = complaints.filter(category_id=category)
    
    if status:
        complaints = complaints.filter(status=status)
    
    # Limit results for API
    complaints = complaints[:20]
    
    results = []
    for complaint in complaints:
        results.append({
            'id': str(complaint.id),
            'title': complaint.title,
            'complaint_number': complaint.complaint_number,
            'status': complaint.get_status_display(),
            'category': complaint.category.name,
            'created_at': complaint.created_at.isoformat(),
            'url': reverse('complaints:detail', kwargs={'complaint_number': complaint.complaint_number})
        })
    
    return JsonResponse({'results': results})
