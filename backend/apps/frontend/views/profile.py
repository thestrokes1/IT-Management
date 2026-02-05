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
    
    Server-side filtering:
    - Reads GET parameters (search, username, action, start_date, end_date, hour_from, hour_to)
    - Uses ActivityService.get_activity_logs() to apply filters with RBAC
    - Recent Activity table displays ONLY filtered results
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
            
            # =====================================================================
            # Read and normalize GET parameters for filtering
            # =====================================================================
            raw_search = request.GET.get('search', '')
            raw_username = request.GET.get('username', '')
            raw_action = request.GET.get('action', '')
            raw_start_date = request.GET.get('start_date', '')
            raw_end_date = request.GET.get('end_date', '')
            raw_hour_from = request.GET.get('hour_from', '')
            raw_hour_to = request.GET.get('hour_to', '')
            
            # Normalize: empty strings become None
            search = self._clean(raw_search) or None
            username = self._clean(raw_username) or None
            action = self._clean(raw_action) or None
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
            
            # =====================================================================
            # DEBUG: Log normalized filters
            # =====================================================================
            print(f"\n[LOGS_VIEW] Normalized filters:")
            print(f"  search: {repr(search)}")
            print(f"  username: {repr(username)}")
            print(f"  action: {repr(action)}")
            print(f"  start_date: {repr(start_date)}")
            print(f"  end_date: {repr(end_date)}")
            print(f"  hour_from: {repr(hour_from)}")
            print(f"  hour_to: {repr(hour_to)}")
            
            # =====================================================================
            # Call ActivityService with filters (includes RBAC)
            # =====================================================================
            recent_logs = service.get_activity_logs(
                user=request.user,
                search=search,
                username=username,
                action=action,
                start_date=start_date,
                end_date=end_date,
                hour_from=hour_from,
                hour_to=hour_to,
                limit=100
            )
            
            print(f"[LOGS_VIEW] Final logs count: {recent_logs.count()}")
            
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

