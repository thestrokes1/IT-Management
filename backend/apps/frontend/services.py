# Frontend services module.
# Contains command services for state mutations (create, update, delete).
# Uses domain exceptions for error handling - no HttpResponse/JsonResponse in services.
# Uses authorization policies for permission checks.
# Uses domain events for activity tracking (no persistence logic in services).

from typing import Optional, Dict
from django.utils import timezone
from django.db import transaction

from apps.core.exceptions import (
    NotFoundError,
    ValidationError,
    PermissionDeniedError,
    DomainException,
)
from apps.core.policies import ProjectPolicy
from apps.core.events import (
    EventPublisher,
    ProjectCreated,
    ProjectUpdated,
    ProjectDeleted,
)


class ProjectService(EventPublisher):
    """
    Service class for Project commands.
    Handles all state mutations for projects.
    Raises ONLY domain exceptions - no HTTP responses.
    Uses ProjectPolicy for authorization checks.
    Uses EventPublisher to emit domain events after successful commands.
    """
    
    # Policy instance for authorization checks
    _policy = ProjectPolicy()
    
    @classmethod
    def _get_project_or_raise(cls, project_id: int):
        """
        Get project by ID or raise NotFoundError.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Project object
            
        Raises:
            NotFoundError: If project not found
        """
        from apps.projects.models import Project
        try:
            return Project.objects.get(id=project_id)
        except (Project.DoesNotExist, ValueError):
            raise NotFoundError(
                resource_type="Project",
                resource_id=project_id
            )
    
    @classmethod
    def _get_category_or_raise(cls, category_id: str):
        """
        Get category by ID or raise NotFoundError.
        
        Args:
            category_id: The ID of the category
            
        Returns:
            ProjectCategory object
            
        Raises:
            NotFoundError: If category not found
        """
        from apps.projects.models import ProjectCategory
        if not category_id:
            return None
        try:
            return ProjectCategory.objects.get(id=category_id)
        except (ProjectCategory.DoesNotExist, ValueError):
            raise NotFoundError(
                resource_type="ProjectCategory",
                resource_id=category_id
            )
    
    @classmethod
    def _get_user_or_raise(cls, user_id: str):
        """
        Get user by ID or raise NotFoundError.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            User object
            
        Raises:
            NotFoundError: If user not found
        """
        from apps.users.models import User
        if not user_id:
            return None
        try:
            return User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError):
            raise NotFoundError(
                resource_type="User",
                resource_id=user_id
            )
    
    @classmethod
    def _validate_project_data(
        cls,
        name: str,
        description: str,
        raise_on_empty: bool = True
    ) -> dict:
        """
        Validate project input data.
        
        Args:
            name: Project name
            description: Project description
            raise_on_empty: Whether to raise ValidationError on empty fields
            
        Returns:
            Dictionary with validated data
            
        Raises:
            ValidationError: If validation fails
        """
        errors = {}
        
        if not name or not name.strip():
            errors['name'] = 'Project name is required'
        elif len(name) > 255:
            errors['name'] = 'Project name must be 255 characters or less'
        
        if not description or not description.strip():
            errors['description'] = 'Description is required'
        
        if errors:
            raise ValidationError(
                message="Project validation failed",
                errors=errors
            )
        
        return {
            'name': name.strip(),
            'description': description.strip()
        }
    
    @classmethod
    def _track_changes(
        cls,
        old_project: 'Project',
        new_data: dict,
        exclude_fields: set = None
    ) -> Dict[str, tuple]:
        """
        Track field changes between old and new values.
        
        Args:
            old_project: Original project instance
            new_data: Dictionary of new field values
            exclude_fields: Fields to exclude from tracking
            
        Returns:
            Dictionary of {field: (old_value, new_value)}
        """
        if exclude_fields is None:
            exclude_fields = {'id', 'created_at', 'updated_at', 'created_by', 'updated_by'}
        
        changes = {}
        for field, new_value in new_data.items():
            if field in exclude_fields:
                continue
            
            old_value = getattr(old_project, field, None)
            
            # Handle many-to-many and foreign key comparisons
            if hasattr(old_value, 'all'):
                # For relations, compare IDs
                old_ids = set(old_value.values_list('id', flat=True)) if hasattr(old_value, 'values_list') else {
                    obj.id for obj in old_value.all()
                }
                new_ids = set(new_value) if isinstance(new_value, (list, set)) else set()
                if old_ids != new_ids:
                    changes[field] = (list(old_ids), list(new_ids))
            elif str(old_value) != str(new_value):
                changes[field] = (old_value, new_value)
        
        return changes
    
    @classmethod
    def create_project(
        cls,
        request,
        name: str,
        description: str,
        category_id: str,
        status: str,
        priority: str,
        start_date: Optional[str],
        end_date: Optional[str],
        budget: str,
        owner_id: Optional[str],
        team_members: list
    ) -> 'Project':
        """
        Create a new project.
        Emits ProjectCreated event after successful creation.
        
        Args:
            request: HTTP request object
            name: Project name
            description: Project description
            category_id: Category ID
            status: Project status
            priority: Project priority
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            budget: Budget string
            owner_id: Owner user ID
            team_members: List of team member IDs
            
        Returns:
            Created Project object
            
        Raises:
            ValidationError: If input validation fails
            NotFoundError: If referenced resources not found
            PermissionDeniedError: If user lacks permission
        """
        from apps.projects.models import (
            Project, ProjectCategory, ProjectMembership
        )
        from apps.users.models import User
        from datetime import datetime
        
        # Check authorization using Policy
        # Policy raises PermissionDeniedError if not allowed
        cls._policy.can_create(request.user).require('create', 'project')
        
        # Validate input data
        validated = cls._validate_project_data(name, description)
        
        # Parse dates
        start_date_obj = None
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError(
                    message="Invalid start date format",
                    field='start_date',
                    details={'expected_format': 'YYYY-MM-DD'}
                )
        
        end_date_obj = None
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError(
                    message="Invalid end date format",
                    field='end_date',
                    details={'expected_format': 'YYYY-MM-DD'}
                )
        
        # Get related objects (will raise NotFoundError if not found)
        category = cls._get_category_or_raise(category_id)
        owner = cls._get_user_or_raise(owner_id)
        
        # Parse budget
        try:
            budget_value = float(budget) if budget else 0.0
        except (ValueError, TypeError):
            raise ValidationError(
                message="Invalid budget value",
                field='budget'
            )
        
        # Create project
        project = Project.objects.create(
            name=validated['name'],
            description=validated['description'],
            category=category,
            status=status or 'PLANNING',
            priority=priority or 'MEDIUM',
            start_date=start_date_obj,
            end_date=end_date_obj,
            budget=budget_value,
            owner=owner,
            created_by=request.user
        )
        
        # Add team members
        for member_id in team_members:
            try:
                member = User.objects.get(id=member_id)
                ProjectMembership.objects.get_or_create(
                    project=project,
                    user=member,
                    defaults={'role': 'MEMBER', 'joined_at': timezone.now()}
                )
            except (User.DoesNotExist, ValueError):
                # Skip invalid member IDs
                pass
        
        # Emit domain event - NO logging/persistence logic in service
        cls._publish_event(
            ProjectCreated(
                actor=request.user,
                entity_id=project.id,
                name=project.name,
                status=project.status,
                priority=project.priority,
                category_id=str(category_id) if category_id else None,
                budget=project.budget,
            )
        )
        
        return project
    
    @classmethod
    def update_project(
        cls,
        request,
        project_id: int,
        name: str,
        description: str,
        category_id: str,
        status: str,
        priority: str,
        start_date: Optional[str],
        end_date: Optional[str],
        budget: str,
        owner_id: Optional[str],
        team_members: list
    ) -> 'Project':
        """
        Update an existing project.
        Emits ProjectUpdated event after successful update.
        
        Args:
            request: HTTP request object
            project_id: Project ID to update
            name: Project name
            description: Project description
            category_id: Category ID
            status: Project status
            priority: Project priority
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            budget: Budget string
            owner_id: Owner user ID
            team_members: List of team member IDs
            
        Returns:
            Updated Project object
            
        Raises:
            NotFoundError: If project not found
            ValidationError: If input validation fails
            PermissionDeniedError: If user lacks permission
        """
        from apps.projects.models import (
            Project, ProjectCategory, ProjectMembership
        )
        from apps.users.models import User
        from datetime import datetime
        
        # Get project or raise NotFoundError
        project = cls._get_project_or_raise(project_id)
        
        # Store old values for change tracking
        old_data = {
            'name': project.name,
            'description': project.description,
            'category_id': str(project.category_id) if project.category_id else None,
            'status': project.status,
            'priority': project.priority,
            'budget': project.budget,
            'owner_id': str(project.owner_id) if project.owner_id else None,
        }
        
        # Check authorization using Policy
        # Policy raises PermissionDeniedError if not allowed
        cls._policy.can_edit(request.user, project).require('edit', 'project')
        
        # Validate input data
        validated = cls._validate_project_data(name, description)
        
        # Parse dates
        start_date_obj = None
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError(
                    message="Invalid start date format",
                    field='start_date',
                    details={'expected_format': 'YYYY-MM-DD'}
                )
        
        end_date_obj = None
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError(
                    message="Invalid end date format",
                    field='end_date',
                    details={'expected_format': 'YYYY-MM-DD'}
                )
        
        # Get related objects (will raise NotFoundError if not found)
        category = cls._get_category_or_raise(category_id)
        owner = cls._get_user_or_raise(owner_id)
        
        # Parse budget
        try:
            budget_value = float(budget) if budget else 0.0
        except (ValueError, TypeError):
            raise ValidationError(
                message="Invalid budget value",
                field='budget'
            )
        
        # Prepare new data for change tracking
        new_data = {
            'name': validated['name'],
            'description': validated['description'],
            'category_id': str(category_id) if category_id else None,
            'status': status or 'PLANNING',
            'priority': priority or 'MEDIUM',
            'budget': budget_value,
            'owner_id': str(owner_id) if owner_id else None,
        }
        
        # Update project
        project.name = validated['name']
        project.description = validated['description']
        project.category = category
        project.status = status or 'PLANNING'
        project.priority = priority or 'MEDIUM'
        project.start_date = start_date_obj
        project.end_date = end_date_obj
        project.budget = budget_value
        project.owner = owner
        project.updated_by = request.user
        project.save()
        
        # Update team members
        ProjectMembership.objects.filter(project=project).delete()
        for member_id in team_members:
            try:
                member = User.objects.get(id=member_id)
                ProjectMembership.objects.get_or_create(
                    project=project,
                    user=member,
                    defaults={'role': 'MEMBER', 'joined_at': timezone.now()}
                )
            except (User.DoesNotExist, ValueError):
                pass
        
        # Track changes
        changes = cls._track_changes(
            Project(**old_data),
            new_data,
            exclude_fields={'id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'start_date', 'end_date'}
        )
        
        # Emit domain event - NO logging/persistence logic in service
        cls._publish_event(
            ProjectUpdated(
                actor=request.user,
                entity_id=project.id,
                name=project.name,
                status=project.status,
                priority=project.priority,
                changes=changes,
            )
        )
        
        return project
    
    @classmethod
    def delete_project(cls, project_id: int, user=None) -> bool:
        """
        Delete a project and all related records.
        Emits ProjectDeleted event after successful deletion.
        
        Args:
            project_id: Project ID to delete
            user: User performing the deletion (required for authorization and event)
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If project not found
            PermissionDeniedError: If user lacks permission
        """
        from apps.projects.models import Project, ProjectTask, ProjectMembership
        
        # Get project or raise NotFoundError
        project = cls._get_project_or_raise(project_id)
        
        # Store project name before deletion for event
        project_name = project.name
        
        # Check authorization using Policy
        # Policy raises PermissionDeniedError if user lacks permission
        cls._policy.can_delete(user, project).require('delete', 'project')
        
        with transaction.atomic():
            # Delete related records
            ProjectTask.objects.filter(project=project).delete()
            ProjectMembership.objects.filter(project=project).delete()
            project.delete()
        
        # Emit domain event - NO logging/persistence logic in service
        cls._publish_event(
            ProjectDeleted(
                actor=user,
                entity_id=project_id,
                name=project_name,
            )
        )
        
        return True


