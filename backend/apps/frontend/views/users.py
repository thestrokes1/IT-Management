"""
User management views for IT Management Platform.
Contains all user-related views (list, create, edit, delete, role change).
Uses permission_mapper for consistent UI permission flags.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from apps.frontend.mixins import CanManageUsersMixin, FrontendAdminReadMixin
from apps.users.models import User
from apps.users.domain.services.user_authority import (
    get_user_permissions, 
    can_create_user,
    assert_can_delete_user,
)
from apps.core.domain.authorization import AuthorizationError
from apps.frontend.permissions_mapper import (
    build_user_ui_permissions,
    build_users_permissions_map,
    get_list_permissions,
)


# =========================
# USERS LIST
# =========================

class UsersView(LoginRequiredMixin, FrontendAdminReadMixin, TemplateView):
    """
    Users management web interface.
    Only MANAGER+ roles can view the users list.
    Uses permission_mapper for consistent UI permission flags.
    
    UI Permission Flags Contract:
    {
        "can_view": bool,
        "can_update": bool,
        "can_delete": bool,
        "can_assign": bool,
        "can_unassign": bool,
        "can_self_assign": bool,
        "assigned_to_me": bool,
    }
    """
    template_name = 'frontend/users.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.filter(is_active=True).order_by('-date_joined')
        
        # Build permissions map using permission_mapper
        permissions_map = build_users_permissions_map(self.request.user, users)
        
        # Get list permissions
        list_permissions = get_list_permissions(self.request.user)
        list_permissions['can_create'] = can_create_user(self.request.user)
        
        context.update({
            'users': users,
            'role_choices': User.ROLE_CHOICES,
            'permissions_map': permissions_map,
            'permissions': list_permissions,
        })
        return context


# =========================
# CREATE USER
# =========================

class CreateUserView(CanManageUsersMixin, TemplateView):
    template_name = 'frontend/create-user.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get list permissions for template consistency
        list_permissions = get_list_permissions(self.request.user)
        list_permissions['can_create'] = can_create_user(self.request.user)
        
        context.update({
            'permissions': list_permissions,
        })
        return context

    def post(self, request, *args, **kwargs):
        try:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            role = request.POST.get('role', 'VIEWER')

            if password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                return redirect('frontend:create-user')

            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role,
                is_active=True
            )

            messages.success(request, f'User "{username}" created.')
            return redirect('frontend:users')

        except Exception as e:
            messages.error(request, str(e))
            return redirect('frontend:create-user')


# =========================
# EDIT USER (NO ROLE CHANGE)
# =========================

class EditUserView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/edit-user.html'
    login_url = 'frontend:login'

    def dispatch(self, request, user_id, *args, **kwargs):
        self.edit_user = get_object_or_404(User, id=user_id)

        # Allow self-edit OR managers
        if request.user != self.edit_user and not request.user.can_manage_users:
            messages.error(request, 'Permission denied.')
            return redirect('frontend:dashboard')

        self.can_change_role = request.user.role == 'SUPERADMIN'
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Build UI permission flags using permission_mapper
        permissions = build_user_ui_permissions(self.request.user, self.edit_user)
        
        context.update({
            'edit_user': self.edit_user,
            'role_choices': User.ROLE_CHOICES,
            'can_change_role': self.can_change_role,
            'permissions': permissions,
        })
        return context

    def post(self, request, *args, **kwargs):
        user = self.edit_user

        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)

        if request.user.can_manage_users:
            user.is_active = request.POST.get('is_active') == 'on'

        password = request.POST.get('password')
        if password:
            user.set_password(password)

        user.save()
        messages.success(request, 'User updated.')
        return redirect('frontend:users')


# =========================
# CHANGE USER ROLE (SEPARATE ACTION)
# =========================

@login_required(login_url='frontend:login')
@require_http_methods(["POST"])
def change_user_role(request, user_id):
    if request.user.role != 'SUPERADMIN':
        messages.error(request, 'Only SUPERADMIN can change roles.')
        return redirect('frontend:edit-user', user_id=user_id)

    target_user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role')

    valid_roles = [r[0] for r in User.ROLE_CHOICES]
    if new_role not in valid_roles:
        messages.error(request, 'Invalid role.')
        return redirect('frontend:edit-user', user_id=user_id)

    if target_user.role == new_role:
        messages.info(request, 'User already has this role.')
        return redirect('frontend:edit-user', user_id=user_id)

    target_user.role = new_role
    target_user.save(update_fields=['role'])

    messages.success(request, f'Role changed to {new_role}.')
    return redirect('frontend:edit-user', user_id=user_id)


# =========================
# DELETE USER
# =========================

@login_required(login_url='frontend:login')
@require_http_methods(["POST", "DELETE"])
def delete_user(request, user_id):
    """
    Delete a user.
    Uses domain authority for authorization.
    """
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        # Check domain permission
        assert_can_delete_user(request.user, target_user)
        
        username = target_user.username
        target_user.delete()
        
        return JsonResponse({'success': True, 'message': f'User {username} deleted.'})
    
    except AuthorizationError as e:
        return JsonResponse({'error': str(e)}, status=403)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# =========================
# PROFILE WITH MY TICKET HISTORY
# =========================

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/profile.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get tickets created by or assigned to user
        created = user.created_tickets.all()
        assigned = user.assigned_tickets.all()
        my_tickets = (created | assigned).distinct().order_by('-created_at')[:50]
        
        # Compute stats in Python
        created_count = created.count()
        assigned_count = assigned.count()
        resolved_count = created.filter(status='RESOLVED').count()
        can_reopen = user.role in ['TECHNICIAN', 'MANAGER', 'IT_ADMIN', 'SUPERADMIN']
        can_reopen_count = created.filter(status='RESOLVED').count() if can_reopen else 0
        
        # Build permissions for own profile
        profile_permissions = build_user_ui_permissions(user, user)
        
        context.update({
            'my_tickets': my_tickets,
            'can_reopen_ticket': can_reopen,
            'permissions': profile_permissions,
            'stats': {
                'created_count': created_count,
                'assigned_count': assigned_count,
                'resolved_count': resolved_count,
                'can_reopen_count': can_reopen_count,
            }
        })
        return context


# =========================
# REOPEN TICKET FROM PROFILE
# =========================

@login_required(login_url='frontend:login')
@require_http_methods(["POST"])
def profile_reopen_ticket(request, ticket_id):
    """
    Reopen a ticket from the profile page.
    Technicians can only reopen their OWN resolved tickets.
    Managers/Admins can reopen any resolved ticket.
    """
    from apps.tickets.models import Ticket
    from django.utils import timezone
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    user = request.user
    
    # Check if ticket can be reopened
    if ticket.status not in ['RESOLVED', 'CLOSED']:
        messages.error(request, 'Only resolved or closed tickets can be reopened.')
        return redirect('frontend:profile')
    
    # Permission check
    can_reopen = False
    if user.role in ['MANAGER', 'IT_ADMIN', 'SUPERADMIN']:
        can_reopen = True
    elif user.role == 'TECHNICIAN' and (ticket.created_by == user or ticket.assigned_to == user):
        can_reopen = True
    
    if not can_reopen:
        messages.error(request, 'You do not have permission to reopen this ticket.')
        return redirect('frontend:profile')
    
    # Reopen the ticket
    old_status = ticket.status
    ticket.status = 'IN_PROGRESS' if user.role == 'TECHNICIAN' else 'OPEN'
    ticket.last_updated_by = user
    ticket.save()
    
    # Log the reopen action
    from apps.core.services.activity_logger import log_activity
    log_activity(
        actor=user,
        action=f"Reopened ticket from {old_status} to {ticket.status}",
        target_object=ticket,
        description=f"Ticket reopened by {user.username}"
    )
    
    messages.success(request, f'Ticket #{ticket.id} has been reopened.')
    return redirect('frontend:profile')


# Wrapper functions for URL patterns
def users(request):
    """Users list view."""
    view = UsersView.as_view()
    return view(request)


def edit_user(request, user_id):
    """Edit user view."""
    view = EditUserView.as_view()
    return view(request, user_id=user_id)


def create_user(request):
    """Create user view."""
    view = CreateUserView.as_view()
    return view(request)


def change_user_role(request, user_id):
    """Change user role view."""
    from django.views.decorators.http import require_http_methods
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from apps.users.models import User
    
    if request.method == 'POST':
        if request.user.role != 'SUPERADMIN':
            messages.error(request, 'Only SUPERADMIN can change roles.')
            return redirect('frontend:edit-user', user_id=user_id)

        target_user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')

        valid_roles = [r[0] for r in User.ROLE_CHOICES]
        if new_role not in valid_roles:
            messages.error(request, 'Invalid role.')
            return redirect('frontend:edit-user', user_id=user_id)

        if target_user.role == new_role:
            messages.info(request, 'User already has this role.')
            return redirect('frontend:edit-user', user_id=user_id)

        target_user.role = new_role
        target_user.save(update_fields=['role'])

        messages.success(request, f'Role changed to {new_role}.')
        return redirect('frontend:edit-user', user_id=user_id)
    
    return redirect('frontend:edit-user', user_id=user_id)

