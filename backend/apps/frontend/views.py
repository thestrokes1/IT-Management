"""
Frontend views for IT Management Platform.
Web interface and dashboard views.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import json

try:
    from apps.users.models import User
    from apps.assets.models import Asset, AssetAssignment
    from apps.projects.models import Project, Task
    from apps.tickets.models import Ticket, TicketComment
    from apps.logs.models import ActivityLog, SecurityEvent, SystemLog
except ImportError:
    # Fallback for testing
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

class LoginView(TemplateView):
    """
    User login view.
    """
    template_name = 'frontend/login.html'
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('frontend:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
        
        return render(request, self.template_name)

class LogoutView(TemplateView):
    """
    User logout view.
    """
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('frontend:login')

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

class AssetsView(LoginRequiredMixin, TemplateView):
    """
    Assets management web interface.
    """
    template_name = 'frontend/assets.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            assets = Asset.objects.select_related('category', 'assigned_to').order_by('-created_at')[:50]
            categories = Asset.objects.select_related('category').values('category__name').distinct()
        except:
            assets = []
            categories = []
        context.update({
            'assets': assets,
            'categories': categories
        })
        return context

class ProjectsView(LoginRequiredMixin, TemplateView):
    """
    Projects management web interface.
    """
    template_name = 'frontend/projects.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            projects = Project.objects.select_related('category', 'project_manager', 'created_by', 'updated_by').order_by('-created_at')[:50]
            status_choices = Project.STATUS_CHOICES
        except:
            projects = []
            status_choices = []
        context.update({
            'projects': projects,
            'status_choices': status_choices
        })
        return context

class TicketsView(LoginRequiredMixin, TemplateView):
    """
    Tickets management web interface.
    """
    template_name = 'frontend/tickets.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            tickets = Ticket.objects.select_related('created_by', 'assigned_to', 'category', 'ticket_type').order_by('-created_at')[:50]
            status_choices = Ticket.STATUS_CHOICES
            priority_choices = Ticket.PRIORITY_CHOICES
        except:
            tickets = []
            status_choices = []
            priority_choices = []
        context.update({
            'tickets': tickets,
            'status_choices': status_choices,
            'priority_choices': priority_choices
        })
        return context

class UsersView(LoginRequiredMixin, TemplateView):
    """
    Users management web interface.
    """
    template_name = 'frontend/users.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            users = User.objects.filter(is_active=True).order_by('-date_joined')[:50]
            role_choices = User.ROLE_CHOICES
        except:
            users = []
            role_choices = []
        context.update({
            'users': users,
            'role_choices': role_choices
        })
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

class CreateTicketView(LoginRequiredMixin, TemplateView):
    """
    Create new support ticket web interface.
    """
    template_name = 'frontend/create-ticket.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.tickets.models import TicketCategory, TicketType
            categories = TicketCategory.objects.filter(is_active=True)
            ticket_types = TicketType.objects.filter(is_active=True)
            available_users = User.objects.filter(is_active=True)
        except:
            categories = []
            ticket_types = []
            available_users = []
        context.update({
            'categories': categories,
            'ticket_types': ticket_types,
            'available_users': available_users,
            'form': {}
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle ticket creation."""
        try:
            from apps.tickets.models import Ticket, TicketCategory, TicketType
            from django.utils import timezone
            from datetime import datetime
            
            title = request.POST.get('title', '')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category', '')
            ticket_type_id = request.POST.get('ticket_type', '')
            priority = request.POST.get('priority', 'MEDIUM')
            impact = request.POST.get('impact', 'MEDIUM')
            urgency = request.POST.get('urgency', 'MEDIUM')
            assigned_to_id = request.POST.get('assigned_to', '')
            due_date = request.POST.get('due_date', '')
            
            # Validation
            errors = {}
            if not title:
                errors['title'] = 'Title is required'
            if not description:
                errors['description'] = 'Description is required'
            if not category_id:
                errors['category'] = 'Category is required'
            if not priority:
                errors['priority'] = 'Priority is required'
            
            if errors:
                context = self.get_context_data()
                context['errors'] = errors
                context['form'] = request.POST
                return render(request, self.template_name, context)
            
            # Create ticket
            category = TicketCategory.objects.get(id=category_id)
            ticket_type = TicketType.objects.get(id=ticket_type_id) if ticket_type_id else None
            assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
            
            # Parse due_date and convert to sla_due_at
            sla_due_at = None
            if due_date:
                try:
                    due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                    sla_due_at = timezone.make_aware(
                        timezone.datetime.combine(due_date_obj, timezone.datetime.min.time())
                    )
                except ValueError:
                    pass  # Invalid date format, leave as None
            
            ticket = Ticket.objects.create(
                title=title,
                description=description,
                category=category,
                ticket_type=ticket_type,
                priority=priority,
                impact=impact,
                urgency=urgency,
                assigned_to=assigned_to,
                sla_due_at=sla_due_at,
                requester=request.user,
                created_by=request.user,
                status='NEW'
            )
            
            messages.success(request, f'Ticket #{ticket.id} created successfully!')
            return redirect('frontend:tickets')
        
        except Exception as e:
            messages.error(request, f'Error creating ticket: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


class CreateProjectView(LoginRequiredMixin, TemplateView):
    """
    Create new project web interface.
    """
    template_name = 'frontend/create-project.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.projects.models import ProjectCategory
            categories = ProjectCategory.objects.filter(is_active=True)
            available_users = User.objects.filter(is_active=True)
        except:
            categories = []
            available_users = []
        context.update({
            'categories': categories,
            'available_users': available_users,
            'form': {}
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle project creation."""
        try:
            from apps.projects.models import Project, ProjectCategory
            
            name = request.POST.get('name', '')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category', '')
            priority = request.POST.get('priority', 'MEDIUM')
            project_manager_id = request.POST.get('project_manager', '')
            objectives = request.POST.get('objectives', '')
            requirements = request.POST.get('requirements', '')
            deliverables = request.POST.get('deliverables', '')
            start_date = request.POST.get('start_date', '')
            end_date = request.POST.get('end_date', '')
            deadline = request.POST.get('deadline', '')
            budget = request.POST.get('budget', '')
            risk_level = request.POST.get('risk_level', 'MEDIUM')
            risk_description = request.POST.get('risk_description', '')
            
            # Validation
            errors = {}
            if not name:
                errors['name'] = 'Project name is required'
            if not description:
                errors['description'] = 'Description is required'
            if not category_id:
                errors['category'] = 'Category is required'
            if not project_manager_id:
                errors['project_manager'] = 'Project manager is required'
            
            if errors:
                context = self.get_context_data()
                context['errors'] = errors
                context['form'] = request.POST
                return render(request, self.template_name, context)
            
            # Create project
            category = ProjectCategory.objects.get(id=category_id)
            project_manager = User.objects.get(id=project_manager_id)
            
            project = Project.objects.create(
                name=name,
                description=description,
                category=category,
                priority=priority,
                project_manager=project_manager,
                objectives=objectives,
                requirements=requirements,
                deliverables=deliverables,
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None,
                deadline=deadline if deadline else None,
                budget=budget if budget else None,
                risk_level=risk_level,
                risk_description=risk_description,
                created_by=request.user,
                status='PLANNING'
            )
            
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('frontend:projects')
        
        except Exception as e:
            messages.error(request, f'Error creating project: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


class CreateAssetView(LoginRequiredMixin, TemplateView):
    """
    Create new asset web interface.
    """
    template_name = 'frontend/create-asset.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.assets.models import AssetCategory
            categories = AssetCategory.objects.filter(is_active=True)
            available_users = User.objects.filter(is_active=True)
        except:
            categories = []
            available_users = []
        context.update({
            'categories': categories,
            'available_users': available_users,
            'form': {}
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle asset creation."""
        try:
            from apps.assets.models import Asset, AssetCategory
            
            name = request.POST.get('name', '')
            asset_type = request.POST.get('asset_type', '')
            category_id = request.POST.get('category', '')
            description = request.POST.get('description', '')
            serial_number = request.POST.get('serial_number', '')
            model = request.POST.get('model', '')
            manufacturer = request.POST.get('manufacturer', '')
            version = request.POST.get('version', '')
            status = request.POST.get('status', 'ACTIVE')
            assigned_to_id = request.POST.get('assigned_to', '')
            location = request.POST.get('location', '')
            purchase_date = request.POST.get('purchase_date', '')
            purchase_cost = request.POST.get('purchase_cost', '')
            warranty_expiry = request.POST.get('warranty_expiry', '')
            end_of_life = request.POST.get('end_of_life', '')
            
            # Validation
            errors = {}
            if not name:
                errors['name'] = 'Asset name is required'
            if not asset_type:
                errors['asset_type'] = 'Asset type is required'
            if not category_id:
                errors['category'] = 'Category is required'
            if not status:
                errors['status'] = 'Status is required'
            
            if errors:
                context = self.get_context_data()
                context['errors'] = errors
                context['form'] = request.POST
                return render(request, self.template_name, context)
            
            # Create asset
            category = AssetCategory.objects.get(id=category_id)
            assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
            
            asset = Asset.objects.create(
                name=name,
                asset_type=asset_type,
                category=category,
                description=description,
                serial_number=serial_number if serial_number else None,
                model=model,
                manufacturer=manufacturer,
                version=version,
                status=status,
                assigned_to=assigned_to,
                location=location,
                purchase_date=purchase_date if purchase_date else None,
                purchase_cost=purchase_cost if purchase_cost else None,
                warranty_expiry=warranty_expiry if warranty_expiry else None,
                end_of_life=end_of_life if end_of_life else None,
                created_by=request.user
            )
            
            messages.success(request, f'Asset "{asset.name}" created successfully!')
            return redirect('frontend:assets')
        
        except Exception as e:
            messages.error(request, f'Error creating asset: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


class Error404View(TemplateView):
    """
    Custom 404 error page.
    """
    template_name = 'frontend/errors/404.html'

class Error500View(TemplateView):
    """
    Custom 500 error page.
    """
    template_name = 'frontend/errors/500.html'

class MaintenanceView(TemplateView):
    """
    Maintenance page view.
    """
    template_name = 'frontend/maintenance.html'


class CreateUserView(LoginRequiredMixin, TemplateView):
    """
    Create new user account web interface.
    """
    template_name = 'frontend/create-user.html'
    login_url = 'frontend:login'
    
    def get(self, request, *args, **kwargs):
        """Check if user is admin."""
        if not request.user.can_manage_users:
            return redirect('frontend:dashboard')
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'form': {}
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle user creation."""
        # Check permissions
        if not request.user.can_manage_users:
            messages.error(request, 'You do not have permission to create users.')
            return redirect('frontend:users')
        
        try:
            from django.contrib.auth import get_user_model
            import uuid
            User = get_user_model()
            
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            role = request.POST.get('role', 'VIEWER')
            is_active = request.POST.get('is_active') == 'on'
            
            # Note: employee_id is now auto-generated by the User model's save() method
            
            # Validation
            errors = {}
            if not username:
                errors['username'] = 'Username is required'
            elif User.objects.filter(username=username).exists():
                errors['username'] = 'Username already exists'
            
            if not email:
                errors['email'] = 'Email is required'
            elif User.objects.filter(email=email).exists():
                errors['email'] = 'Email already exists'
            
            if not password:
                errors['password'] = 'Password is required'
            elif len(password) < 8:
                errors['password'] = 'Password must be at least 8 characters'
            
            if password != password_confirm:
                errors['password_confirm'] = 'Passwords do not match'
            
            if not role:
                errors['role'] = 'Role is required'
            
            if errors:
                context = self.get_context_data()
                context['errors'] = errors
                context['form'] = request.POST
                return render(request, self.template_name, context)
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_active=is_active
            )
            
            messages.success(request, f'User {username} created successfully.')
            return redirect('frontend:users')
            
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


class EditUserView(LoginRequiredMixin, TemplateView):
    """
    Edit user account web interface.
    """
    template_name = 'frontend/edit-user.html'
    login_url = 'frontend:login'
    
    def dispatch(self, request, user_id, *args, **kwargs):
        """Check if user can manage users or is editing their own profile."""
        # Allow if user can manage users OR if editing own profile
        if not (request.user.can_manage_users or request.user.id == int(user_id)):
            return redirect('frontend:dashboard')
        self.user_id = user_id
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=self.user_id)
            context.update({
                'user': user,
                'form': {},
                'role_choices': User.ROLE_CHOICES
            })
        except:
            pass
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle user edit."""
        user_id = self.user_id
        
        # Check permissions
        if not request.user.can_manage_users and request.user.id != int(user_id):
            messages.error(request, 'You do not have permission to edit this user.')
            return redirect('frontend:users')
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            role = request.POST.get('role', user.role)
            is_active = request.POST.get('is_active') == 'on'
            
            print(f"DEBUG: Editing user {user_id}, new role: {role}, current role: {user.role}")
            print(f"DEBUG: can_manage_users: {request.user.can_manage_users}")
            
            # Validation
            errors = {}
            if not email:
                errors['email'] = 'Email is required'
            elif User.objects.filter(email=email).exclude(id=user_id).exists():
                errors['email'] = 'Email already exists'
            
            if password:  # Only validate if changing password
                if len(password) < 8:
                    errors['password'] = 'Password must be at least 8 characters'
                
                if password != password_confirm:
                    errors['password_confirm'] = 'Passwords do not match'
            
            if errors:
                context = self.get_context_data()
                from django.contrib.auth import get_user_model
                User = get_user_model()
                context['user'] = User.objects.get(id=user_id)
                context['errors'] = errors
                context['form'] = request.POST
                return render(request, self.template_name, context)
            
            # Update user
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            
            # Only users with can_manage_users permission can change role and status
            if request.user.can_manage_users:
                print(f"DEBUG: Updating role from {user.role} to {role}")
                user.role = role
                user.is_active = is_active
            
            if password:
                user.set_password(password)
            
            user.save()
            print(f"DEBUG: User saved successfully. Role now: {user.role}")
            
            messages.success(request, f'User "{user.username}" updated successfully.')
            return redirect('frontend:users')
            
        except User.DoesNotExist:
            print(f"DEBUG: User {user_id} not found")
            messages.error(request, 'User not found.')
            return redirect('frontend:users')
        except Exception as e:
            print(f"DEBUG: Exception occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error updating user: {str(e)}')
            context = self.get_context_data()
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                context['user'] = User.objects.get(id=user_id)
            except:
                pass
            context['form'] = request.POST
            return render(request, self.template_name, context)


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "POST"])
def delete_user(request, user_id):
    """Delete a user account."""
    # Check if user is authenticated - return 401 for AJAX requests
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Authentication required. Please log in.'}, status=401)
        return redirect('frontend:login')
    
    # Check permissions - allow ADMIN or SUPERADMIN
    if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN']:
        return JsonResponse({'error': 'You do not have permission to delete users. Only ADMIN or SUPERADMIN roles can delete users.'}, status=403)
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        if user.id == request.user.id:
            return JsonResponse({'error': 'You cannot delete your own account.'}, status=400)
        
        username = user.username
        user.delete()
        
        # Return 204 No Content for DELETE requests, or JSON for POST
        if request.method == 'DELETE':
            return HttpResponse(status=204)
        else:
            return JsonResponse({'success': True, 'message': f'User {username} deleted successfully.'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error deleting user: {str(e)}'}, status=500)


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "PATCH"])
def project_crud(request, project_id):
    """Handle project CRUD operations (DELETE and PATCH)."""
    # Check permissions - use the can_manage_projects property from User model
    if not hasattr(request.user, 'can_manage_projects') or not request.user.can_manage_projects:
        return JsonResponse({'error': 'You do not have permission to manage projects.'}, status=403)
    
    try:
        project = Project.objects.get(id=project_id)
        
        if request.method == 'DELETE':
            # Delete project
            project_name = project.name
            project.delete()
            return JsonResponse({'success': True, 'message': f'Project "{project_name}" deleted successfully.'}, status=200)
        
        elif request.method == 'PATCH':
            # Update project
            data = json.loads(request.body)
            
            if 'name' in data and data['name'].strip():
                project.name = data['name']
            if 'description' in data:
                project.description = data['description']
            
            project.save()
            
            return JsonResponse({'success': True, 'message': f'Project "{project.name}" updated successfully.'})
    
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "PATCH"])
def ticket_crud(request, ticket_id):
    """Handle ticket CRUD operations (DELETE and PATCH)."""
    # Check permissions
    if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN']:
        return JsonResponse({'error': 'You do not have permission to manage tickets.'}, status=403)
    
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        
        if request.method == 'DELETE':
            # Delete ticket
            ticket_title = ticket.title
            ticket.delete()
            return JsonResponse({'success': True, 'message': f'Ticket "{ticket_title}" deleted successfully.'})
        
        elif request.method == 'PATCH':
            # Update ticket
            data = json.loads(request.body)
            
            if 'title' in data and data['title'].strip():
                ticket.title = data['title']
            if 'description' in data:
                ticket.description = data['description']
            
            ticket.save()
            
            return JsonResponse({'success': True, 'message': f'Ticket "{ticket.title}" updated successfully.'})
    
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "PATCH"])
def asset_crud(request, asset_id):
    """Handle asset CRUD operations (DELETE and PATCH)."""
    # Check permissions
    if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN']:
        return JsonResponse({'error': 'You do not have permission to manage assets.'}, status=403)
    
    try:
        asset = Asset.objects.get(id=asset_id)
        
        if request.method == 'DELETE':
            # Delete asset
            asset_name = asset.name
            asset.delete()
            return JsonResponse({'success': True, 'message': f'Asset "{asset_name}" deleted successfully.'})
        
        elif request.method == 'PATCH':
            # Update asset
            data = json.loads(request.body)
            
            if 'name' in data and data['name'].strip():
                asset.name = data['name']
            if 'tag' in data:
                asset.tag = data['tag']
            
            asset.save()
            
            return JsonResponse({'success': True, 'message': f'Asset "{asset.name}" updated successfully.'})
    
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


# Context processors for frontend

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

