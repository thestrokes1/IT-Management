"""
Project views for IT Management Platform.
Contains all project-related views (list, create, edit, delete).
Uses CQRS pattern: Queries return DTOs, Services raise domain exceptions.
Uses permission_mapper for consistent UI permission flags.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from apps.frontend.mixins import CanManageProjectsMixin
from apps.frontend.services import ProjectService
from apps.projects.queries import ProjectQuery
from apps.core.exceptions import DomainException, PermissionDeniedError
from apps.core.exception_mapper import ExceptionMapper, SafeTemplateView
from apps.projects.policies import ProjectPolicy
from apps.projects.domain.services.project_authority import (
    get_project_permissions, 
    can_create_project,
)
from apps.frontend.permissions_mapper import (
    build_project_ui_permissions,
    build_projects_permissions_map,
    get_list_permissions,
)


class ProjectsView(LoginRequiredMixin, SafeTemplateView):
    """
    Projects management web interface.
    Uses ProjectQuery for read operations (returns DTOs).
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
    template_name = 'frontend/projects.html'
    login_url = 'frontend:login'
    redirect_url = 'frontend:projects'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use Query for reads - returns DTOs
        projects_dto = ProjectQuery.get_list_dto()
        status_choices = ProjectQuery.get_status_choices()
        priority_choices = ProjectQuery.get_priority_choices()
        
        # Convert DTOs to list for processing
        projects_list = projects_dto.projects
        
        # Build permissions map using permission_mapper
        permissions_map = build_projects_permissions_map(self.request.user, projects_list)
        
        # Get list-level permissions
        list_permissions = get_list_permissions(self.request.user)
        list_permissions['can_create'] = can_create_project(self.request.user)
        
        context.update({
            'projects': projects_list,
            'projects_dict': projects_dto.to_list(),
            'total_count': projects_dto.total_count,
            'status_choices': status_choices,
            'priority_choices': priority_choices,
            'permissions_map': permissions_map,
            'permissions': list_permissions,
        })
        return context


class CreateProjectView(LoginRequiredMixin, CanManageProjectsMixin, SafeTemplateView):
    """
    Create new project web interface.
    Uses ProjectQuery for reads (DTOs), ProjectService for writes.
    Uses permission_mapper for UI permission flags.
    """
    template_name = 'frontend/create-project.html'
    login_url = 'frontend:login'
    redirect_url = 'frontend:projects'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use Query for reads - returns DTOs/dicts
        categories = ProjectQuery.get_categories()
        available_users = ProjectQuery.get_active_users()
        
        # Get list permissions for template consistency
        list_permissions = get_list_permissions(self.request.user)
        list_permissions['can_create'] = can_create_project(self.request.user)
        
        context.update({
            'categories': categories,
            'categories_dict': [c.to_dict() for c in categories] if hasattr(categories[0], 'to_dict') else categories,
            'available_users': available_users,
            'form': {},
            'permissions': list_permissions,
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle project creation using Service."""
        try:
            # Use Service for write operation
            project = ProjectService.create_project(
                request=request,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', '').strip(),
                category_id=request.POST.get('category', ''),
                status=request.POST.get('status', 'PLANNING'),
                priority=request.POST.get('priority', 'MEDIUM'),
                start_date=request.POST.get('start_date', ''),
                end_date=request.POST.get('end_date', ''),
                budget=request.POST.get('budget', ''),
                owner_id=request.POST.get('project_manager', ''),
                team_members=request.POST.getlist('team_members', [])
            )
            
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('frontend:projects')
        
        except DomainException:
            raise


class EditProjectView(SafeTemplateView):
    """
    Edit project web interface.
    Uses ProjectQuery for reads (DTOs), ProjectService for writes.
    Uses permission_mapper for UI permission flags.
    """
    template_name = 'frontend/edit-project.html'
    login_url = 'frontend:login'
    redirect_url = 'frontend:projects'
    
    def dispatch(self, request, *args, **kwargs):
        """Check edit permission at dispatch time."""
        project_id = kwargs.get('project_id')
        
        # Get project for permission check
        project = ProjectQuery.get_by_id(project_id)
        
        if project is None:
            from apps.core.exceptions import NotFoundError
            raise NotFoundError(
                resource_type="Project",
                resource_id=project_id
            )
        
        # Store project in view for later use
        self._project = project
        
        # Check edit permission using Policy
        policy = ProjectPolicy()
        project_dict = project.to_dict() if hasattr(project, 'to_dict') else project
        auth_result = policy.can_edit(request.user, project_dict)
        
        if not auth_result.allowed:
            raise PermissionDeniedError(
                message=auth_result.reason,
                details={'action': 'edit', 'resource_type': 'project'}
            )
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs.get('project_id')
        
        # Use Query for reads - returns DTO
        project_dto = ProjectQuery.get_with_details(project_id)
        
        if project_dto is None:
            from apps.core.exceptions import NotFoundError
            raise NotFoundError(
                resource_type="Project",
                resource_id=project_id
            )
        
        categories = ProjectQuery.get_categories()
        available_users = ProjectQuery.get_active_users()
        
        # Convert to dict for permissions
        project_dict = project_dto.to_dict() if hasattr(project_dto, 'to_dict') else project_dto
        
        # Build UI permission flags using permission_mapper
        permissions = build_project_ui_permissions(self.request.user, project_dict)
        
        context.update({
            'project': project_dto,
            'project_dict': project_dict,
            'categories': categories,
            'categories_dict': [c.to_dict() for c in categories] if hasattr(categories[0], 'to_dict') else categories,
            'available_users': available_users,
            'form': {},
            'permissions': permissions,
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle project edit using Service."""
        try:
            project_id = self.kwargs.get('project_id')
            
            # Use Service for write operation
            project = ProjectService.update_project(
                request=request,
                project_id=project_id,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', '').strip(),
                category_id=request.POST.get('category', ''),
                status=request.POST.get('status', 'PLANNING'),
                priority=request.POST.get('priority', 'MEDIUM'),
                start_date=request.POST.get('start_date', ''),
                end_date=request.POST.get('end_date', ''),
                budget=request.POST.get('budget', ''),
                owner_id=request.POST.get('project_manager', ''),
                team_members=request.POST.getlist('team_members', [])
            )
            
            messages.success(request, f'Project "{project.name}" updated successfully!')
            return redirect('frontend:projects')
        
        except DomainException:
            raise


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "POST"])
def delete_project(request, project_id):
    """
    Delete a project.
    Uses ProjectService for write operation.
    Uses ProjectPolicy for authorization.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Authentication required. Please log in.'}, status=401)
        return redirect('frontend:login')
    
    try:
        # Get project for authorization check
        project_dto = ProjectQuery.get_by_id(project_id)
        
        if project_dto is None:
            return JsonResponse({'error': f'Project with id {project_id} not found.'}, status=404)
        
        # Convert to dict for permission check
        project_dict = project_dto.to_dict() if hasattr(project_dto, 'to_dict') else project_dto
        
        # Check permission using Policy
        policy = ProjectPolicy()
        policy.can_delete(request.user, project_dict).require('delete', 'project')
        
        # Use Service for write operation
        ProjectService.delete_project(project_id, user=request.user)
        
        return JsonResponse({'success': True, 'message': f'Project deleted successfully.'})
    
    except DomainException as e:
        return ExceptionMapper.to_json_response(e, request)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error deleting project: {str(e)}'}, status=500)


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "PATCH"])
def project_crud(request, project_id):
    """
    Handle project CRUD operations (DELETE and PATCH).
    Uses ProjectService for write operations.
    Uses ProjectPolicy for authorization.
    """
    try:
        if request.method == 'DELETE':
            # Check permission using Policy
            project_dto = ProjectQuery.get_by_id(project_id)
            if project_dto is None:
                return JsonResponse({'error': f'Project with id {project_id} not found.'}, status=404)
            
            project_dict = project_dto.to_dict() if hasattr(project_dto, 'to_dict') else project_dto
            
            policy = ProjectPolicy()
            policy.can_delete(request.user, project_dict).require('delete', 'project')
            
            # Use Service for delete operation
            ProjectService.delete_project(project_id, user=request.user)
            
            return JsonResponse({'success': True, 'message': 'Project deleted successfully.'})
        
        elif request.method == 'PATCH':
            import json
            data = json.loads(request.body)
            
            # Get project for authorization check
            project_dto = ProjectQuery.get_by_id(project_id)
            if project_dto is None:
                return JsonResponse({'error': f'Project with id {project_id} not found.'}, status=404)
            
            project_dict = project_dto.to_dict() if hasattr(project_dto, 'to_dict') else project_dto
            
            # Check permission using Policy
            policy = ProjectPolicy()
            policy.can_edit(request.user, project_dict).require('edit', 'project')
            
            # Use Service for partial update
            project = ProjectService.update_project(
                request=request,
                project_id=project_id,
                **{k: v for k, v in data.items() if k in ['name', 'description', 'status', 'priority', 'start_date', 'end_date', 'budget', 'owner_id']}
            )
            
            return JsonResponse({'success': True, 'message': f'Project "{project.name}" updated successfully.'})
    
    except DomainException as e:
        return ExceptionMapper.to_json_response(e, request)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


# Wrapper functions for URL patterns
def projects(request):
    """Projects list view."""
    view = ProjectsView.as_view()
    return view(request)


def project_detail(request, project_id):
    """Project detail view."""
    view = EditProjectView.as_view()
    return view(request, project_id=project_id)


def create_project(request):
    """Create project view."""
    view = CreateProjectView.as_view()
    return view(request)


def edit_project(request, project_id):
    """Edit project view."""
    view = EditProjectView.as_view()
    return view(request, project_id=project_id)

