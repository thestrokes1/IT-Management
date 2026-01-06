# Project authorization policy.
# Contains authorization rules for Project entities.
# Placed in domain layer (apps/projects/) following Clean Architecture.
# Policies are imported from core.policies base classes.

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.core.policies import (
    AuthorizationPolicy,
    AuthorizationResult,
    RoleBasedPolicy,
    get_policy,
)


@dataclass
class ProjectContext:
    """
    Context data for project authorization decisions.
    
    Provides structured access to resource data for policy evaluation.
    """
    resource_id: Optional[int] = None
    resource_status: Optional[str] = None
    owner_id: Optional[int] = None
    created_by_id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectContext':
        """Create context from dictionary."""
        if data is None:
            return cls()
        return cls(
            resource_id=data.get('id'),
            resource_status=data.get('status'),
            owner_id=data.get('owner_id') or data.get('owner'),
            created_by_id=data.get('created_by_id') or data.get('created_by'),
        )


class ProjectPolicy(AuthorizationPolicy, RoleBasedPolicy):
    """
    Authorization policy for Project entities.
    
    Implements role-based access control with owner overrides.
    
    Role Hierarchy:
        - admin: Full access to all projects
        - manager: Can manage projects they own or are assigned to
        - editor: Can edit projects they own or are assigned to
        - member: Can view projects they are assigned to
        - viewer: Can view public projects only
    
    Ownership Rules:
        - Project owner has full control regardless of role
        - Admin bypasses ownership checks
    """
    
    @property
    def name(self) -> str:
        return "ProjectPolicy"
    
    def can_view(
        self,
        user: Any,
        resource: Any = None
    ) -> AuthorizationResult:
        """
        Check if user can view the project.
        
        Rules:
        - Admin can view all projects
        - Authenticated users can view projects they own/created
        - Authenticated users can view assigned projects
        - Anonymous users can only view public projects (future)
        
        Args:
            user: User requesting access
            resource: Optional project data for context
            
        Returns:
            AuthorizationResult with allowed/reason
        """
        if not user or not user.is_authenticated:
            return AuthorizationResult(
                allowed=False,
                reason="Authentication required to view projects",
                policy=self.name
            )
        
        # Admin has full access
        if user.is_superuser or self._has_role_at_least(user, 'admin'):
            return AuthorizationResult(
                allowed=True,
                reason="Administrator access granted",
                policy=self.name
            )
        
        # Get resource context
        context = ProjectContext.from_dict(resource)
        
        # Check if user owns the project
        if context.owner_id and hasattr(user, 'id') and user.id == context.owner_id:
            return AuthorizationResult(
                allowed=True,
                reason="Project owner access granted",
                policy=self.name
            )
        
        # Check if user created the project
        if context.created_by_id and hasattr(user, 'id') and user.id == context.created_by_id:
            return AuthorizationResult(
                allowed=True,
                reason="Project creator access granted",
                policy=self.name
            )
        
        # Check role-based access
        if self._has_role_at_least(user, 'member'):
            return AuthorizationResult(
                allowed=True,
                reason="Member role grants view access",
                policy=self.name
            )
        
        return AuthorizationResult(
            allowed=False,
            reason="No permission to view this project",
            policy=self.name
        )
    
    def can_create(
        self,
        user: Any,
        resource: Any = None
    ) -> AuthorizationResult:
        """
        Check if user can create new projects.
        
        Rules:
        - Admin can always create projects
        - Users with manager role or higher can create projects
        
        Args:
            user: User requesting access
            resource: Optional resource data for context
            
        Returns:
            AuthorizationResult with allowed/reason
        """
        if not user or not user.is_authenticated:
            return AuthorizationResult(
                allowed=False,
                reason="Authentication required to create projects",
                policy=self.name
            )
        
        # Admin can always create
        if user.is_superuser or self._has_role_at_least(user, 'admin'):
            return AuthorizationResult(
                allowed=True,
                reason="Administrator can create projects",
                policy=self.name
            )
        
        # Manager role required
        if self._has_role_at_least(user, 'manager'):
            return AuthorizationResult(
                allowed=True,
                reason="Manager role grants create permission",
                policy=self.name
            )
        
        return AuthorizationResult(
            allowed=False,
            reason="Manager role or higher required to create projects",
            policy=self.name
        )
    
    def can_edit(
        self,
        user: Any,
        resource: Any
    ) -> AuthorizationResult:
        """
        Check if user can edit the project.
        
        Rules:
        - Admin can edit all projects
        - Owner can always edit their projects
        - Manager can edit projects they have access to
        
        Args:
            user: User requesting access
            resource: Project to edit (dict or Project instance)
            
        Returns:
            AuthorizationResult with allowed/reason
        """
        if not user or not user.is_authenticated:
            return AuthorizationResult(
                allowed=False,
                reason="Authentication required to edit projects",
                policy=self.name
            )
        
        # Admin has full access
        if user.is_superuser or self._has_role_at_least(user, 'admin'):
            return AuthorizationResult(
                allowed=True,
                reason="Administrator access granted",
                policy=self.name
            )
        
        # Get resource context
        context = ProjectContext.from_dict(resource)
        
        # Owner can always edit
        if context.owner_id and hasattr(user, 'id') and user.id == context.owner_id:
            return AuthorizationResult(
                allowed=True,
                reason="Project owner can edit",
                policy=self.name
            )
        
        # Check if user created the project
        if context.created_by_id and hasattr(user, 'id') and user.id == context.created_by_id:
            return AuthorizationResult(
                allowed=True,
                reason="Project creator can edit",
                policy=self.name
            )
        
        # Editor role can edit assigned projects
        if self._has_role_at_least(user, 'editor'):
            return AuthorizationResult(
                allowed=True,
                reason="Editor role grants edit access",
                policy=self.name
            )
        
        return AuthorizationResult(
            allowed=False,
            reason="No permission to edit this project",
            policy=self.name
        )
    
    def can_delete(
        self,
        user: Any,
        resource: Any
    ) -> AuthorizationResult:
        """
        Check if user can delete the project.
        
        Rules:
        - Admin can delete all projects
        - Owner can delete their projects
        - Manager can delete projects with appropriate status
        
        Args:
            user: User requesting access
            resource: Project to delete
            
        Returns:
            AuthorizationResult with allowed/reason
        """
        if not user or not user.is_authenticated:
            return AuthorizationResult(
                allowed=False,
                reason="Authentication required to delete projects",
                policy=self.name
            )
        
        # Admin has full access
        if user.is_superuser or self._has_role_at_least(user, 'admin'):
            return AuthorizationResult(
                allowed=True,
                reason="Administrator can delete projects",
                policy=self.name
            )
        
        # Get resource context
        context = ProjectContext.from_dict(resource)
        
        # Owner can delete their projects
        if context.owner_id and hasattr(user, 'id') and user.id == context.owner_id:
            return AuthorizationResult(
                allowed=True,
                reason="Project owner can delete",
                policy=self.name
            )
        
        # Manager role can delete projects
        if self._has_role_at_least(user, 'manager'):
            # Additional check: don't allow deleting projects with active tasks (future)
            return AuthorizationResult(
                allowed=True,
                reason="Manager role grants delete permission",
                policy=self.name
            )
        
        return AuthorizationResult(
            allowed=False,
            reason="Manager role or ownership required to delete projects",
            policy=self.name
        )
    
    def can_manage(self, user: Any) -> AuthorizationResult:
        """
        Check if user has full management access.
        
        Override: Only admins and managers can manage.
        
        Args:
            user: User requesting access
            
        Returns:
            AuthorizationResult with allowed/reason
        """
        if not user or not user.is_authenticated:
            return AuthorizationResult(
                allowed=False,
                reason="Authentication required",
                policy=self.name
            )
        
        if user.is_superuser or self._has_role_at_least(user, 'admin'):
            return AuthorizationResult(
                allowed=True,
                reason="Administrator has full management access",
                policy=self.name
            )
        
        if self._has_role_at_least(user, 'manager'):
            return AuthorizationResult(
                allowed=True,
                reason="Manager has management access",
                policy=self.name
            )
        
        return AuthorizationResult(
            allowed=False,
            reason="Manager role required for management access",
            policy=self.name
        )


# =============================================================================
# Policy Factory
# =============================================================================

_project_policy: Optional[ProjectPolicy] = None


def get_project_policy() -> ProjectPolicy:
    """
    Get the singleton ProjectPolicy instance.
    
    Returns:
        ProjectPolicy instance
    """
    global _project_policy
    if _project_policy is None:
        _project_policy = ProjectPolicy()
    return _project_policy


# For backward compatibility
def ProjectPolicy() -> ProjectPolicy:
    """Get ProjectPolicy instance (factory function)."""
    return get_project_policy()

