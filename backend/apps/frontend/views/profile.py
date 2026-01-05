"""
Profile views for IT Management Platform.
Contains user profile, logs, and reports views.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta

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
    """
    template_name = 'frontend/profile.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class LogsView(LoginRequiredMixin, TemplateView):
    """
    Logs management web interface.
    """
    template_name = 'frontend/logs.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            recent_logs = ActivityLog.objects.select_related('user', 'category').order_by('-timestamp')[:100]
            security_events = SecurityEvent.objects.select_related('affected_user').order_by('-detected_at')[:50]
            all_users = User.objects.all().order_by('username')
        except:
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
    Reports and analytics web interface.
    """
    template_name = 'frontend/reports.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Generate basic statistics
        try:
            total_assets = Asset.objects.count() if Asset else 0
            active_projects = Project.objects.filter(status__in=['PLANNING', 'ACTIVE']).count() if Project else 0
            open_tickets = Ticket.objects.filter(status__in=['NEW', 'OPEN', 'IN_PROGRESS']).count() if Ticket else 0
            active_users = User.objects.filter(is_active=True).count() if User else 0
            recent_security_events = SecurityEvent.objects.filter(detected_at__gte=timezone.now() - timedelta(days=7)).count() if SecurityEvent else 0
            
            # Get recent tickets for reports
            recent_tickets = Ticket.objects.select_related('created_by', 'category').order_by('-created_at')[:20] if Ticket else []
            
            # Get ticket statistics
            tickets_by_priority = {}
            tickets_by_status = {}
            if Ticket:
                for status, _ in Ticket.STATUS_CHOICES:
                    tickets_by_status[status] = Ticket.objects.filter(status=status).count()
                for priority, _ in Ticket.PRIORITY_CHOICES:
                    tickets_by_priority[priority] = Ticket.objects.filter(priority=priority).count()
        except:
            total_assets = 0
            active_projects = 0
            open_tickets = 0
            active_users = 0
            recent_security_events = 0
            recent_tickets = []
            tickets_by_priority = {}
            tickets_by_status = {}
        
        context.update({
            'total_assets': total_assets,
            'active_projects': active_projects,
            'open_tickets': open_tickets,
            'active_users': active_users,
            'recent_security_events': recent_security_events,
            'recent_tickets': recent_tickets,
            'tickets_by_priority': tickets_by_priority,
            'tickets_by_status': tickets_by_status,
        })
        
        return context

