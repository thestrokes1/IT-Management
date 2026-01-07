# Project views for IT Management Platform.
# Contains all project-related views (list, create, edit, delete).
# Uses CQRS pattern: Queries return DTOs, Services raise domain exceptions.
# Uses ExceptionMapper for centralized error handling.
# Uses ProjectPolicy for view-level authorization.

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


class ProjectsView(LoginRequiredMixin, SafeTemplateView):
    """
    Projects management web interface.
    Uses ProjectQuery for read operations (returns DTOs).
    Uses ProjectPolicy for view-level authorization.
    SafeTemplateView handles domain exceptions automatically.
    """
    template_name = 'frontend/projects.html'
    login_url = 'frontend:login'
    redirect_url = 'frontend:projects'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check view permission using Policy
        policy = ProjectPolicy()
        auth_result = policy.can_view(self.request.user)
        
        if not auth_result.allowed:
            # Still show projects, but might limit visibility in template
            # Policy will raise exception if critical
            pass
        
        # Use Query for reads - returns DTOs
        projects_dto = ProjectQuery.get_list_dto()
        status_choices = ProjectQuery.get_status_choices()
        priority_choices = ProjectQuery.get_priority_choices()
        
        context.update({
            'projects': projects_dto.projects,  # List of ProjectDTO
            'projects_dict': projects_dto.to_list(),  # List of dicts for templates
            'total_count': projects_dto.total_count,
            'status_choices': status_choices,
            'priority_choices': priority_choices,
            'can_create': policy.can_create(self.request.user).allowed,
            'can_edit_any': self._can_edit_any(),
            'can_delete_any': self._can_delete_any(),
        })
        return context
    
    def _can_edit_any(self) -> bool:
        """Check if user can edit any project (admin-level)."""
        policy = ProjectPolicy()
        auth_result = policy.can_manage(self.request.user)
        return auth_result.allowed
    
    def _can_delete_any(self) -> bool:
        """Check if user can delete any project (admin-level)."""
        policy = ProjectPolicy()
        # Check delete permission with None project (general delete permission)
        auth_result = policy.can_delete(self.request.user, None)
        return auth_result.allowed


class CreateProjectView(LoginRequiredMixin, CanManageProjectsMixin, SafeTemplateView):
    """
    Create new project web interface.
    Uses ProjectQuery for reads (DTOs), ProjectService for writes.
    Uses ProjectPolicy for authorization at view level.
    SafeTemplateView handles domain exceptions automatically.
    """
    template_name = 'frontend/create-project.html'
    login_url = 'frontend:login'
    redirect_url = 'frontend:projects'
    
    def dispatch(self, request, *args, **kwargs):
        """Check create permission at dispatch time."""
        policy = ProjectPolicy()
        auth_result = policy.can_create(request.user)
        
        if not auth_result.allowed:
            # Raise domain exception - will be handled by SafeTemplateView
            raise PermissionDeniedError(
                message=auth_result.reason,
                details={'action': 'create', 'resource_type': 'project'}
            )
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use Query for reads - returns DTOs/dicts
        categories = ProjectQuery.get_categories()
        available_users = ProjectQuery.get_active_users()
        
        context.update({
            'categories': categories,
            'categories_dict': [c.to_dict() for c in categories] if hasattr(categories[0], 'to_dict') else categories,
            'available_users': available_users,
            'form': {}
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle project creation using Service."""
        try:
            # Use Service for write operation
            # May raise DomainException (NotFoundError, ValidationError, PermissionDeniedError)
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
                owner_id=request.POST.get('owner', ''),
                team_members=request.POST.getlist('team_members', [])
            )
            
            # Success - add message and redirect
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('frontend:projects')
        
        except DomainException:
            # Let SafeTemplateView handle this
            raise


class EditProjectView(SafeTemplateView):
    """
    Edit project web interface.
    Uses ProjectQuery for reads (DTOs), ProjectService for writes.
    Uses ProjectPolicy for authorization at view level.
    SafeTemplateView handles domain exceptions automatically.
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
        auth_result = policy.can_edit(request.user, project.to_dict() if hasattr(project, 'to_dict') else project)
        
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
            # Let exception handler deal with this
            from apps.core.exceptions import NotFoundError
            raise NotFoundError(
                resource_type="Project",
                resource_id=project_id
            )
        
        categories = ProjectQuery.get_categories()
        available_users = ProjectQuery.get_active_users()
        
        # Check delete permission for context
        policy = ProjectPolicy()
        can_delete = policy.can_delete(self.request.user, project_dto.to_dict() if hasattr(project_dto, 'to_dict') else project_dto).allowed
        
        context.update({
            'project': project_dto,  # ProjectDetailDTO
            'project_dict': project_dto.to_dict(),  # Dict for templates
            'categories': categories,
            'categories_dict': [c.to_dict() for c in categories] if hasattr(categories[0], 'to_dict') else categories,
            'available_users': available_users,
            'form': {},
            'can_delete': can_delete,
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle project edit using Service."""
        try:
            project_id = self.kwargs.get('project_id')
            
            # Use Service for write operation
            # May raise DomainException (NotFoundError, ValidationError, PermissionDeniedError)
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
                owner_id=request.POST.get('owner', ''),
                team_members=request.POST.getlist('team_members', [])
            )
            
            # Success - add message and redirect
            messages.success(request, f'Project "{project.name}" updated successfully!')
            return redirect('frontend:projects')
        
        except DomainException:
            # Let SafeTemplateView handle this
            raise


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "POST"])
def delete_project(request, project_id):
    """
    Delete a project.
    Uses ProjectService for write operation.
    Uses ProjectPolicy for authorization.
    Uses ExceptionMapper for consistent error handling.
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
        
        # Check permission using Policy
        # Policy raises PermissionDeniedError if not allowed
        policy = ProjectPolicy()
        policy.can_delete(request.user, project_dto.to_dict() if hasattr(project_dto, 'to_dict') else project_dto).require('delete', 'project')
        
        # Use Service for write operation
        # May raise DomainException (NotFoundError, PermissionDeniedError)
        ProjectService.delete_project(project_id, user=request.user)
        
        return JsonResponse({'success': True, 'message': f'Project deleted successfully.'})
    
    except DomainException as e:
        # Use ExceptionMapper for consistent error response
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
            
            policy = ProjectPolicy()
            policy.can_delete(request.user, project_dto.to_dict() if hasattr(project_dto, 'to_dict') else project_dto).require('delete', 'project')
            
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
            
            # Check permission using Policy
            policy = ProjectPolicy()
            policy.can_edit(request.user, project_dto.to_dict() if hasattr(project_dto, 'to_dict') else project_dto).require('edit', 'project')
            
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

