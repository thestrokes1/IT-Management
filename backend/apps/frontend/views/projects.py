"""
Project views for IT Management Platform.
Contains all project-related views (list, create, edit, delete, API).
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from datetime import datetime
import json

try:
    from apps.users.models import User
    from apps.projects.models import Project, ProjectCategory
except ImportError:
    User = None
    Project = None


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


class CreateProjectView(LoginRequiredMixin, TemplateView):
    """
    Create new project web interface.
    """
    template_name = 'frontend/create-project.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
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
            
            # Convert date strings to date objects
            start_date_obj = None
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    start_date_obj = None
            
            end_date_obj = None
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    end_date_obj = None
            
            deadline_obj = None
            if deadline:
                try:
                    deadline_obj = datetime.strptime(deadline, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    deadline_obj = None
            
            project = Project.objects.create(
                name=name,
                description=description,
                category=category,
                priority=priority,
                project_manager=project_manager,
                objectives=objectives,
                requirements=requirements,
                deliverables=deliverables,
                start_date=start_date_obj,
                end_date=end_date_obj,
                deadline=deadline_obj,
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


class EditProjectView(LoginRequiredMixin, TemplateView):
    """
    Edit project web interface.
    """
    template_name = 'frontend/edit-project.html'
    login_url = 'frontend:login'
    
    def dispatch(self, request, project_id, *args, **kwargs):
        """Check if user can manage projects."""
        if not hasattr(request.user, 'can_manage_projects') or not request.user.can_manage_projects:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'You do not have permission to edit projects.'}, status=403)
            messages.error(request, 'You do not have permission to edit projects.')
            return redirect('frontend:projects')
        self.project_id = project_id
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            project = Project.objects.select_related('category', 'project_manager', 'created_by', 'updated_by').get(id=self.project_id)
            categories = ProjectCategory.objects.filter(is_active=True)
            available_users = User.objects.filter(is_active=True)
            context.update({
                'project': project,
                'categories': categories,
                'available_users': available_users,
                'form': {}
            })
        except Project.DoesNotExist:
            messages.error(self.request, 'Project not found.')
            return redirect('frontend:projects')
        except Exception as e:
            messages.error(self.request, f'Error loading project: {str(e)}')
            return redirect('frontend:projects')
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle project edit."""
        try:
            project = Project.objects.select_related('category', 'project_manager').get(id=self.project_id)
            
            name = request.POST.get('name', '')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category', '')
            status = request.POST.get('status', 'PLANNING')
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
            
            # Update project
            category = ProjectCategory.objects.get(id=category_id)
            project_manager = User.objects.get(id=project_manager_id)
            
            # Convert date strings to datetime.date objects
            start_date_obj = None
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    start_date_obj = None
            
            end_date_obj = None
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    end_date_obj = None
            
            deadline_obj = None
            if deadline:
                try:
                    deadline_obj = datetime.strptime(deadline, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    deadline_obj = None
            
            project.name = name
            project.description = description
            project.category = category
            project.status = status
            project.priority = priority
            project.project_manager = project_manager
            project.objectives = objectives
            project.requirements = requirements
            project.deliverables = deliverables
            project.start_date = start_date_obj
            project.end_date = end_date_obj
            project.deadline = deadline_obj
            project.budget = budget if budget else None
            project.risk_level = risk_level
            project.risk_description = risk_description
            project.updated_by = request.user
            project.save()
            
            messages.success(request, f'Project "{project.name}" updated successfully!')
            return redirect('frontend:projects')
        
        except Project.DoesNotExist:
            messages.error(request, 'Project not found.')
            return redirect('frontend:projects')
        except Exception as e:
            messages.error(request, f'Error updating project: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


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

