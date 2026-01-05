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
    """
    template_name = 'frontend/dashboard.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get recent activity
        try:
            recent_logs = ActivityLog.objects.select_related('user', 'category').order_by('-timestamp')[:10]
        except:
            recent_logs = []
        
        # Get dashboard statistics
        context.update({
            'recent_logs': recent_logs,
            'user_count': User.objects.filter(is_active=True).count() if User else 0,
            'asset_count': Asset.objects.filter(status='ACTIVE').count() if Asset else 0,
            'project_count': Project.objects.filter(status__in=['PLANNING', 'IN_PROGRESS']).count() if Project else 0,
            'ticket_count': Ticket.objects.filter(status__in=['NEW', 'OPEN', 'IN_PROGRESS']).count() if Ticket else 0,
            'security_events': SecurityEvent.objects.filter(status__in=['OPEN', 'INVESTIGATING']).count() if SecurityEvent else 0,
            'system_errors': SystemLog.objects.filter(level__in=['ERROR', 'CRITICAL']).count() if SystemLog else 0,
        })
        
        return context


@login_required
@require_http_methods(["GET", "POST"])
def dashboard_api(request):
    """
    Dashboard API for AJAX updates.
    """
    if request.method == 'GET':
        # Return dashboard data
        data = {
            'stats': {
                'users': User.objects.filter(is_active=True).count() if User else 0,
                'assets': Asset.objects.filter(status='ACTIVE').count() if Asset else 0,
                'projects': Project.objects.filter(status__in=['PLANNING', 'IN_PROGRESS']).count() if Project else 0,
                'tickets': Ticket.objects.filter(status__in=['NEW', 'OPEN', 'IN_PROGRESS']).count() if Ticket else 0,
            },
            'recent_activity': list(ActivityLog.objects.select_related('user').order_by('-timestamp')[:5].values(
                'id', 'title', 'description', 'timestamp', 'user__username'
            )) if ActivityLog else [],
            'alerts': {
                'security_events': SecurityEvent.objects.filter(status__in=['OPEN', 'INVESTIGATING']).count() if SecurityEvent else 0,
                'system_errors': SystemLog.objects.filter(level__in=['ERROR', 'CRITICAL']).count() if SystemLog else 0,
            }
        }
        return JsonResponse(data)
    
    elif request.method == 'POST':
        # Handle dashboard actions
        action = request.POST.get('action')
        
        if action == 'refresh_stats':
            # Return updated statistics
            return JsonResponse({
                'success': True,
                'stats': {
                    'users': User.objects.filter(is_active=True).count() if User else 0,
                    'assets': Asset.objects.filter(status='ACTIVE').count() if Asset else 0,
                    'projects': Project.objects.filter(status__in=['PLANNING', 'IN_PROGRESS']).count() if Project else 0,
                    'tickets': Ticket.objects.filter(status__in=['NEW', 'OPEN', 'IN_PROGRESS']).count() if Ticket else 0,
                }
            })
        
        return JsonResponse({'error': 'Invalid action'}, status=400)


@login_required
def search_api(request):
    """
    Global search API.
    """
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    
    results = {}
    
    if 'all' in search_type or 'users' in search_type:
        try:
            users = User.objects.filter(username__icontains=query)[:10].values('id', 'username', 'email', 'role')
            results['users'] = list(users)
        except:
            results['users'] = []
    
    if 'all' in search_type or 'assets' in search_type:
        try:
            assets = Asset.objects.filter(name__icontains=query)[:10].values('id', 'name', 'asset_tag', 'category__name', 'status')
            results['assets'] = list(assets)
        except:
            results['assets'] = []
    
    if 'all' in search_type or 'projects' in search_type:
        try:
            projects = Project.objects.filter(name__icontains=query)[:10].values('id', 'name', 'status', 'priority')
            results['projects'] = list(projects)
        except:
            results['projects'] = []
    
    if 'all' in search_type or 'tickets' in search_type:
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
    
    # Get unread notifications (this would be more sophisticated in production)
    notifications = [
        {
            'id': 1,
            'title': 'Welcome to IT Management Platform',
            'message': 'Your account has been successfully created.',
            'timestamp': timezone.now().isoformat(),
            'read': False,
        }
    ]
    
    return JsonResponse({
        'notifications': notifications,
        'unread_count': len([n for n in notifications if not n['read']])
    })


@login_required
def quick_actions(request):
    """
    Quick actions for common tasks.
    """
    action = request.POST.get('action')
    
    if action == 'create_ticket':
        title = request.POST.get('title')
        description = request.POST.get('description')
        
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
    return {
        'site_name': 'IT Management Platform',
        'user_role': request.user.role if request.user.is_authenticated else None,
        'current_path': request.path,
        'debug': settings.DEBUG,
    }


def dashboard_stats_context(request):
    """
    Add dashboard statistics to context.
    """
    if not request.user.is_authenticated:
        return {}
    
    return {
        'dashboard_stats': {
            'active_users': User.objects.filter(is_active=True).count() if User else 0,
            'total_assets': Asset.objects.count() if Asset else 0,
            'active_projects': Project.objects.filter(status='ACTIVE').count() if Project else 0,
            'open_tickets': Ticket.objects.filter(status__in=['NEW', 'OPEN']).count() if Ticket else 0,
        }
    }

