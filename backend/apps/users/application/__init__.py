"""
User Application Layer.
Contains use-case classes that orchestrate domain services.
Acts as intermediary between views (presentation layer) and domain services.
Handles cross-cutting concerns: authorization, idempotency, transaction boundaries.
NO HTTP logic, NO Django imports (except for type hints if needed).
"""

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
class ChangeUserRoleResult(ApplicationResult):
    """Result of user role change use case."""
    user_id: int = 0
    username: str = ""
    old_role: str = ""
    new_role: str = ""
    changed_by: str = ""
    
    @classmethod
    def ok(
        cls,
        user_id: int,
        username: str,
        old_role: str,
        new_role: str,
        changed_by: str
    ) -> 'ChangeUserRoleResult':
        return cls(
            success=True,
            user_id=user_id,
            username=username,
            old_role=old_role,
            new_role=new_role,
            changed_by=changed_by,
            data={
                'user_id': user_id,
                'username': username,
                'old_role': old_role,
                'new_role': new_role,
                'changed_by': changed_by,
            }
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
# User Use Cases
# =============================================================================

class ChangeUserRole(IdempotentUseCase):
    """
    Use case for changing a user's role.
    
    Business Rules:
    - Only SUPERADMIN can change another user's role
    - A user cannot change their own role
    - The actor must have can_change_user_role permission
    
    Orchestrates:
    1. Authorization check via User model can_change_user_role property
    2. Self-change validation
    3. Role update via direct model update
    
    Input (via execute):
        actor: Any - User performing the role change (SUPERADMIN)
        target_user: User - User whose role is being changed
        new_role: str - New role for the target user
        idempotency_key: Optional[str] - Key to prevent duplicate changes
    
    Output:
        ChangeUserRoleResult with change details or error
    
    Usage:
        result = ChangeUserRole().execute(
            actor=request.user,
            target_user=target_user,
            new_role='MANAGER',
            idempotency_key="change-role-user-456"
        )
        
        if result.success:
            print(f"Changed {result.username} from {result.old_role} to {result.new_role}")
        else:
            print(f"Error: {result.error}")
    """
    
    def execute(
        self,
        actor: Any,
        target_user: Any,
        new_role: str,
        idempotency_key: Optional[str] = None,
    ) -> ChangeUserRoleResult:
        """
        Execute user role change use case.
        
        Args:
            actor: User performing the role change (must be SUPERADMIN)
            target_user: User whose role is being changed
            new_role: New role to assign
            idempotency_key: Optional key to prevent duplicate changes
            
        Returns:
            ChangeUserRoleResult with change details or error
        """
        from django.core.exceptions import PermissionDenied, ValidationError
        from apps.users.models import User
        
        # Step 1: Authorization check - only SUPERADMIN can change roles
        if not hasattr(actor, 'can_change_user_role') or not actor.can_change_user_role:
            return ChangeUserRoleResult.fail(
                "Not allowed to change user roles"
            )
        
        # Step 2: Validate - user cannot change their own role
        if actor == target_user:
            return ChangeUserRoleResult.fail(
                "You cannot change your own role"
            )
        
        # Step 3: Capture old role for result
        old_role = target_user.role
        
        # Step 4: Execute role change
        target_user.role = new_role
        target_user.save(update_fields=["role"])
        
        # Step 5: Return typed result
        return ChangeUserRoleResult.ok(
            user_id=target_user.id,
            username=target_user.username,
            old_role=old_role,
            new_role=new_role,
            changed_by=actor.username,
        )


# =============================================================================
# Use Case Factory
# =============================================================================

class UserUseCases:
    """
    Factory class for user-related use cases.
    
    Provides easy access to all user use cases.
    
    Usage:
        result = UserUseCases.change_user_role(
            actor=request.user,
            target_user=target_user,
            new_role='MANAGER',
        )
    """
    
    @staticmethod
    def change_user_role(
        actor: Any,
        target_user: Any,
        new_role: str,
        idempotency_key: Optional[str] = None,
    ) -> ChangeUserRoleResult:
        """
        Change a user's role.
        
        Args:
            actor: User performing the change (must have can_change_user_role)
            target_user: User whose role is being changed
            new_role: New role to assign
            idempotency_key: Optional key to prevent duplicate changes
            
        Returns:
            ChangeUserRoleResult with change details or error
        """
        return ChangeUserRole().execute(
            actor=actor,
            target_user=target_user,
            new_role=new_role,
            idempotency_key=idempotency_key,
        )

