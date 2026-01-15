"""
User authority service for IT Management Platform.

Pure domain layer authorization for user management.
No Django dependencies.

User Management Permissions:
    - Viewing: MANAGER+ can view any user, users can view own profile
    - Updating: Role-based hierarchy controls profile updates
    - Role Changes: Cannot assign roles >= own role, cannot change own role
    - Deactivation: SUPERADMIN > MANAGER > IT_ADMIN hierarchy
    - Deletion: SUPERADMIN only (cannot delete self)
"""

from apps.core.domain.roles import (
    has_higher_role,
    has_strictly_higher_role,
    get_role_rank,
    is_superadmin_or_manager,
)
from apps.core.domain.authorization import AuthorizationError


def can_view_user(actor, target) -> bool:
    """
    Check if actor can view target's user profile.
    
    Args:
        actor: User instance attempting the action
        target: User instance whose profile is being viewed
        
    Returns:
        bool: True if actor is authorized to view target's profile
        
    Examples:
        >>> # MANAGER can view any user
        >>> can_view_user(manager, regular_user)
        True
        
        >>> # Users can view their own profile
        >>> can_view_user(john, john)
        True
        
        >>> # Same-rank users can view each other
        >>> can_view_user(tech1, tech2)
        True
    """
    # Actor can always view their own profile
    if actor == target:
        return True
    
    # SUPERADMIN and MANAGER can view any user
    if is_superadmin_or_manager(actor.role):
        return True
    
    # IT_ADMIN and below can view any user (read access is permissive)
    return True


def can_update_user(actor, target) -> bool:
    """
    Check if actor can update target's user profile (excluding role).
    
    Authorization rules:
    1. SUPERADMIN can update any user
    2. MANAGER can update any user except SUPERADMIN
    3. IT_ADMIN can update TECHNICIAN or VIEWER only
    4. TECHNICIAN and VIEWER can only update their own profile
    
    Args:
        actor: User instance attempting the action
        target: User instance whose profile is being updated
        
    Returns:
        bool: True if actor is authorized to update target's profile
    """
    # Users can update their own profile
    if actor == target:
        return True
    
    # SUPERADMIN can update any user
    if actor.role == 'SUPERADMIN':
        return True
    
    # MANAGER can update any user except SUPERADMIN
    if actor.role == 'MANAGER' and target.role != 'SUPERADMIN':
        return True
    
    # IT_ADMIN can update TECHNICIAN or VIEWER only
    if actor.role == 'IT_ADMIN' and target.role in ('TECHNICIAN', 'VIEWER'):
        return True
    
    return False


def can_change_role(actor, target, new_role) -> bool:
    """
    Check if actor can change target's role to new_role.
    
    Authorization rules:
    1. Cannot change own role
    2. Cannot assign a role >= actor's role (prevents privilege escalation)
       - Exception: SUPERADMIN can assign MANAGER role (equal rank, but SUPERADMIN is top-level)
    3. SUPERADMIN can assign any role
    4. MANAGER can assign IT_ADMIN, TECHNICIAN, or VIEWER
    5. IT_ADMIN can assign TECHNICIAN or VIEWER only
    
    Args:
        actor: User instance attempting the action
        target: User instance whose role is being changed
        new_role: The role to assign to target
        
    Returns:
        bool: True if actor is authorized to change target's role
    """
    # Cannot change own role
    if actor == target:
        return False
    
    # Cannot assign a role >= actor's role (prevents privilege escalation)
    # Exception: SUPERADMIN can assign MANAGER (equal rank, but SUPERADMIN is top-level admin)
    actor_rank = get_role_rank(actor.role)
    new_role_rank = get_role_rank(new_role)
    
    if new_role_rank > actor_rank:
        return False
    
    # Handle equal rank case: only SUPERADMIN can assign MANAGER role
    if new_role_rank == actor_rank:
        return actor.role == 'SUPERADMIN' and new_role == 'MANAGER'
    
    # SUPERADMIN can assign any role (already covered by rank check above)
    if actor.role == 'SUPERADMIN':
        return True
    
    # MANAGER can assign IT_ADMIN, TECHNICIAN, or VIEWER
    if actor.role == 'MANAGER' and new_role in ('IT_ADMIN', 'TECHNICIAN', 'VIEWER'):
        return True
    
    # IT_ADMIN can assign TECHNICIAN or VIEWER only
    if actor.role == 'IT_ADMIN' and new_role in ('TECHNICIAN', 'VIEWER'):
        return True
    
    return False


def can_deactivate_user(actor, target) -> bool:
    """
    Check if actor can deactivate target's account.
    
    Authorization rules:
    1. Cannot deactivate self
    2. SUPERADMIN can deactivate any user except self
    3. MANAGER can deactivate IT_ADMIN and below
    4. IT_ADMIN can deactivate TECHNICIAN or VIEWER only
    
    Args:
        actor: User instance attempting the action
        target: User instance being deactivated
        
    Returns:
        bool: True if actor is authorized to deactivate target
    """
    # Cannot deactivate self
    if actor == target:
        return False
    
    # SUPERADMIN can deactivate any user except self
    if actor.role == 'SUPERADMIN':
        return True
    
    # MANAGER can deactivate IT_ADMIN and below (cannot deactivate SUPERADMIN)
    if actor.role == 'MANAGER' and target.role != 'SUPERADMIN':
        return True
    
    # IT_ADMIN can deactivate TECHNICIAN or VIEWER only
    if actor.role == 'IT_ADMIN' and target.role in ('TECHNICIAN', 'VIEWER'):
        return True
    
    return False


def can_delete_user(actor, target) -> bool:
    """
    Check if actor can delete target's account.
    
    Authorization rules:
    1. Cannot delete self
    2. Only SUPERADMIN can delete other users
    
    Deletion is restricted to SUPERADMIN for safety.
    
    Args:
        actor: User instance attempting the action
        target: User instance being deleted
        
    Returns:
        bool: True if actor is authorized to delete target
    """
    # Cannot delete self
    if actor == target:
        return False
    
    # Only SUPERADMIN can delete other users
    return actor.role == 'SUPERADMIN'


def get_user_permissions(actor, target) -> dict:
    """
    Get comprehensive permission set for actor on target user.
    
    Args:
        actor: User instance attempting actions
        target: User instance being accessed
        
    Returns:
        dict: Permission flags for all user management actions
    """
    return {
        'can_view': can_view_user(actor, target),
        'can_update': can_update_user(actor, target),
        'can_change_role': can_change_role(actor, target, target.role),
        'can_deactivate': can_deactivate_user(actor, target),
        'can_delete': can_delete_user(actor, target),
    }


# =============================================================================
# Assertion helpers that raise AuthorizationError
# =============================================================================

def can_create_user(actor) -> bool:
    """
    Check if actor can create new users.
    
    Authorization rules:
    - Any authenticated user can create users (self-registration)
    - This is typically used for initial sign-up
    
    Args:
        actor: User instance attempting to create a new user
        
    Returns:
        bool: True (any authenticated user can create accounts)
    """
    # Any authenticated user can create users (self-registration)
    return True


def assert_can_create_user(actor) -> None:
    """
    Assert that actor can create new users.
    
    Since user creation is open for self-registration, this always passes.
    
    Raises:
        AuthorizationError: Never raised for user creation
    """
    # User creation is open for self-registration
    pass


def assert_can_update_user(actor, target) -> None:
    """
    Assert that actor can update target's user profile.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_update_user(actor, target):
        raise AuthorizationError(
            f"User '{actor.username}' is not authorized to update "
            f"profile of user '{target.username}'"
        )


def assert_can_change_role(actor, target, new_role) -> None:
    """
    Assert that actor can change target's role to new_role.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_change_role(actor, target, new_role):
        raise AuthorizationError(
            f"User '{actor.username}' is not authorized to change "
            f"role of user '{target.username}' to '{new_role}'"
        )


def assert_can_deactivate_user(actor, target) -> None:
    """
    Assert that actor can deactivate target's account.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_deactivate_user(actor, target):
        raise AuthorizationError(
            f"User '{actor.username}' is not authorized to deactivate "
            f"account of user '{target.username}'"
        )


def assert_can_delete_user(actor, target) -> None:
    """
    Assert that actor can delete target's account.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_delete_user(actor, target):
        raise AuthorizationError(
            f"User '{actor.username}' is not authorized to delete "
            f"account of user '{target.username}'"
        )

