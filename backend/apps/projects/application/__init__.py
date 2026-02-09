# Project Application Layer.
# Contains use-case classes (CQRS commands) that orchestrate domain services.
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
    ):
        """Delete a project."""
        from .delete_project import DeleteProject
        return DeleteProject().execute(
            user=user,
            project_id=project_id,
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
    ):
        """Create a new project."""
        from .create_project import CreateProject
        return CreateProject().execute(
            user=user,
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
    ):
        """Update an existing project."""
        from .update_project import UpdateProject
        return UpdateProject().execute(
            user=user,
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
        )


# =============================================================================
# CQRS Commands with Activity Logging
# =============================================================================
# These commands use domain authority and include activity logging
# Following the same pattern as apps/tickets/application/* and apps/assets/application/*

from .create_project import CreateProject, CreateProjectResult
from .update_project import UpdateProject, UpdateProjectResult
from .delete_project import DeleteProject, DeleteProjectResult
from .manage_members import (
    AddProjectMember, AddProjectMemberResult,
    RemoveProjectMember, RemoveProjectMemberResult
)
from .change_status import ChangeProjectStatus, ChangeProjectStatusResult

__all__ = [
    # Base classes
    'ApplicationResult',
    'ApplicationUseCase',
    'IdempotentUseCase',
    # Factory
    'ProjectUseCases',
    # CQRS Commands
    'CreateProject',
    'CreateProjectResult',
    'UpdateProject',
    'UpdateProjectResult',
    'DeleteProject',
    'DeleteProjectResult',
    'AddProjectMember',
    'AddProjectMemberResult',
    'RemoveProjectMember',
    'RemoveProjectMemberResult',
    'ChangeProjectStatus',
    'ChangeProjectStatusResult',
]
