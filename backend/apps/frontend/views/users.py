"""
User management views for IT Management Platform.
Contains all user-related views (list, create, edit, delete, role change).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from apps.frontend.mixins import CanManageUsersMixin
from apps.users.models import User


# =========================
# USERS LIST
# =========================

class UsersView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/users.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.filter(is_active=True).order_by('-date_joined')
        context['role_choices'] = User.ROLE_CHOICES
        return context


# =========================
# CREATE USER
# =========================

class CreateUserView(CanManageUsersMixin, TemplateView):
    template_name = 'frontend/create-user.html'
    login_url = 'frontend:login'

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
        context.update({
            'edit_user': self.edit_user,
            'role_choices': User.ROLE_CHOICES,
            'can_change_role': self.can_change_role,
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
    if request.user.role not in ['SUPERADMIN', 'IT_ADMIN']:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    try:
        user = get_object_or_404(User, id=user_id)

        if user == request.user:
            return JsonResponse({'error': 'You cannot delete yourself.'}, status=400)

        username = user.username
        user.delete()

        return JsonResponse({'success': True, 'message': f'User {username} deleted.'})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
