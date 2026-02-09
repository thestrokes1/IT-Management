"""
Enterprise Logs View with Timeline UI

Features:
- Chronological timeline grouped by day
- Expandable entries with full details
- Smart filtering (category, severity, actor, target, time)
- Human + machine readable format
- Event correlation (request_id, session_id)
- Export functionality (CSV, JSON)

Usage:
    from apps.frontend.views.logs import logs_view, logs_api, logs_export

ARCHITECTURE:
- Uses ActivityAdapter.to_ui() as the SINGLE source for UI log objects
- Views orchestrate only - no business logic here
- Templates receive pre-computed UI objects
"""

from datetime import datetime
import json
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

from apps.logs.models import ActivityLog, SecurityEvent
from apps.logs.services.log_query_service import LogQueryService
from apps.logs.services.access_policy import LogAccessPolicyService
from apps.logs.services.activity_adapter import ActivityAdapter
from apps.logs.services.security_event_service import SecurityEventService


class LogsView(TemplateView):
    """
    Main logs view using ActivityAdapter.to_ui() as the single source
    for UI log representations.
    
    Template receives:
    - log_entries: List[ActivityUIData] - pre-computed UI objects
    - security_events: List[SecurityEventDetailDTO]
    - all_users: QuerySet for filter dropdown
    """
    template_name = 'frontend/logs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check access policy
        policy_service = LogAccessPolicyService(user=self.request.user)
        access_policy = policy_service.get_access_policy()
        
        if not access_policy.allowed:
            context['error'] = 'You do not have permission to view logs.'
            return context
        
        # Build query from filters
        query_service = LogQueryService(user=self.request.user)
        query_service = self._apply_filters(query_service, self.request.GET)
        
        # Get paginated results
        page = int(self.request.GET.get('page', 1))
        per_page = int(self.request.GET.get('per_page', 50))
        
        queryset = query_service.order_by('-timestamp').all()
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)
        
        # CRITICAL: Use ActivityAdapter.to_ui() as the SINGLE source for UI objects
        log_entries = ActivityAdapter.adapt_queryset(page_obj.object_list)
        
        # Get security events
        security_events = self._get_security_events()
        
        # Get all active users for the filter dropdown
        from apps.users.models import User
        all_users = User.objects.filter(is_active=True).order_by('username')
        
        context.update({
            'log_entries': log_entries,
            'security_events': security_events,
            'all_users': all_users,
            'page_obj': page_obj,
            'paginator': paginator,
            'filters': self._get_filters(),
        })
        
        return context
    
    def _get_filters(self) -> dict:
        """Get filter parameters from request."""
        return {
            'category': self.request.GET.get('category', ''),
            'severity': self.request.GET.get('severity', ''),
            'actor_role': self.request.GET.get('actor_role', ''),
            'action': self.request.GET.get('action', ''),
            'target_type': self.request.GET.get('target_type', ''),
            'target_id': self.request.GET.get('target_id', ''),
            'username': self.request.GET.get('username', ''),
            'search': self.request.GET.get('search', ''),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
        }
    
    def _apply_filters(self, query_service: LogQueryService, params) -> LogQueryService:
        """Apply filters to query service."""
        if params.get('category'):
            query_service = query_service.filter_by_category(params['category'])
        
        if params.get('severity'):
            query_service = query_service.filter_by_severity([params['severity']])
        
        if params.get('actor_role'):
            query_service = query_service.filter_by_actor_role([params['actor_role']])
        
        if params.get('action'):
            query_service = query_service.filter_by_action([params['action']])
        
        if params.get('target_type'):
            query_service = query_service.filter_by_target(params['target_type'])
        
        if params.get('username'):
            # Strip whitespace and filter by exact actor name (case-insensitive)
            username = params['username'].strip() if isinstance(params['username'], str) else params['username']
            query_service = query_service.filter_by_actor(actor_name=username)
        
        if params.get('search'):
            search_term = params['search'].strip() if isinstance(params['search'], str) else params['search']
            query_service = query_service.search(search_term)
        
        if params.get('start_date') or params.get('end_date'):
            query_service = query_service.filter_by_date_range(
                start_date=params.get('start_date'),
                end_date=params.get('end_date')
            )
        
        return query_service
    
    def _get_security_events(self) -> list:
        """Get security events for display."""
        service = SecurityEventService()
        return service.get_recent_events(limit=10)


# =============================================================================
# API Endpoints
# =============================================================================

@login_required
def logs_api(request):
    """
    API endpoint for logs data.
    
    Query parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50, max: 100)
        - category: Filter by category
        - severity: Filter by severity
        - All other filters supported by logs view
    
    Returns JSON with ActivityAdapter-formatted data.
    """
    # Check access
    policy_service = LogAccessPolicyService(user=request.user)
    access_policy = policy_service.get_access_policy()
    
    if not access_policy.allowed:
        return JsonResponse({
            'error': 'Access denied',
            'message': 'You do not have permission to view logs.'
        }, status=403)
    
    # Get parameters
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 50)), 100)
    
    # Build query
    query_service = LogQueryService(user=request.user)
    query_service = _apply_api_filters(query_service, request.GET)
    
    # Execute query
    queryset = query_service.order_by('-timestamp').all()
    
    # Paginate
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)
    
    # CRITICAL: Use ActivityAdapter.to_dict() for API response
    logs_data = [ActivityAdapter.to_dict(log) for log in page_obj.object_list]
    
    response_data = {
        'logs': logs_data,
        'pagination': {
            'page': page_obj.number,
            'per_page': per_page,
            'total': paginator.count,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        },
        'access': {
            'can_export': access_policy.can_export,
        }
    }
    
    return JsonResponse(response_data)


@login_required
def logs_export(request):
    """
    Export logs in CSV or JSON format.
    
    Query parameters:
        - format: 'csv' or 'json' (default: 'csv')
        - All filters supported by logs view
    
    Only users with export permission can use this endpoint.
    """
    # Check access
    policy_service = LogAccessPolicyService(user=request.user)
    access_policy = policy_service.get_access_policy()
    
    if not access_policy.can_export:
        return JsonResponse({
            'error': 'Access denied',
            'message': 'You do not have permission to export logs.'
        }, status=403)
    
    # Get parameters
    export_format = request.GET.get('format', 'csv')
    limit = min(int(request.GET.get('limit', 10000)), 50000)
    
    # Build query
    query_service = LogQueryService(user=request.user)
    query_service = _apply_api_filters(query_service, request.GET)
    
    # Execute query with limit
    queryset = query_service.order_by('-timestamp').all()[:limit]
    
    # CRITICAL: Use ActivityAdapter.to_dict() for export data
    logs_data = [ActivityAdapter.to_dict(log) for log in queryset]
    
    if export_format == 'json':
        response = JsonResponse({'logs': logs_data, 'exported_at': timezone.now().isoformat()})
        response['Content-Disposition'] = f'attachment; filename="logs_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    
    # CSV format
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'ID', 'Timestamp', 'Event Code', 'Category', 'Severity',
        'Actor', 'Actor Role', 'Action', 'Target Type', 'Target ID',
        'Description', 'IP Address', 'Narrative'
    ])
    
    # Rows - use ActivityAdapter fields
    for log in logs_data:
        writer.writerow([
            log.get('log_id', ''),
            log.get('timestamp', ''),
            log.get('action', {}).get('key', ''),
            log.get('category', ''),
            log.get('severity', {}).get('level', ''),
            log.get('actor', {}).get('name', ''),
            log.get('actor', {}).get('role', ''),
            log.get('action', {}).get('verb', ''),
            log.get('entity', {}).get('type', ''),
            log.get('entity', {}).get('id', ''),
            log.get('changes_summary', ''),
            log.get('ip_address', ''),
            log.get('narrative', ''),
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="logs_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    return response


# =============================================================================
# Helper Functions
# =============================================================================

def _apply_api_filters(query_service: LogQueryService, params) -> LogQueryService:
    """Apply filters from API parameters."""
    if params.get('category'):
        query_service.filter_by_category(params['category'])
    
    if params.get('severity'):
        query_service.filter_by_severity([params['severity']])
    
    if params.get('actor_role'):
        query_service.filter_by_actor_role([params['actor_role']])
    
    if params.get('action'):
        query_service.filter_by_action([params['action']])
    
    if params.get('target_type'):
        query_service.filter_by_target(params['target_type'])
    
    if params.get('search'):
        query_service.search(params['search'])
    
    if params.get('start_date') or params.get('end_date'):
        query_service.filter_by_date_range(
            start_date=params.get('start_date'),
            end_date=params.get('end_date')
        )
    
    return query_service


# =============================================================================
# View Wrappers
# =============================================================================

def logs(request):
    """Main logs page view."""
    view = LogsView.as_view()
    return view(request)


def logs_detail(request, log_id):
    """Single log detail view."""
    from django.shortcuts import get_object_or_404
    
    # Check access
    policy_service = LogAccessPolicyService(user=request.user)
    access_policy = policy_service.get_access_policy()
    
    if not access_policy.allowed:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('You do not have permission to view logs.')
    
    log = get_object_or_404(ActivityLog, id=log_id)
    
    # Check if user can view this specific log
    if not policy_service.can_view_log(log):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('You do not have permission to view this log.')
    
    # CRITICAL: Use ActivityAdapter.to_ui() for detail view
    ui_data = ActivityAdapter.to_ui(log)
    
    return JsonResponse({
        'log': ActivityAdapter.to_dict(log),
        'narrative': ui_data.narrative,
        'changes_summary': ui_data.changes_summary,
        'changes_detail': ui_data.changes_detail,
    })
