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
from apps.projects.policies import ProjectPolicy
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
            Project, ProjectCategory, ProjectMember
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
        # Default to request.user if no valid owner is provided (since project_manager is required)
        owner = cls._get_user_or_raise(owner_id) or request.user
        
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
            project_manager=owner,
            created_by=request.user
        )
        
        # Add team members
        for member_id in team_members:
            try:
                member = User.objects.get(id=member_id)
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=member,
                    defaults={'role': 'MEMBER', 'joined_date': timezone.now().date()}
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
            Project, ProjectCategory, ProjectMember
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
            'project_manager_id': str(project.project_manager_id) if project.project_manager_id else None,
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
        # Default to existing project_manager if no valid owner is provided
        owner = cls._get_user_or_raise(owner_id) or project.project_manager
        
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
            'project_manager_id': str(owner.id) if owner else None,
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
        project.project_manager = owner
        project.updated_by = request.user
        project.save()
        
        # Update team members
        ProjectMember.objects.filter(project=project).delete()
        for member_id in team_members:
            try:
                member = User.objects.get(id=member_id)
                ProjectMember.objects.get_or_create(
                    project=project,
                    user=member,
                    defaults={'role': 'MEMBER', 'joined_date': timezone.now().date()}
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
        from apps.projects.models import Project, Task, ProjectMember
        
        # Get project or raise NotFoundError
        project = cls._get_project_or_raise(project_id)
        
        # Store project name before deletion for event
        project_name = project.name
        
        # Check authorization using Policy
        # Policy raises PermissionDeniedError if user lacks permission
        cls._policy.can_delete(user, project).require('delete', 'project')
        
        with transaction.atomic():
            # Delete related records
            Task.objects.filter(project=project).delete()
            ProjectMember.objects.filter(project=project).delete()
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


class TicketService(EventPublisher):
    """
    Service class for Ticket commands.
    Handles all state mutations for tickets.
    Raises ONLY domain exceptions - no HTTP responses.
    """
    
    @classmethod
    def _get_ticket_or_raise(cls, ticket_id: int):
        """Get ticket by ID or raise NotFoundError."""
        from apps.tickets.models import Ticket
        try:
            return Ticket.objects.get(id=ticket_id)
        except (Ticket.DoesNotExist, ValueError):
            raise NotFoundError(
                resource_type="Ticket",
                resource_id=ticket_id
            )
    
    @classmethod
    def create_ticket(
        cls,
        request,
        title: str,
        description: str,
        category_id: str,
        ticket_type_id: str,
        priority: str = 'MEDIUM',
        impact: str = 'MEDIUM',
        urgency: str = 'MEDIUM',
        assigned_to_id: str = '',
        due_date: str = ''
    ) -> 'Ticket':
        """Create a new ticket."""
        from apps.tickets.models import Ticket, TicketCategory, TicketType
        from datetime import datetime
        
        # Validate required fields
        if not title or not title.strip():
            raise ValidationError(message="Title is required", field='title')
        if not description or not description.strip():
            raise ValidationError(message="Description is required", field='description')
        
        # Get related objects
        try:
            category = TicketCategory.objects.get(id=category_id) if category_id else None
        except (TicketCategory.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="TicketCategory", resource_id=category_id)
        
        try:
            ticket_type = TicketType.objects.get(id=ticket_type_id) if ticket_type_id else None
        except (TicketType.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="TicketType", resource_id=ticket_type_id)
        
        assigned_to = None
        if assigned_to_id:
            from apps.users.models import User
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
            except (User.DoesNotExist, ValueError):
                pass  # Optional field
        
        # Parse due date
        sla_due_at = None
        if due_date:
            try:
                sla_due_at = datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                pass  # Optional field
        
        # Create ticket
        ticket = Ticket.objects.create(
            title=title.strip(),
            description=description.strip(),
            category=category,
            ticket_type=ticket_type,
            priority=priority,
            impact=impact,
            urgency=urgency,
            assigned_to=assigned_to,
            sla_due_at=sla_due_at,
            requester=request.user,
            created_by=request.user
        )
        
        return ticket
    
    @classmethod
    def update_ticket(
        cls,
        request,
        ticket_id: int,
        title: str,
        description: str,
        category_id: str,
        ticket_type_id: str,
        status: str = 'NEW',
        priority: str = 'MEDIUM',
        impact: str = 'MEDIUM',
        urgency: str = 'MEDIUM',
        assigned_to_id: str = '',
        assigned_team: str = '',
        location: str = '',
        contact_phone: str = '',
        contact_email: str = '',
        sla_due_at_str: str = '',
        resolution_summary: str = ''
    ) -> 'Ticket':
        """Update an existing ticket."""
        from apps.tickets.models import Ticket, TicketCategory, TicketType
        from datetime import datetime
        
        ticket = cls._get_ticket_or_raise(ticket_id)
        
        # Validate required fields
        if not title or not title.strip():
            raise ValidationError(message="Title is required", field='title')
        if not description or not description.strip():
            raise ValidationError(message="Description is required", field='description')
        
        # Get related objects
        try:
            category = TicketCategory.objects.get(id=category_id) if category_id else ticket.category
        except (TicketCategory.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="TicketCategory", resource_id=category_id)
        
        try:
            ticket_type = TicketType.objects.get(id=ticket_type_id) if ticket_type_id else ticket.ticket_type
        except (TicketType.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="TicketType", resource_id=ticket_type_id)
        
        assigned_to = ticket.assigned_to
        if assigned_to_id:
            from apps.users.models import User
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
            except (User.DoesNotExist, ValueError):
                pass
        
        # Parse SLA due date
        sla_due_at = ticket.sla_due_at
        if sla_due_at_str:
            try:
                sla_due_at = datetime.strptime(sla_due_at_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        # Update ticket
        ticket.title = title.strip()
        ticket.description = description.strip()
        ticket.category = category
        ticket.ticket_type = ticket_type
        ticket.status = status
        ticket.priority = priority
        ticket.impact = impact
        ticket.urgency = urgency
        ticket.assigned_to = assigned_to
        ticket.assigned_team = assigned_team.strip()
        ticket.location = location.strip()
        ticket.contact_phone = contact_phone.strip()
        ticket.contact_email = contact_email.strip()
        ticket.sla_due_at = sla_due_at
        ticket.resolution_summary = resolution_summary.strip()
        ticket.updated_by = request.user
        ticket.save()
        
        return ticket
    
    @classmethod
    def delete_ticket(cls, ticket_id: int) -> bool:
        """Delete a ticket."""
        ticket = cls._get_ticket_or_raise(ticket_id)
        ticket.delete()
        return True
    
    @classmethod
    def partial_update_ticket(cls, ticket_id: int, data: dict) -> 'Ticket':
        """Partially update a ticket."""
        from apps.tickets.models import Ticket
        
        ticket = cls._get_ticket_or_raise(ticket_id)
        
        # Update only provided fields
        for field, value in data.items():
            if hasattr(ticket, field) and field not in ['id', 'ticket_id', 'created_at', 'updated_at']:
                setattr(ticket, field, value)
        
        ticket.save()
        return ticket


class AssetService(EventPublisher):
    """
    Service class for Asset commands.
    Handles all state mutations for assets.
    Raises ONLY domain exceptions - no HTTP responses.
    """
    
    @classmethod
    def _get_asset_or_raise(cls, asset_id: int):
        """Get asset by ID or raise NotFoundError."""
        from apps.assets.models import Asset
        try:
            return Asset.objects.get(id=asset_id)
        except (Asset.DoesNotExist, ValueError):
            raise NotFoundError(
                resource_type="Asset",
                resource_id=asset_id
            )
    
    @classmethod
    def create_asset(
        cls,
        request,
        name: str,
        description: str,
        category_id: str,
        serial_number: str = '',
        asset_tag: str = '',  # Not in model, but used in views
        status: str = 'ACTIVE',
        location: str = '',
        purchase_date: str = '',
        purchase_price: str = '',
        warranty_expiry: str = '',
        assigned_to_id: str = ''
    ) -> 'Asset':
        """Create a new asset."""
        from apps.assets.models import Asset, AssetCategory
        from datetime import datetime
        
        # Validate required fields
        if not name or not name.strip():
            raise ValidationError(message="Name is required", field='name')
        
        # Get category
        try:
            category = AssetCategory.objects.get(id=category_id) if category_id else None
        except (AssetCategory.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="AssetCategory", resource_id=category_id)
        
        # Determine asset type (default to HARDWARE)
        asset_type = 'HARDWARE'  # Default, can be made configurable
        
        # Parse dates
        purchase_date_obj = None
        if purchase_date:
            try:
                purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        warranty_expiry_obj = None
        if warranty_expiry:
            try:
                warranty_expiry_obj = datetime.strptime(warranty_expiry, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Parse purchase price
        purchase_cost = None
        if purchase_price:
            try:
                purchase_cost = float(purchase_price)
            except (ValueError, TypeError):
                pass
        
        # Get assigned user
        assigned_to = None
        if assigned_to_id:
            from apps.users.models import User
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
            except (User.DoesNotExist, ValueError):
                pass
        
        # Create asset
        asset = Asset.objects.create(
            name=name.strip(),
            description=description.strip(),
            asset_type=asset_type,
            category=category,
            serial_number=serial_number.strip() if serial_number else '',
            status=status,
            location=location.strip(),
            purchase_date=purchase_date_obj,
            purchase_cost=purchase_cost,
            warranty_expiry=warranty_expiry_obj,
            assigned_to=assigned_to,
            created_by=request.user
        )
        
        return asset
    
    @classmethod
    def update_asset(
        cls,
        request,
        asset_id: int,
        name: str,
        description: str,
        category_id: str,
        serial_number: str = '',
        asset_tag: str = '',  # Not in model, but used in views
        status: str = 'ACTIVE',
        location: str = '',
        purchase_date: str = '',
        purchase_price: str = '',
        warranty_expiry: str = '',
        assigned_to_id: str = ''
    ) -> 'Asset':
        """Update an existing asset."""
        from apps.assets.models import Asset, AssetCategory
        from datetime import datetime
        
        asset = cls._get_asset_or_raise(asset_id)
        
        # Validate required fields
        if not name or not name.strip():
            raise ValidationError(message="Name is required", field='name')
        
        # Get category
        try:
            category = AssetCategory.objects.get(id=category_id) if category_id else asset.category
        except (AssetCategory.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="AssetCategory", resource_id=category_id)
        
        # Parse dates
        purchase_date_obj = asset.purchase_date
        if purchase_date:
            try:
                purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        warranty_expiry_obj = asset.warranty_expiry
        if warranty_expiry:
            try:
                warranty_expiry_obj = datetime.strptime(warranty_expiry, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Parse purchase price
        purchase_cost = asset.purchase_cost
        if purchase_price:
            try:
                purchase_cost = float(purchase_price)
            except (ValueError, TypeError):
                pass
        
        # Get assigned user
        assigned_to = asset.assigned_to
        if assigned_to_id:
            from apps.users.models import User
            try:
                assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
            except (User.DoesNotExist, ValueError):
                pass
        
        # Update asset
        asset.name = name.strip()
        asset.description = description.strip()
        asset.category = category
        asset.serial_number = serial_number.strip() if serial_number else asset.serial_number
        asset.status = status
        asset.location = location.strip()
        asset.purchase_date = purchase_date_obj
        asset.purchase_cost = purchase_cost
        asset.warranty_expiry = warranty_expiry_obj
        asset.assigned_to = assigned_to
        asset.updated_by = request.user
        asset.save()
        
        return asset
    
    @classmethod
    def delete_asset(cls, asset_id: int) -> bool:
        """Delete an asset."""
        asset = cls._get_asset_or_raise(asset_id)
        asset.delete()
        return True


