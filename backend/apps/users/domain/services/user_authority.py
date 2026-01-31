"""
User authority service for IT Management Platform.

Pure domain layer authorization for user management.
No Django dependencies.

IMPORTANT: IT_ADMIN can only edit TECHNICIAN users.
Cannot edit MANAGER, IT_ADMIN, or SUPERADMIN users.

Role Hierarchy (highest to lowest):
    - SUPERADMIN (rank 4) - Full user management access
    - MANAGER (rank 4) - Same as SUPERADMIN
    - IT_ADMIN (rank 3) - Can only edit TECHNICIAN users
    - TECHNICIAN (rank 2) - Can only edit own profile
    - VIEWER (rank 1) - Read-only, can view own profile only
"""

from apps.core.domain.roles import (
    has_higher_role,
    has_strictly_higher_role,
    get_role_rank,
    is_superadmin_or_manager,
)
from apps.core.domain.authorization import AuthorizationError


# Role constants
_ROLE_SUPERADMIN = 'SUPERADMIN'
_ROLE_MANAGER = 'MANAGER'
_ROLE_IT_ADMIN = 'IT_ADMIN'
_ROLE_TECHNICIAN = 'TECHNICIAN'
_ROLE_VIEWER = 'VIEWER'


# =============================================================================
# VIEW PERMISSIONS
# =============================================================================

def can_view(actor, target) -> bool:
    """
    Check if actor can view target's user profile.
    
    Rules:
    - SUPERADMIN, MANAGER: can view any user
    - IT_ADMIN: can view any user (read access is permissive)
    - TECHNICIAN: can view any user
    - VIEWER: can ONLY view their own profile
    
    Args:
        actor: User instance attempting the action
        target: User instance whose profile is being viewed
        
    Returns:
        bool: True if actor is authorized to view target's profile
    """
    # Actor can always view their own profile
    if actor == target:
        return True
    
    # VIEWER can only view their own profile
    if actor.role == _ROLE_VIEWER:
        return False
    
    # All other roles can view any user
    return True


def can_view_list(actor) -> bool:
    """
    Check if actor can view the user list.
    
    Rules:
    - VIEWER: NOT allowed
    - All other roles: allowed
    
    Args:
        actor: User instance
        
    Returns:
        bool: True if actor can view user list
    """
    return actor.role != _ROLE_VIEWER


def can_view_details(actor, target) -> bool:
    """
    Check if actor can view target's user details.
    
    Same as can_view.
    
    Args:
        actor: User instance
        target: User instance
        
    Returns:
        bool: True if actor can view target's details
    """
    return can_view(actor, target)


# =============================================================================
# CREATE PERMISSIONS
# =============================================================================

def can_create(actor) -> bool:
    """
    Check if actor can create new users.
    
    Rules:
    - Any authenticated user can create users (self-registration)
    - This is typically used for initial sign-up
    
    Args:
        actor: User instance attempting to create a new user
        
    Returns:
        bool: True (any authenticated user can create accounts)
    """
    return True


# =============================================================================
# EDIT / UPDATE PERMISSIONS
# =============================================================================

def can_edit(actor, target) -> bool:
    """
    Check if actor can update target's user profile (excluding role).
    
    Rules:
    - SUPERADMIN: can update any user
    - MANAGER: can update any user except SUPERADMIN
    - IT_ADMIN: can ONLY update TECHNICIAN users (not MANAGER, IT_ADMIN, SUPERADMIN)
    - TECHNICIAN: can only update their own profile
    - VIEWER: cannot update any user profile
    
    Args:
        actor: User instance attempting the action
        target: User instance whose profile is being updated
        
    Returns:
        bool: True if actor is authorized to update target's profile
    """
    # Users can update their own profile
    if actor == target:
        return True
    
    # VIEWER cannot update any profile
    if actor.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN can update any user
    if actor.role == _ROLE_SUPERADMIN:
        return True
    
    # MANAGER can update any user except SUPERADMIN
    if actor.role == _ROLE_MANAGER and target.role != _ROLE_SUPERADMIN:
        return True
    
    # IT_ADMIN can ONLY update TECHNICIAN users
    if actor.role == _ROLE_IT_ADMIN and target.role == _ROLE_TECHNICIAN:
        return True
    
    return False


def can_update(actor, target) -> bool:
    """
    Alias for can_edit.
    
    Args:
        actor: User instance
        target: User instance
        
    Returns:
        bool: True if actor can update target
    """
    return can_edit(actor, target)


# =============================================================================
# ROLE CHANGE PERMISSIONS
# =============================================================================

def can_change_role(actor, target, new_role) -> bool:
    """
    Check if actor can change target's role to new_role.
    
    Rules:
    - Cannot change own role
    - Cannot assign a role >= actor's role (prevents privilege escalation)
      Exception: SUPERADMIN can assign MANAGER role (equal rank)
    - SUPERADMIN can assign any role
    - MANAGER can assign IT_ADMIN, TECHNICIAN, or VIEWER
    - IT_ADMIN can assign TECHNICIAN or VIEWER only
    - TECHNICIAN, VIEWER: cannot change any role
    
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
    
    # TECHNICIAN and VIEWER cannot change roles
    if actor.role in (_ROLE_TECHNICIAN, _ROLE_VIEWER):
        return False
    
    # Cannot assign a role >= actor's role (prevents privilege escalation)
    actor_rank = get_role_rank(actor.role)
    new_role_rank = get_role_rank(new_role)
    
    if new_role_rank > actor_rank:
        return False
    
    # Handle equal rank case: only SUPERADMIN can assign MANAGER role
    if new_role_rank == actor_rank:
        return actor.role == _ROLE_SUPERADMIN and new_role == _ROLE_MANAGER
    
    # SUPERADMIN can assign any role (already covered by rank check above)
    if actor.role == _ROLE_SUPERADMIN:
        return True
    
    # MANAGER can assign IT_ADMIN, TECHNICIAN, or VIEWER
    if actor.role == _ROLE_MANAGER and new_role in (_ROLE_IT_ADMIN, _ROLE_TECHNICIAN, _ROLE_VIEWER):
        return True
    
    # IT_ADMIN can assign TECHNICIAN or VIEWER only
    if actor.role == _ROLE_IT_ADMIN and new_role in (_ROLE_TECHNICIAN, _ROLE_VIEWER):
        return True
    
    return False


# =============================================================================
# DEACTIVATE / ACTIVATE PERMISSIONS
# =============================================================================

def can_deactivate(actor, target) -> bool:
    """
    Check if actor can deactivate target's account.
    
    Rules:
    - Cannot deactivate self
    - SUPERADMIN can deactivate any user except self
    - MANAGER can deactivate IT_ADMIN and below (cannot deactivate SUPERADMIN)
    - IT_ADMIN can deactivate TECHNICIAN or VIEWER only
    - TECHNICIAN, VIEWER: cannot deactivate any user
    
    Args:
        actor: User instance attempting the action
        target: User instance being deactivated
        
    Returns:
        bool: True if actor is authorized to deactivate target
    """
    # Cannot deactivate self
    if actor == target:
        return False
    
    # TECHNICIAN and VIEWER cannot deactivate
    if actor.role in (_ROLE_TECHNICIAN, _ROLE_VIEWER):
        return False
    
    # SUPERADMIN can deactivate any user except self
    if actor.role == _ROLE_SUPERADMIN:
        return True
    
    # MANAGER can deactivate IT_ADMIN and below (cannot deactivate SUPERADMIN)
    if actor.role == _ROLE_MANAGER and target.role != _ROLE_SUPERADMIN:
        return True
    
    # IT_ADMIN can deactivate TECHNICIAN or VIEWER only
    if actor.role == _ROLE_IT_ADMIN and target.role in (_ROLE_TECHNICIAN, _ROLE_VIEWER):
        return True
    
    return False


def can_activate(actor, target) -> bool:
    """
    Check if actor can activate target's account.
    
    Same rules as can_deactivate.
    
    Args:
        actor: User instance
        target: User instance
        
    Returns:
        bool: True if actor can activate target
    """
    return can_deactivate(actor, target)


# =============================================================================
# DELETE PERMISSIONS
# =============================================================================

def can_delete(actor, target) -> bool:
    """
    Check if actor can delete target's account.
    
    Rules:
    - Cannot delete self
    - Only SUPERADMIN can delete other users
    - All other roles cannot delete users
    
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
    return actor.role == _ROLE_SUPERADMIN


# =============================================================================
# PERMISSION AGGREGATION
# =============================================================================

def get_permissions(actor, target) -> dict:
    """
    Get comprehensive permission set for actor on target user.
    
    Args:
        actor: User instance attempting actions
        target: User instance being accessed
        
    Returns:
        dict: Permission flags for all user management actions
    """
    return {
        'can_view': can_view(actor, target),
        'can_edit': can_edit(actor, target),
        'can_change_role': can_change_role(actor, target, target.role),
        'can_deactivate': can_deactivate(actor, target),
        'can_activate': can_activate(actor, target),
        'can_delete': can_delete(actor, target),
    }


def get_list_permissions(actor) -> dict:
    """
    Get all list-level permissions for a user.
    
    Args:
        actor: User instance
        
    Returns:
        dict: Dictionary with permission keys and boolean values
    """
    return {
        'can_view_list': can_view_list(actor),
        'can_create': can_create(actor),
    }


# =============================================================================
# ASSERTION HELPERS (Raise AuthorizationError)
# =============================================================================

def assert_can_view(actor, target) -> None:
    """
    Assert that actor can view target's profile.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_view(actor, target):
        raise AuthorizationError(
            f"User '{actor.username}' is not authorized to view "
            f"profile of user '{target.username}'"
        )


def assert_can_create(actor) -> None:
    """
    Assert that actor can create new users.
    
    Raises:
        AuthorizationError: Never raised (user creation is open)
    """
    # User creation is open for self-registration
    pass


def assert_can_edit(actor, target) -> None:
    """
    Assert that actor can update target's profile.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_edit(actor, target):
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


def assert_can_deactivate(actor, target) -> None:
    """
    Assert that actor can deactivate target's account.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_deactivate(actor, target):
        raise AuthorizationError(
            f"User '{actor.username}' is not authorized to deactivate "
            f"account of user '{target.username}'"
        )


def assert_can_activate(actor, target) -> None:
    """
    Assert that actor can activate target's account.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_activate(actor, target):
        raise AuthorizationError(
            f"User '{actor.username}' is not authorized to activate "
            f"account of user '{target.username}'"
        )


def assert_can_delete(actor, target) -> None:
    """
    Assert that actor can delete target's account.
    
    Raises:
        AuthorizationError: If actor is not authorized
    """
    if not can_delete(actor, target):
        raise AuthorizationError(
            f"User '{actor.username}' is not authorized to delete "
            f"account of user '{target.username}'"
        )


# =============================================================================
# LEGACY ALIASES (for backward compatibility)
# =============================================================================

def can_view_user(actor, target) -> bool:
    """Alias for can_view."""
    return can_view(actor, target)


def can_update_user(actor, target) -> bool:
    """Alias for can_edit."""
    return can_edit(actor, target)


def can_change_user_role(actor, target, new_role) -> bool:
    """Alias for can_change_role."""
    return can_change_role(actor, target, new_role)


def can_deactivate_user(actor, target) -> bool:
    """Alias for can_deactivate."""
    return can_deactivate(actor, target)


def can_delete_user(actor, target) -> bool:
    """Alias for can_delete."""
    return can_delete(actor, target)


def get_user_permissions(actor, target) -> dict:
    """Alias for get_permissions."""
    return get_permissions(actor, target)


def can_create_user(actor) -> bool:
    """Alias for can_create."""
    return can_create(actor)


# Legacy assertion aliases
def assert_can_update_user(actor, target) -> None:
    return assert_can_edit(actor, target)


def assert_can_change_role(actor, target, new_role) -> None:
    return assert_can_change_role(actor, target, new_role)


def assert_can_deactivate_user(actor, target) -> None:
    return assert_can_deactivate(actor, target)


def assert_can_delete_user(actor, target) -> None:
    return assert_can_delete(actor, target)


def assert_can_create_user(actor) -> None:
    # User creation is open for self-registration
    pass

