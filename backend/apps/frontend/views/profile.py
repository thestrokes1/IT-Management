"""
Profile views for IT Management Platform.
Contains user profile, logs, and reports views.
"""

from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
import csv
import json

try:
    from apps.users.models import User
    from apps.assets.models import Asset
    from apps.projects.models import Project
    from apps.tickets.models import Ticket
    from apps.logs.models import ActivityLog, SecurityEvent, SystemLog
except ImportError:
    User = None
    Asset = None
    Project = None
    Ticket = None
    ActivityLog = None
    SecurityEvent = None
    SystemLog = None


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    User profile view.
    
    Displays user information and "My Ticket History" section showing:
    - Tickets created by the user (ticket.created_by = user)
    - Tickets assigned to the user (ticket.assigned_to = user)
    
    Implements RBAC - only shows tickets the logged-in user is authorized to see.
    Supports filtering by status and priority.
    
    Uses TicketQueryService for Clean Architecture separation.
    """
    template_name = 'frontend/profile.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        """
        Build context for profile page with user's ticket history.
        
        This method:
        1. Fetches the logged-in user
        2. Uses TicketQueryService to get tickets (created OR assigned)
        3. Calculates statistics
        4. Gets available filters based on user's tickets
        5. Applies any GET filters (status, priority)
        6. Returns all data for template rendering
        """
        context = super().get_context_data(**kwargs)
        request = self.request
        current_user = request.user
        
        # =====================================================================
        # Read filter parameters from GET request
        # =====================================================================
        status_filter = request.GET.get('status', '')
        priority_filter = request.GET.get('priority', '')
        page = int(request.GET.get('page', 1))
        
        # Empty strings become None for filtering
        status_filter = status_filter if status_filter else None
        priority_filter = priority_filter if priority_filter else None
        
        # =====================================================================
        # Use TicketQueryService for Clean Architecture
        # =====================================================================
        try:
            from apps.tickets.services.ticket_query_service import TicketQueryService
            
            ticket_service = TicketQueryService()
            
            # Get user's tickets with optional filtering
            # This fetches tickets where:
            # - created_by = current_user OR assigned_to = current_user
            # - Plus optional status/priority filters
            tickets_result = ticket_service.get_user_tickets(
                user=current_user,
                status_filter=status_filter,
                priority_filter=priority_filter,
                page=page,
                page_size=10  # Show 10 tickets per page
            )
            
            # Get statistics for quick stats cards
            stats = ticket_service.get_user_ticket_stats(user=current_user)
            
            # Check if user can reopen tickets (RBAC)
            can_reopen_ticket = ticket_service.can_user_reopen_ticket(user=current_user)
            
            # Get available filter options based on user's tickets
            available_filters = ticket_service.get_available_filters(user=current_user)
            
        except ImportError:
            # Fallback if service is not available
            print("[PROFILE_VIEW] TicketQueryService not available, using fallback")
            tickets_result = self._get_tickets_fallback(
                current_user, status_filter, priority_filter, page
            )
            stats = self._get_stats_fallback(current_user)
            can_reopen_ticket = self._check_reopen_permission(current_user)
            available_filters = {'statuses': [], 'priorities': []}
        
        # =====================================================================
        # Update context with all data for template
        # =====================================================================
        context.update({
            'user': current_user,
            'my_tickets': tickets_result['tickets'],
            'ticket_pagination': {
                'page': tickets_result['page'],
                'page_size': tickets_result['page_size'],
                'total_count': tickets_result['total_count'],
                'total_pages': tickets_result['total_pages'],
                'has_next': tickets_result['has_next'],
                'has_previous': tickets_result['has_previous'],
            },
            'stats': stats,
            'can_reopen_ticket': can_reopen_ticket,
            'available_filters': available_filters,
            'current_filters': {
                'status': status_filter,
                'priority': priority_filter,
            },
        })
        
        return context
    
    def _get_tickets_fallback(self, user, status_filter, priority_filter, page):
        """Fallback method if TicketQueryService is not available."""
        base_query = Q(created_by=user) | Q(assigned_to=user)
        
        if status_filter:
            base_query &= Q(status=status_filter)
        if priority_filter:
            base_query &= Q(priority=priority_filter)
        
        tickets_qs = Ticket.objects.filter(base_query).select_related(
            'created_by', 'assigned_to', 'category', 'updated_by'
        ).order_by('-created_at')
        
        from django.core.paginator import Paginator
        paginator = Paginator(tickets_qs, 10)
        
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        tickets_list = []
        for ticket in page_obj.object_list:
            tickets_list.append({
                'id': ticket.id,
                'title': ticket.title,
                'status': ticket.status,
                'priority': ticket.priority,
                'category': ticket.category.name if ticket.category else None,
                'created_at': ticket.created_at,
                'updated_at': ticket.updated_at,
                'created_by': {
                    'id': ticket.created_by.id if ticket.created_by else None,
                    'username': ticket.created_by.username if ticket.created_by else 'System',
                },
                'updated_by': {
                    'id': ticket.updated_by.id if ticket.updated_by else None,
                    'username': ticket.updated_by.username if ticket.updated_by else None,
                },
                'assigned_to': {
                    'id': ticket.assigned_to.id if ticket.assigned_to else None,
                    'username': ticket.assigned_to.username if ticket.assigned_to else None,
                },
                'status_display': ticket.get_status_display(),
                'priority_display': ticket.get_priority_display(),
            })
        
        return {
            'tickets': tickets_list,
            'page': page,
            'page_size': 10,
            'total_count': paginator.count,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    
    def _get_stats_fallback(self, user):
        """Fallback statistics if service is unavailable."""
        user_tickets_query = Q(created_by=user) | Q(assigned_to=user)
        
        return {
            'total': Ticket.objects.filter(user_tickets_query).distinct().count(),
            'created': Ticket.objects.filter(created_by=user).count(),
            'assigned': Ticket.objects.filter(assigned_to=user).count(),
            'resolved': Ticket.objects.filter(
                user_tickets_query, status='RESOLVED'
            ).distinct().count(),
            'open': Ticket.objects.filter(
                user_tickets_query,
                status__in=['NEW', 'OPEN', 'IN_PROGRESS']
            ).distinct().count(),
            'can_reopen': Ticket.objects.filter(
                user_tickets_query,
                status__in=['RESOLVED', 'CLOSED']
            ).distinct().count(),
        }
    
    def _check_reopen_permission(self, user):
        """Fallback RBAC check if service is unavailable."""
        if not user:
            return False
        user_role = getattr(user, 'role', 'VIEWER') if user else None
        return user.is_superuser or user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']


class LogsView(LoginRequiredMixin, TemplateView):
    """
    Logs management web interface with server-side filtering.
    """
    template_name = 'frontend/logs.html'
    login_url = 'frontend:login'
    
    def _clean(self, value):
        """Normalize GET parameter: empty strings become None."""
        return value.strip() if hasattr(value, 'strip') else value
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from django.contrib.auth import get_user_model
            from apps.logs.services.activity_service import ActivityService
            from datetime import datetime
            
            User = get_user_model()
            service = ActivityService()
            request = self.request
            
            # Read and normalize GET parameters for filtering
            raw_search = request.GET.get('search', '')
            raw_username = request.GET.get('username', '')
            raw_action = request.GET.get('action', '')
            raw_actor_role = request.GET.get('actor_role', '')
            raw_start_date = request.GET.get('start_date', '')
            raw_end_date = request.GET.get('end_date', '')
            raw_hour_from = request.GET.get('hour_from', '')
            raw_hour_to = request.GET.get('hour_to', '')
            
            # Normalize: empty strings become None
            search = self._clean(raw_search) or None
            username = self._clean(raw_username) or None
            action = self._clean(raw_action) or None
            actor_role = self._clean(raw_actor_role) or None
            hour_from = self._clean(raw_hour_from) or None
            hour_to = self._clean(raw_hour_to) or None
            
            # Parse dates
            start_date = None
            end_date = None
            if raw_start_date:
                try:
                    start_date = datetime.strptime(raw_start_date, '%Y-%m-%d').date()
                except ValueError:
                    pass
            if raw_end_date:
                try:
                    end_date = datetime.strptime(raw_end_date, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            # Call ActivityService with filters (includes RBAC)
            recent_logs = service.get_activity_logs(
                user=request.user,
                search=search,
                username=username,
                action=action,
                actor_role=actor_role,
                start_date=start_date,
                end_date=end_date,
                hour_from=hour_from,
                hour_to=hour_to,
                limit=100
            )
            
            security_events = SecurityEvent.objects.select_related('affected_user').order_by('-detected_at')[:50]
            all_users = User.objects.all().order_by('username')
        except Exception as e:
            import traceback
            print(f"[LOGS_VIEW] Error: {e}")
            traceback.print_exc()
            recent_logs = []
            security_events = []
            all_users = []
        
        context.update({
            'recent_logs': recent_logs,
            'security_events': security_events,
            'all_users': all_users
        })
        return context


class ReportsView(LoginRequiredMixin, TemplateView):
    """
    Reports and analytics web interface with audit-grade activity logging.
    """
    template_name = 'frontend/reports.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        
        # Check RBAC permissions
        user_role = getattr(request.user, 'role', 'VIEWER') if request.user else None
        is_admin = request.user and (
            request.user.is_superuser or 
            user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
        )
        
        try:
            # Basic counts with permission checks
            if is_admin:
                total_assets = Asset.objects.count() if Asset else 0
                active_users = User.objects.filter(is_active=True).count() if User else 0
            else:
                total_assets = Asset.objects.filter(
                    Q(assigned_to=request.user) | Q(assigned_to__isnull=True)
                ).count() if Asset else 0
                active_users = 1
            
            active_projects = Project.objects.filter(status__in=['PLANNING', 'ACTIVE']).count() if Project else 0
            open_tickets = Ticket.objects.filter(status__in=['NEW', 'OPEN', 'IN_PROGRESS']).count() if Ticket else 0
            recent_security_events = SecurityEvent.objects.filter(
                detected_at__gte=timezone.now() - timedelta(days=7)
            ).count() if SecurityEvent else 0
            
            # Recent Tickets with full audit information
            if Ticket:
                if is_admin:
                    recent_tickets = Ticket.objects.select_related(
                        'created_by', 'category', 'assigned_to'
                    ).order_by('-created_at')[:20]
                else:
                    recent_tickets = Ticket.objects.filter(
                        Q(created_by=request.user) | Q(assigned_to=request.user)
                    ).select_related('created_by', 'category', 'assigned_to').order_by('-created_at')[:20]
            else:
                recent_tickets = []
            
            # Ticket Statistics
            tickets_by_priority = {}
            tickets_by_status = {}
            total_tickets = 0
            if Ticket:
                for status, label in Ticket.STATUS_CHOICES:
                    count = Ticket.objects.filter(status=status).count()
                    tickets_by_status[status] = {'label': label, 'count': count}
                    total_tickets += count
                for priority, label in Ticket.PRIORITY_CHOICES:
                    tickets_by_priority[priority] = {'label': label, 'count': Ticket.objects.filter(priority=priority).count()}
            
            # Asset Status Distribution
            asset_status_distribution = {}
            if Asset:
                for status, label in Asset.STATUS_CHOICES:
                    asset_status_distribution[status] = {'label': label, 'count': Asset.objects.filter(status=status).count()}
            
            # Recent Activity Logs with full audit-grade details
            from apps.logs.services.activity_service import ActivityService
            service = ActivityService()
            
            recent_activities = service.get_activity_logs(user=request.user, limit=30)
            
            # Build structured activity data for template
            structured_activities = []
            for activity in recent_activities:
                target_type = activity.model_name or ''
                target_id = activity.object_id
                target_url = '#'
                if target_type == 'ticket' and target_id:
                    target_url = f'/tickets/{target_id}/'
                elif target_type == 'asset' and target_id:
                    target_url = f'/assets/{target_id}/'
                elif target_type == 'project' and target_id:
                    target_url = f'/projects/{target_id}/'
                elif target_type == 'user' and target_id:
                    target_url = f'/users/{target_id}/'
                
                actor_username = activity.extra_data.get('actor_username') or activity.user.username if activity.user else 'System'
                actor_id = activity.extra_data.get('actor_id') or activity.user.id if activity.user else None
                
                changes_summary = ''
                extra_data = activity.extra_data or {}
                
                if 'from_status' in extra_data and 'to_status' in extra_data:
                    changes_summary = f"Status: {extra_data['from_status']} → {extra_data['to_status']}"
                elif 'from_priority' in extra_data and 'to_priority' in extra_data:
                    changes_summary = f"Priority: {extra_data['from_priority']} → {extra_data['to_priority']}"
                elif 'from_assignee' in extra_data and 'to_assignee' in extra_data:
                    changes_summary = f"Assignee: {extra_data['from_assignee']} → {extra_data['to_assignee']}"
                elif 'changes' in extra_data:
                    changes_summary = extra_data['changes']
                elif activity.description:
                    changes_summary = activity.description
                
                action_icon = self._get_action_icon(activity.action)
                action_color = self._get_action_color(activity.action)
                
                structured_activities.append({
                    'id': activity.log_id,
                    'timestamp': activity.timestamp,
                    'actor': {
                        'username': actor_username,
                        'id': actor_id,
                        'role': activity.extra_data.get('actor_role', activity.user.role if activity.user else 'VIEWER')
                    },
                    'action': activity.action,
                    'action_label': service._get_action_label(activity.action),
                    'action_icon': action_icon,
                    'action_color': action_color,
                    'entity': {
                        'type': target_type.capitalize() if target_type else 'System',
                        'id': target_id,
                        'name': activity.object_repr or '',
                        'url': target_url
                    },
                    'changes_summary': changes_summary,
                    'level': activity.level,
                    'description': activity.description,
                    'ip_address': activity.ip_address,
                })
            
        except Exception as e:
            import traceback
            print(f"[REPORTS_VIEW] Error: {e}")
            traceback.print_exc()
            total_assets = 0
            active_projects = 0
            open_tickets = 0
            active_users = 0
            recent_security_events = 0
            recent_tickets = []
            tickets_by_priority = {}
            tickets_by_status = {}
            asset_status_distribution = {}
            structured_activities = []
        
        context.update({
            'total_assets': total_assets,
            'active_projects': active_projects,
            'open_tickets': open_tickets,
            'active_users': active_users,
            'recent_security_events': recent_security_events,
            'recent_tickets': recent_tickets,
            'tickets_by_priority': tickets_by_priority,
            'tickets_by_status': tickets_by_status,
            'total_tickets': total_tickets,
            'asset_status_distribution': asset_status_distribution,
            'recent_activities': structured_activities,
            'is_admin': is_admin,
        })
        
        return context
    
    def _get_action_icon(self, action):
        """Get icon class for an action."""
        icons = {
            'TICKET_CREATED': 'fa-ticket-alt',
            'TICKET_UPDATED': 'fa-edit',
            'TICKET_ASSIGNED': 'fa-user-plus',
            'TICKET_RESOLVED': 'fa-check-circle',
            'TICKET_DELETED': 'fa-trash',
            'ASSET_CREATED': 'fa-desktop',
            'ASSET_UPDATED': 'fa-edit',
            'ASSET_ASSIGNED': 'fa-hand-paper',
            'ASSET_DELETED': 'fa-trash',
            'PROJECT_CREATED': 'fa-project-diagram',
            'PROJECT_UPDATED': 'fa-edit',
            'PROJECT_DELETED': 'fa-trash',
            'USER_CREATED': 'fa-user-plus',
            'USER_LOGIN': 'fa-sign-in-alt',
            'USER_LOGOUT': 'fa-sign-out-alt',
            'USER_UPDATED': 'fa-edit',
        }
        return icons.get(action, 'fa-circle')
    
    def _get_action_color(self, action):
        """Get color class for an action type."""
        colors = {
            'CREATED': 'text-green-500',
            'DELETED': 'text-red-500',
            'ASSIGNED': 'text-blue-500',
            'RESOLVED': 'text-green-600',
            'LOGIN': 'text-green-500',
            'LOGOUT': 'text-gray-500',
        }
        for key, color in colors.items():
            if key in action:
                return color
        return 'text-blue-500'


# Wrapper functions for URL patterns
def profile(request):
    """User profile view."""
    view = ProfileView.as_view()
    return view(request)


def logs(request):
    """Logs view."""
    view = LogsView.as_view()
    return view(request)


def reports(request):
    """Reports view."""
    view = ReportsView.as_view()
    return view(request)


@login_required
def profile_reopen_ticket(request, ticket_id):
    """
    Reopen a ticket from the profile page.
    
    RBAC: Only admins (SUPERADMIN, IT_ADMIN, MANAGER) can reopen tickets.
    User must also be the creator or assignee of the ticket.
    
    Args:
        request: The HTTP request object
        ticket_id: The ID of the ticket to reopen
    
    Returns:
        Redirects back to the profile page with a success/error message
    """
    from django.db import transaction
    from apps.logs.services.activity_service import ActivityService
    
    user = request.user
    user_role = getattr(user, 'role', 'VIEWER') if user else None
    
    # RBAC Check: Only admins can reopen tickets
    can_reopen = user.is_superuser or user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    
    if not can_reopen:
        messages.error(request, "You don't have permission to reopen tickets.")
        return redirect('frontend:profile')
    
    # Get the ticket
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Verify the ticket can be reopened (must be RESOLVED or CLOSED)
    if ticket.status not in ['RESOLVED', 'CLOSED']:
        messages.error(request, f"Cannot reopen ticket #{ticket_id}. Only resolved or closed tickets can be reopened.")
        return redirect('frontend:profile')
    
    # Verify user has access to this ticket (created or assigned)
    if ticket.created_by != user and ticket.assigned_to != user:
        messages.error(request, "You don't have permission to reopen this ticket.")
        return redirect('frontend:profile')
    
    try:
        with transaction.atomic():
            # Store old status for activity log
            old_status = ticket.status
            
            # Reopen the ticket - set to IN_PROGRESS
            ticket.status = 'IN_PROGRESS'
            ticket.updated_by = user
            ticket.save(update_fields=['status', 'updated_by', 'updated_at'])
            
            # Log the activity
            ActivityService.log_activity(
                user=user,
                action='TICKET_REOPENED',
                model_name='ticket',
                object_id=ticket.id,
                object_repr=str(ticket),
                description=f"Ticket reopened from {old_status} to IN_PROGRESS",
                request=request
            )
            
            messages.success(request, f"Ticket #{ticket_id} has been reopened successfully.")
            
    except Exception as e:
        import traceback
        print(f"[PROFILE_REOPEN_TICKET] Error: {e}")
        traceback.print_exc()
        messages.error(request, f"Error reopening ticket: {str(e)}")
    
    return redirect('frontend:profile')


@login_required
def export_reports(request):
    """
    Export reports data in various formats (CSV, Excel, PDF).
    
    Supports RBAC - users only see data they are authorized to view.
    """
    export_format = request.POST.get('export_format', 'csv')
    
    # Check RBAC permissions
    user_role = getattr(request.user, 'role', 'VIEWER') if request.user else None
    is_admin = request.user and (
        request.user.is_superuser or 
        user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    )
    
    # Collect report data based on permissions
    try:
        # Recent Tickets with full audit information
        if Ticket:
            if is_admin:
                recent_tickets = list(Ticket.objects.select_related(
                    'created_by', 'category', 'assigned_to'
                ).order_by('-created_at')[:50])
            else:
                recent_tickets = list(Ticket.objects.filter(
                    Q(created_by=request.user) | Q(assigned_to=request.user)
                ).select_related('created_by', 'category', 'assigned_to').order_by('-created_at')[:50])
        else:
            recent_tickets = []
        
        # Recent Activity Logs
        from apps.logs.services.activity_service import ActivityService
        service = ActivityService()
        recent_activities = list(service.get_activity_logs(user=request.user, limit=50))
        
        # Asset status distribution
        asset_stats = {}
        if Asset:
            for status, label in Asset.STATUS_CHOICES:
                asset_stats[status] = {'label': label, 'count': Asset.objects.filter(status=status).count()}
        
        # Ticket status distribution
        ticket_stats = {}
        if Ticket:
            for status, label in Ticket.STATUS_CHOICES:
                ticket_stats[status] = {'label': label, 'count': Ticket.objects.filter(status=status).count()}
    except Exception as e:
        import traceback
        print(f"[EXPORT_REPORTS] Error: {e}")
        traceback.print_exc()
        recent_tickets = []
        recent_activities = []
        asset_stats = {}
        ticket_stats = {}
    
    # Generate export based on format
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reports_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow(['IT Management Platform - Reports Export'])
        writer.writerow([f'Generated at: {timezone.now()}'])
        writer.writerow([f'Exported by: {request.user.username}'])
        writer.writerow([])
        
        # Write asset status distribution
        writer.writerow(['Asset Status Distribution'])
        writer.writerow(['Status', 'Count', 'Percentage'])
        total_assets = sum(s['count'] for s in asset_stats.values())
        for status, data in asset_stats.items():
            percent = (data['count'] / total_assets * 100) if total_assets > 0 else 0
            writer.writerow([data['label'], data['count'], f'{percent:.1f}%'])
        writer.writerow([])
        
        # Write ticket status distribution
        writer.writerow(['Ticket Status Distribution'])
        writer.writerow(['Status', 'Count', 'Percentage'])
        total_tickets = sum(s['count'] for s in ticket_stats.values())
        for status, data in ticket_stats.items():
            percent = (data['count'] / total_tickets * 100) if total_tickets > 0 else 0
            writer.writerow([data['label'], data['count'], f'{percent:.1f}%'])
        writer.writerow([])
        
        # Write recent tickets
        writer.writerow(['Recent Tickets'])
        writer.writerow(['ID', 'Title', 'Status', 'Priority', 'Created By', 'Created Date', 'Last Modified By'])
        for ticket in recent_tickets:
            writer.writerow([
                ticket.id,
                ticket.title,
                ticket.get_status_display() if hasattr(ticket, 'get_status_display') else ticket.status,
                ticket.get_priority_display() if hasattr(ticket, 'get_priority_display') else ticket.priority,
                ticket.created_by.username if ticket.created_by else 'System',
                ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                ticket.updated_by.username if ticket.updated_by else (ticket.created_by.username if ticket.created_by else 'System'),
            ])
        writer.writerow([])
        
        # Write recent activity logs
        writer.writerow(['Recent Activity Logs (Audit Trail)'])
        writer.writerow(['Timestamp', 'Actor', 'Action', 'Entity', 'Entity ID', 'Changes Summary', 'IP Address', 'Level'])
        for activity in recent_activities:
            actor_username = activity.extra_data.get('actor_username') or activity.user.username if activity.user else 'System'
            writer.writerow([
                activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                actor_username,
                service._get_action_label(activity.action),
                activity.model_name or 'System',
                activity.object_id or '',
                activity.description,
                activity.ip_address or '',
                activity.level,
            ])
        
        return response
    
    elif export_format == 'excel':
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="reports_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xls"'
        
        response.write('IT Management Platform - Reports Export\t\n')
        response.write(f'Generated at:\t{timezone.now()}\t\n')
        response.write(f'Exported by:\t{request.user.username}\t\n\t\n')
        
        return response
    
    elif export_format == 'json':
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="reports_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        export_data = {
            'export_info': {
                'generated_at': timezone.now().isoformat(),
                'exported_by': request.user.username,
                'format': 'json',
            },
            'asset_status_distribution': asset_stats,
            'ticket_status_distribution': ticket_stats,
            'recent_tickets': [
                {
                    'id': t.id,
                    'title': t.title,
                    'status': t.status,
                    'priority': t.priority,
                    'created_by': t.created_by.username if t.created_by else 'System',
                    'created_at': t.created_at.isoformat() if t.created_at else None,
                }
                for t in recent_tickets
            ],
            'recent_activities': [
                {
                    'timestamp': a.timestamp.isoformat() if a.timestamp else None,
                    'actor': a.extra_data.get('actor_username') or a.user.username if a.user else 'System',
                    'action': a.action,
                    'entity': a.model_name or 'System',
                    'entity_id': a.object_id,
                    'changes_summary': a.description,
                    'ip_address': a.ip_address,
                    'level': a.level,
                }
                for a in recent_activities
            ],
        }
        
        response.write(json.dumps(export_data, indent=2))
        return response
    
    else:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reports_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        return response
