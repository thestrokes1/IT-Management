"""
User management views for IT Management Platform.
Contains all user-related views (list, create, edit, delete).
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

try:
    from apps.users.models import User
except ImportError:
    User = None


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
            
            # Validation
            errors = {}
            if not email:
                errors['email'] = 'Email is required'
            elif User.objects.filter(email=email).exclude(id=user_id).exists():
                errors['email'] = 'Email already exists'
            
            if password:
                if len(password) < 8:
                    errors['password'] = 'Password must be at least 8 characters'
                
                if password != password_confirm:
                    errors['password_confirm'] = 'Passwords do not match'
            
            if errors:
                context = self.get_context_data()
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
                user.role = role
                user.is_active = is_active
            
            if password:
                user.set_password(password)
            
            user.save()
            
            messages.success(request, f'User "{user.username}" updated successfully.')
            return redirect('frontend:users')
            
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('frontend:users')
        except Exception as e:
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
    """Delete a user account with proper handling of related records."""
    # Import User model at module level to avoid UnboundLocalError in exception handlers
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Check if user is authenticated - return 401 for AJAX requests
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Authentication required. Please log in.'}, status=401)
        return redirect('frontend:login')
    
    # Check permissions - allow ADMIN or SUPERADMIN (also check for IT_ADMIN role)
    if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN', 'IT_ADMIN']:
        return JsonResponse({'error': 'You do not have permission to delete users. Only ADMIN or SUPERADMIN roles can delete users.'}, status=403)
    
    try:
        from django.db import connection
        from apps.tickets.models import Ticket, TicketComment, TicketAttachment, TicketHistory, TicketEscalation, TicketSatisfaction, TicketTemplate, TicketReport
        from apps.projects.models import Project, Task, ProjectMember, ProjectTemplate, ProjectReport
        from apps.assets.models import Asset, AssetAssignment, AssetMaintenance
        from apps.logs.models import SystemLog

        user = User.objects.get(id=user_id)
        
        if user.id == request.user.id:
            return JsonResponse({'error': 'You cannot delete your own account.'}, status=400)
        
        username = user.username
        
        # Use raw SQL to avoid Django signals during deletion
        # This prevents the atomic block error by executing deletions outside Django's signal handlers
        
        # Step 1: Disable user-related signals temporarily
        # We'll use raw SQL to update foreign key references first
        
        user_uuid = str(user.user_id)
        
        # Build a list of all tables that reference users and need to be updated
        # This is done BEFORE starting any transaction to avoid atomic block issues
        
        # Update all User foreign key references to NULL
        tables_to_update = [
            # Tickets table references
            ('ticket_categories', 'default_assignee'),
            ('tickets', 'requester'),
            ('tickets', 'assigned_to'),
            ('tickets', 'created_by'),
            ('tickets', 'updated_by'),
            # Ticket comments/attachments/history references
            ('ticket_comments', 'user'),
            ('ticket_attachments', 'user'),
            ('ticket_history', 'user'),
            ('ticket_templates', 'created_by'),
            ('ticket_escalations', 'escalated_by'),
            ('ticket_escalations', 'escalated_to'),
            ('ticket_satisfaction', 'rated_by'),
            ('ticket_reports', 'generated_by'),
            # Project tables
            ('projects', 'created_by'),
            ('projects', 'updated_by'),
            ('projects', 'owner'),
            ('project_memberships', 'user'),
            ('project_templates', 'created_by'),
            ('project_reports', 'generated_by'),
            # Asset tables
            ('assets', 'assigned_to'),
            ('assets', 'created_by'),
            ('assets', 'updated_by'),
            ('asset_assignments', 'user'),
            ('asset_assignments', 'assigned_by'),
            ('maintenance_records', 'created_by'),
            ('asset_audit_logs', 'user'),
            ('asset_reports_generated', 'generated_by'),
            # User profile references
            ('user_profiles', 'manager'),
            # Log tables
            ('system_logs', 'user'),
            # Login attempts - can't set to NULL, but that's OK (no FK constraint)
        ]
        
        # Use a cursor to execute raw SQL updates
        with connection.cursor() as cursor:
            # First, delete tickets where user is the requester (NOT NULL constraint)
            # These tickets must be fully deleted including all child records
            
            # Get ticket IDs where user is requester
            cursor.execute("SELECT id FROM tickets WHERE requester_id = %s", [user.id])
            ticket_ids = [row[0] for row in cursor.fetchall()]
            
            if ticket_ids:
                # Create a comma-separated list of IDs for SQLite compatibility
                ticket_ids_str = ','.join(str(tid) for tid in ticket_ids)
                
                # Delete all child records for these tickets first
                # Delete TicketReports
                cursor.execute(f"DELETE FROM ticket_reports WHERE id IN ({ticket_ids_str})")
                # Delete TicketEscalations
                cursor.execute(f"DELETE FROM ticket_escalations WHERE id IN ({ticket_ids_str})")
                # Delete TicketSatisfaction
                cursor.execute(f"DELETE FROM ticket_satisfaction WHERE id IN ({ticket_ids_str})")
                # Delete TicketHistory
                cursor.execute(f"DELETE FROM ticket_history WHERE id IN ({ticket_ids_str})")
                # Delete TicketAttachments
                cursor.execute(f"DELETE FROM ticket_attachments WHERE id IN ({ticket_ids_str})")
                # Delete TicketComments
                cursor.execute(f"DELETE FROM ticket_comments WHERE id IN ({ticket_ids_str})")
                # Delete the tickets themselves
                cursor.execute(f"DELETE FROM tickets WHERE id IN ({ticket_ids_str})")
            
            # Delete TicketEscalations where user is escalated_by or escalated_to
            cursor.execute(
                "DELETE FROM ticket_escalations WHERE escalated_by_id = %s OR escalated_to_id = %s",
                [user.id, user.id]
            )
            
            # Delete TicketSatisfaction where user is rated_by
            cursor.execute(
                "DELETE FROM ticket_satisfaction WHERE rated_by_id = %s",
                [user.id]
            )
            
            # Now update all nullable foreign key references to NULL
            for table, column in tables_to_update:
                try:
                    # Skip 'tickets' table and 'requester' column since it has NOT NULL constraint
                    if table == 'tickets' and column == 'requester':
                        continue
                    # Check if column exists and update
                    cursor.execute(
                        f"UPDATE {table} SET {column} = NULL WHERE {column}_id = %s",
                        [user.id]
                    )
                except Exception:
                    # Table or column might not exist, skip
                    pass
        
        # Now delete the user normally - this should work since we've cleared references
        user.delete()
        
        # Return consistent JSON response for both DELETE and POST
        return JsonResponse({'success': True, 'message': f'User {username} deleted successfully.'})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error deleting user: {str(e)}'}, status=500)

