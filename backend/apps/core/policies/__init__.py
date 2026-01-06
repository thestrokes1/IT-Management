# Policies module.
# Contains authorization policies for domain entities.
# Policies represent authorization rules and belong in the core/domain layer.
# Following Clean Architecture: policies are independent of presentation/infra.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


# =============================================================================
# Authorization Result
# =============================================================================

@dataclass
class AuthorizationResult:
    """
    Result of an authorization check.
    
    Attributes:
        allowed: Whether the action is permitted
        reason: Explanation if denied (empty if allowed)
        policy: Name of the policy that produced this result
    """
    allowed: bool
    reason: str = ""
    policy: str = "UnknownPolicy"
    
    def require(self, action: str, resource: str) -> None:
        """
        Convenience method to raise exception if not authorized.
        
        Args:
            action: Action being attempted
            resource: Resource type being accessed
            
        Raises:
            PermissionDeniedError: If authorization was denied
        """
        if not self.allowed:
            from apps.core.exceptions import PermissionDeniedError
            raise PermissionDeniedError(
                message=f"{action.capitalize()} {resource} denied: {self.reason}",
                details={'action': action, 'resource': resource, 'policy': self.policy}
            )


# =============================================================================
# Policy Base Classes
# =============================================================================

class AuthorizationPolicy(ABC):
    """
    Base class for all authorization policies.
    
    Policies encapsulate authorization rules for specific resources.
    They are independent of HTTP/framework concerns and can be tested
    in isolation.
    
    Usage:
        class ProjectPolicy(AuthorizationPolicy):
            def can_view(self, user, resource=None) -> AuthorizationResult:
                ...
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the policy name for logging/tracing."""
        pass
    
    @abstractmethod
    def can_view(
        self,
        user: Any,
        resource: Any = None
    ) -> AuthorizationResult:
        """
        Check if user can view resource.
        
        Args:
            user: The user requesting access
            resource: Optional resource instance to check
            
        Returns:
            AuthorizationResult with allowed/reason
        """
        pass
    
    @abstractmethod
    def can_create(
        self,
        user: Any,
        resource: Any = None
    ) -> AuthorizationResult:
        """
        Check if user can create resource.
        
        Args:
            user: The user requesting access
            resource: Optional resource data for context
            
        Returns:
            AuthorizationResult with allowed/reason
        """
        pass
    
    @abstractmethod
    def can_edit(
        self,
        user: Any,
        resource: Any
    ) -> AuthorizationResult:
        """
        Check if user can edit resource.
        
        Args:
            user: The user requesting access
            resource: Resource instance being edited
            
        Returns:
            AuthorizationResult with allowed/reason
        """
        pass
    
    @abstractmethod
    def can_delete(
        self,
        user: Any,
        resource: Any
    ) -> AuthorizationResult:
        """
        Check if user can delete resource.
        
        Args:
            user: The user requesting access
            resource: Resource instance being deleted
            
        Returns:
            AuthorizationResult with allowed/reason
        """
        pass
    
    def can_manage(self, user: Any) -> AuthorizationResult:
        """
        Check if user has full management access.
        
        Default implementation: same as can_delete.
        Override for more complex permission schemes.
        
        Args:
            user: The user requesting access
            
        Returns:
            AuthorizationResult with allowed/reason
        """
        # Default: users who can delete can manage
        # Override in subclasses for specific logic
        return self.can_delete(user, None)


class RoleBasedPolicy(AuthorizationPolicy):
    """
    Base class for role-based authorization policies.
    
    Provides common role-checking functionality for policies
    that use role-based access control.
    """
    
    # Default role hierarchy (higher index = more permissions)
    ROLE_HIERARCHY = {
        'viewer': 0,
        'member': 1,
        'editor': 2,
        'manager': 3,
        'admin': 4,
        'owner': 5,
    }
    
    def _get_user_role(self, user: Any) -> str:
        """
        Get the user's role for authorization.
        
        Override in subclasses to implement actual role retrieval.
        
        Args:
            user: User to get role for
            
        Returns:
            Role name string
        """
        if not user or not user.is_authenticated:
            return 'anonymous'
        
        if hasattr(user, 'role'):
            return user.role
        elif hasattr(user, 'user_type'):
            return user.user_type
        elif user.is_superuser:
            return 'admin'
        
        return 'member'
    
    def _has_role_at_least(self, user: Any, required_role: str) -> bool:
        """
        Check if user has at least the specified role.
        
        Args:
            user: User to check
            required_role: Minimum required role name
            
        Returns:
            True if user has sufficient role
        """
        user_role = self._get_user_role(user)
        user_level = self.ROLE_HIERARCHY.get(user_role, 0)
        required_level = self.ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level


# =============================================================================
# Policy Registry
# =============================================================================

class PolicyRegistry:
    """
    Registry for all authorization policies.
    
    Provides centralized policy lookup and management.
    
    Usage:
        registry = PolicyRegistry()
        registry.register('project', ProjectPolicy())
        policy = registry.get('project')
    """
    
    _instance: Optional['PolicyRegistry'] = None
    _policies: Dict[str, AuthorizationPolicy] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, name: str, policy: AuthorizationPolicy) -> None:
        """Register a policy by name."""
        self._policies[name] = policy
    
    def get(self, name: str) -> Optional[AuthorizationPolicy]:
        """Get a policy by name."""
        return self._policies.get(name)
    
    def list_policies(self) -> List[str]:
        """List all registered policy names."""
        return list(self._policies.keys())
    
    def clear(self) -> None:
        """Clear all registered policies."""
        self._policies.clear()


# =============================================================================
# Factory Function
# =============================================================================

def get_policy(policy_type: Type[AuthorizationPolicy]) -> AuthorizationPolicy:
    """
    Factory function to get a policy instance.
    
    For singleton policies, returns the same instance.
    
    Args:
        policy_type: Policy class to instantiate
        
    Returns:
        Policy instance
    """
    # Simple singleton pattern for policy classes
    if not hasattr(policy_type, '_instance'):
        policy_type._instance = policy_type()
    return policy_type._instance

