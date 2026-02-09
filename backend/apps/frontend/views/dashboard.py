"""
Dashboard views for IT Management Platform.
Contains DashboardView and related API endpoints.
Enhanced with activity logging and security event services.

Action-driven dashboard design:
- "My Responsibility" section (role-aware)
- SLA risk indicators
- Unassigned / stalled tickets
- Recent explainable logs (filtered by role)
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime, date
import json

try:
    from apps.users.models import User
    from apps.assets.models import Asset
    from apps.projects.models import Project
    from apps.tickets.models import Ticket, TicketComment
    from apps.logs.models import ActivityLog, SecurityEvent, SystemLog
    # Import new services for enhanced dashboard
    from apps.logs.services.activity_service import ActivityService
    from apps.logs.services.security_service import SecurityEventService
except ImportError:
    User = None
    Asset = None
    Project = None
    Ticket = None
    ActivityLog = None
    SecurityEvent = None
    SystemLog = None
    ActivityService = None
    SecurityEventService = None


# =============================================================================
# Safe Count Helper Functions
# =============================================================================

def safe_count(data) -> int:
    """
    Safely get the count of a QuerySet or list.
    
    This helper handles the difference between:
    - QuerySet.count() - SQL COUNT query (no argument)
    - len(list) - Python length
    
    Args:
        data: QuerySet, list, or other collection
        
    Returns:
        Integer count of items
    """
    if data is None:
        return 0
    # Check if it's a Django QuerySet by checking for the 'count' attribute
    # that's specific to QuerySet (not Python's list.count which requires an argument)
    if hasattr(data, 'count') and not isinstance(data, (list, tuple, set)):
        # It's a QuerySet or similar with count() method that takes no args
        return data.count()
    # It's a list, tuple, or other iterable - use len()
    return len(data)


def safe_getattr(obj, name, default=None):
    """
    Safely get an attribute from an object.
    
    Args:
        obj: The object to get attribute from
        name: Attribute name
        default: Default value if attribute doesn't exist
        
    Returns:
        Attribute value or default
    """
    if obj is None:
        return default
    return getattr(obj, name, default)


# SLA thresholds in hours
SLA_THRESHOLDS = {
    'CRITICAL': 4,    # 4 hours for critical
    'HIGH': 8,        # 8 hours for high
    'MEDIUM': 24,     # 24 hours for medium
    'LOW': 72,        # 72 hours for low
}

# Stalled ticket threshold (hours without update)
STALLED_THRESHOLD_HOURS = 24


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Action-driven dashboard with role-aware metrics.
    
    All business logic is resolved in the view.
    Template receives only safe-to-render data.
    """
    template_name = 'frontend/dashboard.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_role = getattr(user, 'role', 'VIEWER')
        is_admin = user.is_superuser or user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
        
        # Display login success message if it exists in session
        if 'login_success' in self.request.session:
            from django.contrib import messages
            messages.success(self.request, self.request.session.pop('login_success'))
        
        # Initialize services
        activity_service = ActivityService() if ActivityService else None
        
        # =====================================================================
        # 1. MY RESPONSIBILITY SECTION (Role-aware)
        # =====================================================================
        responsibility_metrics = self._get_responsibility_metrics(user, user_role)
        
        # =====================================================================
        # 2. SLA RISK INDICATORS
        # =====================================================================
        sla_risks = self._get_sla_risks(user, user_role)
        
        # =====================================================================
        # 3. UNASSIGNED / STALLED TICKETS
        # =====================================================================
        unassigned_stalled = self._get_unassigned_stalled_tickets(user_role)
        
        # =====================================================================
        # 4. RECENT EXPLAINABLE LOGS (Filtered by role)
        # =====================================================================
        recent_logs = self._get_recent_logs_for_dashboard(activity_service, user, user_role)
        
        # =====================================================================
        # 5. STATISTICS (Pre-computed)
        # =====================================================================
        stats = self._get_stats(user_role, is_admin)
        
        # =====================================================================
        # 6. SECURITY EVENTS (Admin only)
        # =====================================================================
        security_data = self._get_security_data(is_admin)
        
        # Build complete context
        context.update({
            # Role info
            'user_role': user_role,
            'is_admin': is_admin,
            
            # Section 1: My Responsibility
            'my_tickets_count': responsibility_metrics['my_tickets_count'],
            'my_assigned_count': responsibility_metrics['my_assigned_count'],
            'my_created_count': responsibility_metrics['my_created_count'],
            'my_overdue_count': responsibility_metrics['my_overdue_count'],
            'my_tickets': responsibility_metrics['my_tickets'],
            'my_projects': responsibility_metrics.get('my_projects', []),
            'my_projects_count': responsibility_metrics.get('my_projects_count', 0),
            
            # Section 2: SLA Risks
            'sla_risks': sla_risks['risky_tickets'],
            'sla_risk_count': sla_risks['risk_count'],
            'critical_sla_count': sla_risks['critical_count'],
            
            # Section 3: Unassigned / Stalled
            'unassigned_tickets': unassigned_stalled['unassigned'],
            'unassigned_count': unassigned_stalled['unassigned_count'],
            'stalled_tickets': unassigned_stalled['stalled'],
            'stalled_count': unassigned_stalled['stalled_count'],
            
            # Section 4: Recent Logs
            'recent_logs': recent_logs,
            
            # Section 5: Statistics
            'stats': stats,
            
            # Section 6: Security (Admin only)
            'security_events': security_data['events'],
            'security_count': security_data['count'],
            'system_healthy': security_data['healthy'],
        })
        
        return context
    
    def _get_responsibility_metrics(self, user, user_role):
        """
        Get metrics for "My Responsibility" section.
        - Regular users: see assigned tickets
        - IT_ADMIN: see assigned tickets + assigned projects
        - Managers: see assigned tickets
        """
        now = timezone.now()
        
        # Tickets assigned to user
        my_assigned_tickets = Ticket.objects.filter(
            assigned_to=user,
            status__in=['NEW', 'OPEN', 'IN_PROGRESS']
        ) if Ticket and user else []
        
        # Tickets created by user
        my_created_tickets = Ticket.objects.filter(
            created_by=user,
            status__in=['NEW', 'OPEN', 'IN_PROGRESS']
        ) if Ticket and user else []
        
        # Combine unique tickets
        my_tickets_set = set()
        my_tickets = []
        
        for ticket in list(my_assigned_tickets) + list(my_created_tickets):
            if ticket.id not in my_tickets_set:
                my_tickets_set.add(ticket.id)
                my_tickets.append(ticket)
        
        # Sort by priority and created date
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        my_tickets.sort(key=lambda t: (priority_order.get(t.priority, 4), t.created_at))
        
        # Count overdue based on SLA
        overdue_count = 0
        for ticket in my_tickets:
            hours_since_created = (now - ticket.created_at).total_seconds() / 3600
            sla_threshold = SLA_THRESHOLDS.get(ticket.priority, 72)
            if hours_since_created > sla_threshold:
                overdue_count += 1
        
        # Get projects for IT_ADMIN users
        my_projects = []
        if user_role == 'IT_ADMIN' and Project and user:
            # Get projects where user is a member
            from apps.projects.models import ProjectMember
            my_projects = Project.objects.filter(
                memberships__user=user,
                memberships__is_active=True,
                status__in=['PLANNING', 'IN_PROGRESS']
            ).distinct() if ProjectMember else []
            my_projects = list(my_projects)[:10]  # Limit to 10 for display
        
        return {
            'my_tickets_count': safe_count(my_tickets),
            'my_assigned_count': safe_count(my_assigned_tickets),
            'my_created_count': safe_count(my_created_tickets),
            'my_overdue_count': overdue_count,
            'my_tickets': my_tickets[:10],  # Limit to 10 for display
            'my_projects': my_projects,
            'my_projects_count': safe_count(my_projects),
        }
    
    def _get_sla_risks(self, user, user_role):
        """
        Get tickets at risk of SLA breach.
        Admin sees all; regular users see only their responsible tickets.
        """
        now = timezone.now()
        risky_tickets = []
        critical_count = 0
        
        base_query = Ticket.objects.filter(
            status__in=['NEW', 'OPEN', 'IN_PROGRESS']
        )
        
        # Non-admins only see their responsible tickets
        is_admin = user.is_superuser or user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
        if not is_admin and user:
            base_query = base_query.filter(
                Q(assigned_to=user) | Q(created_by=user)
            )
        
        tickets = base_query.select_related('assigned_to', 'created_by', 'category')
        
        for ticket in tickets:
            hours_since_created = (now - ticket.created_at).total_seconds() / 3600
            sla_threshold = SLA_THRESHOLDS.get(ticket.priority, 72)
            remaining_hours = sla_threshold - hours_since_created
            
            # Flag as risky if less than 25% time remaining or already breached
            if remaining_hours <= 0:
                risk_level = 'breached'
            elif remaining_hours <= sla_threshold * 0.25:
                risk_level = 'critical'
            elif remaining_hours <= sla_threshold * 0.5:
                risk_level = 'warning'
            else:
                risk_level = 'safe'
            
            if risk_level in ['breached', 'critical', 'warning']:
                risky_tickets.append({
                    'id': ticket.id,
                    'title': ticket.title,
                    'priority': ticket.priority,
                    'status': ticket.status,
                    'created_at': ticket.created_at,
                    'hours_elapsed': round(hours_since_created, 1),
                    'sla_hours': sla_threshold,
                    'remaining_hours': round(remaining_hours, 1),
                    'risk_level': risk_level,
                    'assigned_to': ticket.assigned_to.username if ticket.assigned_to else None,
                    'category': ticket.category.name if ticket.category else None,
                })
                
                if risk_level in ['breached', 'critical']:
                    critical_count += 1
        
        # Sort by risk level (breached first, then critical, then warning)
        risk_order = {'breached': 0, 'critical': 1, 'warning': 2}
        risky_tickets.sort(key=lambda t: (risk_order.get(t['risk_level'], 3), t['hours_elapsed']))
        
        return {
            'risky_tickets': risky_tickets[:10],  # Limit to 10
            'risk_count': len(risky_tickets),
            'critical_count': critical_count,
        }
    
    def _get_unassigned_stalled_tickets(self, user_role):
        """
        Get unassigned and stalled tickets.
        Only admins can see unassigned tickets.
        """
        now = timezone.now()
        stalled_threshold = now - timedelta(hours=STALLED_THRESHOLD_HOURS)
        
        unassigned = []
        stalled = []
        
        # Only admins can see unassigned tickets
        is_admin = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
        
        if is_admin and Ticket:
            # Unassigned tickets
            unassigned_query = Ticket.objects.filter(
                assigned_to__isnull=True,
                status__in=['NEW', 'OPEN']
            ).select_related('created_by', 'category').order_by('created_at')
            
            unassigned = [
                {
                    'id': t.id,
                    'title': t.title,
                    'priority': t.priority,
                    'created_at': t.created_at,
                    'created_by': t.created_by.username if t.created_by else 'Unknown',
                    'category': t.category.name if t.category else None,
                }
                for t in unassigned_query[:10]
            ]
            
            # Stalled tickets (no update for 24+ hours)
            stalled_query = Ticket.objects.filter(
                status__in=['IN_PROGRESS'],
                updated_at__lt=stalled_threshold
            ).select_related('assigned_to', 'category').order_by('updated_at')
            
            stalled = [
                {
                    'id': t.id,
                    'title': t.title,
                    'priority': t.priority,
                    'updated_at': t.updated_at,
                    'assigned_to': t.assigned_to.username if t.assigned_to else 'Unassigned',
                    'hours_stalled': round((now - t.updated_at).total_seconds() / 3600, 1),
                    'category': t.category.name if t.category else None,
                }
                for t in stalled_query[:10]
            ]
        
        return {
            'unassigned': unassigned,
            'unassigned_count': len(unassigned),
            'stalled': stalled,
            'stalled_count': len(stalled),
        }
    
    def _get_recent_logs_for_dashboard(self, activity_service, user, user_role):
        """
        Get recent explainable logs filtered by role.
        Returns pre-formatted, safe-to-render data.
        """
        if not activity_service:
            return []
        
        try:
            # Get logs with role-based filtering
            logs = activity_service.get_activity_logs(
                user=user,
                limit=10,
            )
            
            # Normalize for template (no business logic in template)
            return [
                {
                    'id': log.id,
                    'timestamp': log.timestamp,
                    'actor_username': log.user.username if log.user else 'System',
                    'actor_role': getattr(log.user, 'role', 'VIEWER') if log.user else 'SYSTEM',
                    'action': log.action,
                    'action_label': log.title or log.action.replace('_', ' ').title(),
                    'target_type': log.model_name or '',
                    'target_id': log.object_id,
                    'target_name': log.object_repr or '',
                    'description': log.description,
                    'level': log.level,
                    'level_icon': self._get_level_icon(log.level),
                    'level_color': self._get_level_color(log.level),
                }
                for log in logs
            ]
        except Exception:
            return []
    
    def _get_level_icon(self, level):
        """Get icon for log level."""
        icons = {
            'ERROR': 'fa-exclamation-triangle',
            'WARNING': 'fa-exclamation',
            'SUCCESS': 'fa-check-circle',
            'CRITICAL': 'fa-times-circle',
        }
        return icons.get(level, 'fa-info-circle')
    
    def _get_level_color(self, level):
        """Get color class for log level."""
        colors = {
            'ERROR': 'red',
            'WARNING': 'yellow',
            'SUCCESS': 'green',
            'CRITICAL': 'red',
        }
        return colors.get(level, 'blue')
    
    def _get_stats(self, user_role, is_admin):
        """
        Get pre-computed statistics.
        All filtering done in backend.
        """
        if not Ticket:
            return {}
        
        base_tickets = Ticket.objects.filter(
            status__in=['NEW', 'OPEN', 'IN_PROGRESS']
        )
        
        stats = {
            'open_tickets': base_tickets.count(),
            'new_today': Ticket.objects.filter(
                created_at__date=timezone.now().date()
            ).count() if Ticket else 0,
            'resolved_today': Ticket.objects.filter(
                status='RESOLVED',
                updated_at__date=timezone.now().date()
            ).count() if Ticket else 0,
        }
        
        if is_admin and Asset:
            stats['active_assets'] = Asset.objects.filter(status='ACTIVE').count()
            stats['maintenance_assets'] = Asset.objects.filter(
                status='MAINTENANCE'
            ).count()
        
        if user_role in ['SUPERADMIN', 'MANAGER'] and Project:
            stats['active_projects'] = Project.objects.filter(
                status__in=['PLANNING', 'IN_PROGRESS']
            ).count()
        
        if user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER'] and User:
            stats['active_users'] = User.objects.filter(is_active=True).count()
        
        return stats
    
    def _get_security_data(self, is_admin):
        """
        Get security events for admin users.
        """
        if not is_admin or not SecurityEvent:
            return {'events': [], 'count': 0, 'healthy': True}
        
        try:
            events = SecurityEvent.objects.filter(
                status__in=['OPEN', 'INVESTIGATING']
            ).select_related('affected_user').order_by('-detected_at')[:5]
            
            event_list = [
                {
                    'id': str(e.event_id),
                    'type': e.event_type.replace('_', ' ').title(),
                    'severity': e.severity,
                    'detected_at': e.detected_at,
                    'affected_user': e.affected_user.username if e.affected_user else None,
                }
                for e in events
            ]
            
            return {
                'events': event_list,
                'count': len(event_list),
                'healthy': len(event_list) == 0,
            }
        except Exception:
            return {'events': [], 'count': 0, 'healthy': True}


# =============================================================================
# Helper functions for template-safe data
# =============================================================================

def get_priority_color(priority):
    """Get color class for priority level."""
    colors = {
        'CRITICAL': 'red',
        'HIGH': 'orange',
        'MEDIUM': 'yellow',
        'LOW': 'green',
    }
    return colors.get(priority, 'gray')


def get_status_color(status):
    """Get color class for status."""
    colors = {
        'NEW': 'gray',
        'OPEN': 'blue',
        'IN_PROGRESS': 'yellow',
        'RESOLVED': 'green',
        'CLOSED': 'gray',
    }
    return colors.get(status, 'gray')


@login_required
@require_http_methods(["GET", "POST"])
def dashboard_api(request):
    """
    Dashboard API for AJAX updates with role-based filtering.
    """
    user = request.user
    user_role = getattr(user, 'role', 'VIEWER')
    
    if request.method == 'GET':
        # Determine what the user can access
        can_access_assets = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN']
        can_access_projects = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
        can_access_users = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
        
        # Build stats based on role
        stats = {
            'tickets': Ticket.objects.filter(status__in=['NEW', 'OPEN', 'IN_PROGRESS']).count() if Ticket else 0,
        }
        
        if can_access_assets:
            stats['assets'] = Asset.objects.filter(status='ACTIVE').count() if Asset else 0
        
        if can_access_projects:
            stats['projects'] = Project.objects.filter(status__in=['PLANNING', 'IN_PROGRESS']).count() if Project else 0
        
        if can_access_users:
            stats['users'] = User.objects.filter(is_active=True).count() if User else 0
        
        # Return role-appropriate data
        data = {
            'stats': stats,
            'recent_activity': self._get_filtered_activity(user, user_role) if hasattr(DashboardView, '_get_filtered_activity') else [],
            'alerts': {
                'security_events': SecurityEvent.objects.filter(status__in=['OPEN', 'INVESTIGATING']).count() if SecurityEvent and user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER'] else 0,
                'system_errors': SystemLog.objects.filter(level__in=['ERROR', 'CRITICAL']).count() if SystemLog and user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER'] else 0,
            },
            'user_role': user_role,
            'permissions': {
                'can_access_assets': can_access_assets,
                'can_access_projects': can_access_projects,
                'can_access_users': can_access_users,
                'can_access_logs': user_role in ['SUPERADMIN', 'MANAGER'],
                'can_access_reports': user_role in ['SUPERADMIN', 'MANAGER'],
            }
        }
        return JsonResponse(data)
    
    elif request.method == 'POST':
        # Handle dashboard actions
        action = request.POST.get('action')
        
        if action == 'refresh_stats':
            # Return updated statistics with role filtering
            can_access_assets = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
            can_access_projects = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
            can_access_users = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
            
            stats = {
                'tickets': Ticket.objects.filter(status__in=['NEW', 'OPEN', 'IN_PROGRESS']).count() if Ticket else 0,
            }
            
            if can_access_assets:
                stats['assets'] = Asset.objects.filter(status='ACTIVE').count() if Asset else 0
            
            if can_access_projects:
                stats['projects'] = Project.objects.filter(status__in=['PLANNING', 'IN_PROGRESS']).count() if Project else 0
            
            if can_access_users:
                stats['users'] = User.objects.filter(is_active=True).count() if User else 0
            
            return JsonResponse({
                'success': True,
                'stats': stats,
                'user_role': user_role,
            })
        
        return JsonResponse({'error': 'Invalid action'}, status=400)


@login_required
def search_api(request):
    """
    Global search API with role-based filtering.
    """
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    user = request.user
    user_role = getattr(user, 'role', 'VIEWER')
    
    results = {}
    
    # Determine what the user can access
    can_access_assets = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    can_access_projects = user_role in ['SUPERADMIN', 'MANAGER']
    can_access_users = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    can_access_tickets = True  # All roles can access tickets
    
    if ('all' in search_type or 'users' in search_type) and can_access_users:
        try:
            users = User.objects.filter(username__icontains=query)[:10].values('id', 'username', 'email', 'role')
            results['users'] = list(users)
        except:
            results['users'] = []
    
    if ('all' in search_type or 'assets' in search_type) and can_access_assets:
        try:
            assets = Asset.objects.filter(name__icontains=query)[:10].values('id', 'name', 'asset_tag', 'category__name', 'status')
            results['assets'] = list(assets)
        except:
            results['assets'] = []
    
    if ('all' in search_type or 'projects' in search_type) and can_access_projects:
        try:
            projects = Project.objects.filter(name__icontains=query)[:10].values('id', 'name', 'status', 'priority')
            results['projects'] = list(projects)
        except:
            results['projects'] = []
    
    if ('all' in search_type or 'tickets' in search_type) and can_access_tickets:
        try:
            tickets = Ticket.objects.filter(title__icontains=query)[:10].values('id', 'title', 'status', 'priority', 'ticket_id')
            results['tickets'] = list(tickets)
        except:
            results['tickets'] = []
    
    return JsonResponse({
        'query': query,
        'results': results,
        'count': sum(len(category) for category in results.values())
    })


@login_required
def notifications_api(request):
    """
    Notifications API for real-time updates.
    """
    user = request.user
    user_role = getattr(user, 'role', 'VIEWER')
    
    # Get notifications based on role
    notifications = []
    
    # All roles get welcome notification if new
    notifications.append({
        'id': 1,
        'title': 'Welcome to IT Management Platform',
        'message': 'Your account has been successfully created.',
        'timestamp': timezone.now().isoformat(),
        'read': False,
        'type': 'info'
    })
    
    # Add role-specific notifications
    if user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']:
        notifications.append({
            'id': 2,
            'title': 'System Overview',
            'message': 'You have access to all management features.',
            'timestamp': timezone.now().isoformat(),
            'read': False,
            'type': 'info'
        })
    
    return JsonResponse({
        'notifications': notifications,
        'unread_count': len([n for n in notifications if not n['read']])
    })


@login_required
def quick_actions(request):
    """
    Quick actions for common tasks with role-based access.
    """
    user = request.user
    user_role = getattr(user, 'role', 'VIEWER')
    action = request.POST.get('action')
    
    if action == 'create_ticket':
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        # All roles can create tickets
        if title and Ticket:
            ticket = Ticket.objects.create(
                title=title,
                description=description,
                created_by=request.user,
                status='NEW'
            )
            return JsonResponse({
                'success': True,
                'message': 'Ticket created successfully',
                'ticket_id': ticket.id
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Title is required'
            }, status=400)
    
    elif action == 'create_project':
        # Only SUPERADMIN and MANAGER can create projects
        if user_role not in ['SUPERADMIN', 'MANAGER']:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to create projects'
            }, status=403)
        
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if name and Project:
            project = Project.objects.create(
                name=name,
                description=description,
                created_by=request.user,
                status='PLANNING'
            )
            return JsonResponse({
                'success': True,
                'message': 'Project created successfully',
                'project_id': project.id
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Name is required'
            }, status=400)
    
    return JsonResponse({'error': 'Invalid action'}, status=400)


def frontend_context(request):
    """
    Add common context variables to all frontend views.
    """
    user = request.user
    user_role = getattr(user, 'role', None) if user.is_authenticated else None
    
    return {
        'site_name': 'IT Management Platform',
        'user_role': user_role,
        'current_path': request.path,
        'debug': settings.DEBUG,
    }


def dashboard_stats_context(request):
    """
    Add dashboard statistics to context with role-based filtering.
    """
    if not request.user.is_authenticated:
        return {}
    
    user = request.user
    user_role = getattr(user, 'role', 'VIEWER')
    
    # Determine what the user can access
    can_access_assets = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    can_access_projects = user_role in ['SUPERADMIN', 'MANAGER']
    can_access_users = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    can_access_logs = user_role in ['SUPERADMIN', 'MANAGER']
    
    stats = {
        'active_users': User.objects.filter(is_active=True).count() if User and can_access_users else 0,
        'total_assets': Asset.objects.count() if Asset and can_access_assets else 0,
        'active_projects': Project.objects.filter(status='ACTIVE').count() if Project and can_access_projects else 0,
        'open_tickets': Ticket.objects.filter(status__in=['NEW', 'OPEN']).count() if Ticket else 0,
    }
    
    return {
        'dashboard_stats': stats,
        'can_access_assets': can_access_assets,
        'can_access_projects': can_access_projects,
        'can_access_users': can_access_users,
        'can_access_logs': can_access_logs,
    }


# Wrapper functions for URL patterns
def dashboard(request):
    """Main dashboard view."""
    view = DashboardView.as_view()
    return view(request)


# =============================================================================
# COMMAND PALETTE API
# =============================================================================

@login_required
def command_palette_api(request):
    """
    Command Palette API for Ctrl+K functionality.
    
    Returns available commands based on user role.
    All permission filtering done in backend - template receives safe data.
    """
    from apps.frontend.command_palette import get_command_palette_data, resolve_command
    
    if request.method == 'GET':
        # Return available commands for the user
        data = get_command_palette_data(request.user)
        return JsonResponse(data)
    
    elif request.method == 'POST':
        # Resolve a command execution
        import json
        try:
            body = json.loads(request.body)
            command_key = body.get('command_key')
            input_value = body.get('input_value')
            
            result = resolve_command(command_key, input_value)
            return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({
                'type': 'error',
                'message': 'Invalid request body'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'type': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

