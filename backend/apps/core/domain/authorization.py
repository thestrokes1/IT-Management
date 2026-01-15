"""
Domain authorization service for IT Management Platform.

Pure domain layer authorization without Django dependencies.
Reusable by Tickets, Assets, Projects, Users applications.
"""

from apps.core.domain.roles import has_higher_role, has_strictly_higher_role, is_superadmin_or_manager


class AuthorizationError(Exception):
    """
    Exception raised when an actor is not authorized to perform an action.
    
    This is a domain exception that should be caught and handled
    at the application or presentation layer.
    """
    pass


def can_modify_resource(actor, resource_owner) -> bool:
    """
    Check if an actor can modify a resource owned by another user.
    
    Authorization rules:
    1. Allow if actor.role is SUPERADMIN or MANAGER (highest privilege)
    2. Allow if actor == resource_owner (user modifying their own resource)
    3. Allow if actor.role rank > resource_owner.role rank (hierarchy)
    4. Deny otherwise
    
    Args:
        actor: User instance attempting the action
        resource_owner: User instance who owns the resource
        
    Returns:
        bool: True if actor is authorized to modify the resource
        
    Examples:
        >>> # SUPERADMIN can modify any resource
        >>> can_modify_resource(superadmin_user, regular_user)
        True
        
        >>> # User can modify their own resource
        >>> can_modify_resource(john, john)
        True
        
        >>> # Higher rank can modify lower rank
        >>> can_modify_resource(manager, technician)
        True
        
        >>> # Same rank cannot modify
        >>> can_modify_resource(manager_a, manager_b)
        False
        
        >>> # Lower rank cannot modify higher rank
        >>> can_modify_resource(technician, manager)
        False
    """
    # Rule 1: SUPERADMIN or MANAGER can modify any resource
    if is_superadmin_or_manager(actor.role):
        return True
    
    # Rule 2: Actor can modify their own resource
    if actor == resource_owner:
        return True
    
    # Rule 3: Higher role rank can modify lower role rank (strictly higher)
    if has_strictly_higher_role(actor.role, resource_owner.role):
        return True
    
    # Deny otherwise
    return False


def can_delete_resource(actor, resource_owner) -> bool:
    """
    Check if an actor can delete a resource owned by another user.
    
    Deletion has stricter rules - only SUPERADMIN or MANAGER can
    delete resources owned by other users.
    
    Args:
        actor: User instance attempting the action
        resource_owner: User instance who owns the resource
        
    Returns:
        bool: True if actor is authorized to delete the resource
    """
    # Only SUPERADMIN or MANAGER can delete others' resources
    if is_superadmin_or_manager(actor.role):
        return True
    
    # Users can delete their own resources
    if actor == resource_owner:
        return True
    
    return False


def can_view_resource(actor, resource_owner) -> bool:
    """
    Check if an actor can view a resource owned by another user.
    
    View permissions are more permissive - actors with higher or
    equal rank can view, and users can always view their own resources.
    
    Args:
        actor: User instance attempting the action
        resource_owner: User instance who owns the resource
        
    Returns:
        bool: True if actor is authorized to view the resource
    """
    # SUPERADMIN or MANAGER can view any resource
    if is_superadmin_or_manager(actor.role):
        return True
    
    # Actor can always view their own resource
    if actor == resource_owner:
        return True
    
    # Higher or equal rank can view
    actor_rank = _get_role_rank(actor.role)
    owner_rank = _get_role_rank(resource_owner.role)
    
    return actor_rank >= owner_rank


def assert_can_modify(actor, resource_owner) -> None:
    """
    Assert that an actor can modify a resource.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_modify_resource(actor, resource_owner):
        raise AuthorizationError(
            f"User '{actor.username}' is not authorized to modify "
            f"resource owned by '{resource_owner.username}'"
        )


def assert_can_delete(actor, resource_owner) -> None:
    """
    Assert that an actor can delete a resource.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_delete_resource(actor, resource_owner):
        raise AuthorizationError(
            f"User '{actor.username}' is not authorized to delete "
            f"resource owned by '{resource_owner.username}'"
        )


def _get_role_rank(role: str) -> int:
    """
    Get numeric rank for a role.
    
    Args:
        role: Role name string
        
    Returns:
        int: Numeric rank (higher = more privileges)
    """
    # Inline implementation to avoid circular imports
    ranks = {
        'VIEWER': 1,
        'TECHNICIAN': 2,
        'IT_ADMIN': 3,
        'MANAGER': 4,
        'SUPERADMIN': 4,
    }
    return ranks.get(role, 0)

