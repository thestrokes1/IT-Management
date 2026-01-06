# Project Application Layer.
# Contains use-case classes that orchestrate domain services.
# Acts as intermediary between views (presentation layer) and domain services.
# Handles cross-cutting concerns: authorization, idempotency, transaction boundaries.
# NO HTTP logic, NO Django imports (except for type hints if needed).

from dataclasses import dataclass
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


# =============================================================================
# Result Types
# =============================================================================

@dataclass
class ApplicationResult:
    """Result of an application use case execution."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, data: Dict = None) -> 'ApplicationResult':
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> 'ApplicationResult':
        return cls(success=False, error=error)


@dataclass
class DeleteProjectResult(ApplicationResult):
    """Result of project deletion use case."""
    project_id: int = 0
    project_name: str = ""
    deleted_at: str = ""
    
    @classmethod
    def ok(cls, project_id: int, project_name: str, deleted_at: str) -> 'DeleteProjectResult':
        return cls(
            success=True,
            project_id=project_id,
            project_name=project_name,
            deleted_at=deleted_at,
            data={'id': project_id, 'name': project_name, 'deleted_at': deleted_at}
        )


# =============================================================================
# Base Application Classes
# =============================================================================

class ApplicationUseCase(ABC):
    """
    Base class for all application use cases.
    
    Defines the interface for use case classes that orchestrate
    domain services. Subclasses should implement the execute method.
    
    Features:
    - Accepts request/user context
    - Returns typed ApplicationResult
    - No HTTP logic
    """
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> ApplicationResult:
        """
        Execute the use case.
        
        Returns:
            ApplicationResult with success status and data/error
        """
        pass


class IdempotentUseCase(ApplicationUseCase):
    """
    Base class for use cases that support idempotency.
    
    Adds idempotency_key handling to use cases.
    """
    
    @abstractmethod
    def execute(
        self,
        idempotency_key: Optional[str] = None,
        *args,
        **kwargs
    ) -> ApplicationResult:
        """
        Execute the use case with optional idempotency.
        
        Args:
            idempotency_key: Optional key to prevent duplicate execution
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            ApplicationResult
        """
        pass


# =============================================================================
# Project Use Cases
# =============================================================================

class DeleteProject(IdempotentUseCase):
    """
    Use case for deleting a project.
    
    Orchestrates:
    1. Authorization check via ProjectPolicy
    2. Project retrieval via ProjectQuery
    3. Deletion via ProjectService
    4. Returns typed DeleteProjectResult
    
    Input (via execute):
        project_id: int - ID of project to delete
        user: Any - User performing the deletion
        idempotency_key: Optional[str] - Key to prevent duplicate deletion
    
    Output:
        DeleteProjectResult with success/data or error
    
    Usage:
        result = DeleteProject().execute(
            project_id=123,
            user=request.user,
            idempotency_key="delete-project-123"
        )
        
        if result.success:
            print(f"Deleted {result.project_name}")
        else:
            print(f"Error: {result.error}")
    """
    
    def execute(
        self,
        project_id: int,
        user: Any,
        idempotency_key: Optional[str] = None,
    ) -> DeleteProjectResult:
        """
        Execute project deletion use case.
        
        Args:
            project_id: ID of project to delete
            user: User performing the deletion
            idempotency_key: Optional key to prevent duplicate deletion
            
        Returns:
            DeleteProjectResult with deletion details or error
        """
        from apps.projects.queries import ProjectQuery
        from apps.frontend.services import ProjectService
        from apps.core.policies import ProjectPolicy
        from apps.core.exceptions import PermissionDeniedError, NotFoundError
        
        # Step 1: Get project for authorization
        project_dto = ProjectQuery.get_by_id(project_id)
        
        if project_dto is None:
            return DeleteProjectResult.fail(
                f"Project with id {project_id} not found."
            )
        
        # Step 2: Authorization check
        policy = ProjectPolicy()
        auth_result = policy.can_delete(
            user,
            project_dto.to_dict() if hasattr(project_dto, 'to_dict') else project_dto
        )
        
        if not auth_result.allowed:
            return DeleteProjectResult.fail(
                f"Permission denied: {auth_result.reason}"
            )
        
        # Step 3: Execute deletion via service (with idempotency)
        service_result = ProjectService.delete_project(
            project_id=project_id,
            user=user,
            idempotency_key=idempotency_key,
        )
        
        # Step 4: Return typed result
        if service_result.success:
            data = service_result.data or {}
            return DeleteProjectResult.ok(
                project_id=project_id,
                project_name=data.get('name', 'Unknown'),
                deleted_at=data.get('deleted_at', ''),
            )
        else:
            return DeleteProjectResult.fail(
                service_result.error or "Unknown error during deletion"
            )


class CreateProject(IdempotentUseCase):
    """
    Use case for creating a project.
    
    Orchestrates:
    1. Authorization check via ProjectPolicy
    2. Validation of input data
    3. Project creation via ProjectService
    4. Returns typed result
    
    Input (via execute):
        name: str - Project name
        description: str - Project description
        category_id: str - Category ID
        status: str - Project status
        priority: str - Project priority
        start_date: Optional[str] - Start date
        end_date: Optional[str] - End date
        budget: str - Budget
        owner_id: Optional[str] - Owner user ID
        team_members: list - Team member IDs
        user: Any - User creating the project
        idempotency_key: Optional[str] - Key to prevent duplicate creation
    """
    
    def execute(
        self,
        name: str,
        description: str,
        category_id: str,
        status: str,
        priority: str,
        user: Any,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        budget: str = "0",
        owner_id: Optional[str] = None,
        team_members: Optional[list] = None,
        idempotency_key: Optional[str] = None,
    ) -> ApplicationResult:
        """
        Execute project creation use case.
        
        Returns:
            ApplicationResult with project data or error
        """
        from apps.core.policies import ProjectPolicy
        from apps.frontend.services import ProjectService
        from apps.core.exceptions import PermissionDeniedError
        
        # Authorization check
        policy = ProjectPolicy()
        auth_result = policy.can_create(user)
        
        if not auth_result.allowed:
            return ApplicationResult.fail(
                f"Permission denied: {auth_result.reason}"
            )
        
        # Execute creation
        service_result = ProjectService.create_project(
            request={'user': user},  # Service expects request object
            name=name,
            description=description,
            category_id=category_id,
            status=status,
            priority=priority,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            owner_id=owner_id,
            team_members=team_members or [],
            idempotency_key=idempotency_key,
        )
        
        if service_result.success:
            return ApplicationResult.ok(data=service_result.data)
        else:
            return ApplicationResult.fail(error=service_result.error)


class UpdateProject(IdempotentUseCase):
    """
    Use case for updating a project.
    
    Orchestrates:
    1. Project retrieval
    2. Authorization check
    3. Project update via ProjectService
    4. Returns typed result
    """
    
    def execute(
        self,
        project_id: int,
        name: str,
        description: str,
        category_id: str,
        status: str,
        priority: str,
        user: Any,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        budget: str = "0",
        owner_id: Optional[str] = None,
        team_members: Optional[list] = None,
        idempotency_key: Optional[str] = None,
    ) -> ApplicationResult:
        """Execute project update use case."""
        from apps.projects.queries import ProjectQuery
        from apps.core.policies import ProjectPolicy
        from apps.frontend.services import ProjectService
        
        # Get project
        project_dto = ProjectQuery.get_by_id(project_id)
        
        if project_dto is None:
            return ApplicationResult.fail(
                f"Project with id {project_id} not found."
            )
        
        # Authorization check
        policy = ProjectPolicy()
        auth_result = policy.can_edit(
            user,
            project_dto.to_dict() if hasattr(project_dto, 'to_dict') else project_dto
        )
        
        if not auth_result.allowed:
            return ApplicationResult.fail(
                f"Permission denied: {auth_result.reason}"
            )
        
        # Execute update
        service_result = ProjectService.update_project(
            request={'user': user},
            project_id=project_id,
            name=name,
            description=description,
            category_id=category_id,
            status=status,
            priority=priority,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            owner_id=owner_id,
            team_members=team_members or [],
            idempotency_key=idempotency_key,
        )
        
        if service_result.success:
            return ApplicationResult.ok(data=service_result.data)
        else:
            return ApplicationResult.fail(error=service_result.error)


# =============================================================================
# Use Case Factory
# =============================================================================

class ProjectUseCases:
    """
    Factory class for project-related use cases.
    
    Provides easy access to all project use cases.
    
    Usage:
        delete_result = ProjectUseCases.delete_project(
            project_id=123,
            user=request.user,
        )
    """
    
    @staticmethod
    def delete_project(
        project_id: int,
        user: Any,
        idempotency_key: Optional[str] = None,
    ) -> DeleteProjectResult:
        """Delete a project."""
        return DeleteProject().execute(
            project_id=project_id,
            user=user,
            idempotency_key=idempotency_key,
        )
    
    @staticmethod
    def create_project(
        name: str,
        description: str,
        category_id: str,
        status: str,
        priority: str,
        user: Any,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        budget: str = "0",
        owner_id: Optional[str] = None,
        team_members: Optional[list] = None,
        idempotency_key: Optional[str] = None,
    ) -> ApplicationResult:
        """Create a new project."""
        return CreateProject().execute(
            name=name,
            description=description,
            category_id=category_id,
            status=status,
            priority=priority,
            user=user,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            owner_id=owner_id,
            team_members=team_members,
            idempotency_key=idempotency_key,
        )
    
    @staticmethod
    def update_project(
        project_id: int,
        name: str,
        description: str,
        category_id: str,
        status: str,
        priority: str,
        user: Any,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        budget: str = "0",
        owner_id: Optional[str] = None,
        team_members: Optional[list] = None,
        idempotency_key: Optional[str] = None,
    ) -> ApplicationResult:
        """Update an existing project."""
        return UpdateProject().execute(
            project_id=project_id,
            name=name,
            description=description,
            category_id=category_id,
            status=status,
            priority=priority,
            user=user,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            owner_id=owner_id,
            team_members=team_members,
            idempotency_key=idempotency_key,
        )

