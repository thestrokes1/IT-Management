"""
Dashboard views for IT Management Platform.
Contains DashboardView and related API endpoints.
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
from django.utils import timezone
from datetime import timedelta, datetime, date
import json

try:
    from apps.users.models import User
    from apps.assets.models import Asset
    from apps.projects.models import Project
    from apps.tickets.models import Ticket, TicketComment
    from apps.logs.models import ActivityLog, SecurityEvent, SystemLog
except ImportError:
    User = None
    Asset = None
    Project = None
    Ticket = None
    ActivityLog = None
    SecurityEvent = None
    SystemLog = None


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view showing overview of all modules.
    Role-based filtering applied based on user permissions.
    """
    template_name = 'frontend/dashboard.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_role = getattr(user, 'role', 'VIEWER')
        
        # Determine what the user can access based on role
        can_access_assets = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
        can_access_projects = user_role in ['SUPERADMIN', 'MANAGER']
        can_access_users = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
        can_access_logs = user_role in ['SUPERADMIN', 'MANAGER']
        can_access_reports = user_role in ['SUPERADMIN', 'MANAGER']
        
        # Get recent activity (filtered based on user permissions)
        try:
            if user_role in ['SUPERADMIN', 'MANAGER']:
                # Admins and Managers see all activity
                recent_logs = ActivityLog.objects.select_related('user', 'category').order_by('-timestamp')[:10]
            elif user_role in ['IT_ADMIN']:
                # IT Admins see all activity except logs
                recent_logs = ActivityLog.objects.select_related('user', 'category').order_by('-timestamp')[:10]
            else:
                # Technicians and Viewers see only ticket-related activity
                recent_logs = ActivityLog.objects.select_related('user', 'category').filter(
                    category__in=['ticket', 'asset']
                ).order_by('-timestamp')[:10]
        except:
            recent_logs = []
        
        # Get dashboard statistics based on role
        stats = {
            'user_count': 0,
            'asset_count': 0,
            'project_count': 0,
            'ticket_count': 0,
            'security_events': 0,
            'system_errors': 0,
        }
        
        # All roles can see ticket counts
        stats['ticket_count'] = Ticket.objects.filter(status__in=['NEW', 'OPEN', 'IN_PROGRESS']).count() if Ticket else 0
        
        # Assets, Projects, Users stats based on role
        if can_access_assets:
            stats['asset_count'] = Asset.objects.filter(status='ACTIVE').count() if Asset else 0
        
        if can_access_projects:
            stats['project_count'] = Project.objects.filter(status__in=['PLANNING', 'IN_PROGRESS']).count() if Project else 0
        
        if can_access_users:
            stats['user_count'] = User.objects.filter(is_active=True).count() if User else 0
        
        # Security events and system errors for admin roles
        if user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']:
            stats['security_events'] = SecurityEvent.objects.filter(status__in=['OPEN', 'INVESTIGATING']).count() if SecurityEvent else 0
            stats['system_errors'] = SystemLog.objects.filter(level__in=['ERROR', 'CRITICAL']).count() if SystemLog else 0
        
        context.update({
            'recent_logs': recent_logs,
            'user_count': stats['user_count'],
            'asset_count': stats['asset_count'],
            'project_count': stats['project_count'],
            'ticket_count': stats['ticket_count'],
            'security_events': stats['security_events'],
            'system_errors': stats['system_errors'],
            # Role flags for template
            'can_access_assets': can_access_assets,
            'can_access_projects': can_access_projects,
            'can_access_users': can_access_users,
            'can_access_logs': can_access_logs,
            'can_access_reports': can_access_reports,
            'user_role': user_role,
        })
        
        return context


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
        can_access_assets = user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
        can_access_projects = user_role in ['SUPERADMIN', 'MANAGER']
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
            can_access_projects = user_role in ['SUPERADMIN', 'MANAGER']
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

