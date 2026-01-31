"""
Asset authorization domain service.

Pure domain layer authorization for asset management.
No Django dependencies.

IMPORTANT: For TECHNICIAN role, ownership is determined by assigned_to,
NOT created_by. Technicians can only edit/delete assets assigned to them.

Role Hierarchy (highest to lowest):
    - SUPERADMIN (rank 4) - Full access, no restrictions
    - MANAGER (rank 4) - Same as SUPERADMIN
    - IT_ADMIN (rank 3) - Full asset access, cannot manage projects/users
    - TECHNICIAN (rank 2) - Can only manage assets assigned to them
    - VIEWER (rank 1) - Read-only, no asset access
"""

from apps.core.domain.roles import (
    has_higher_role,
    has_strictly_higher_role,
    is_superadmin_or_manager,
    is_admin_role,
)
from apps.core.domain.authorization import AuthorizationError


# Role constants
_ROLE_IT_ADMIN = 'IT_ADMIN'
_ROLE_TECHNICIAN = 'TECHNICIAN'
_ROLE_VIEWER = 'VIEWER'


# =============================================================================
# VIEW PERMISSIONS
# =============================================================================

def can_view(user, asset) -> bool:
    """
    Check if user can view an asset.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full asset access)
    - TECHNICIAN: always allowed (can view any asset)
    - VIEWER: NOT allowed - VIEWER has no asset access
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can view the asset
    """
    # VIEWER has no asset access
    if user.role == _ROLE_VIEWER:
        return False
    
    # All other roles can view assets
    return True


def can_view_list(user) -> bool:
    """
    Check if user can view the asset list.
    
    Rules:
    - VIEWER: NOT allowed
    - All other authenticated roles: allowed
    
    Args:
        user: User instance
        
    Returns:
        bool: True if user can view asset list
    """
    return user.role != _ROLE_VIEWER


def can_view_details(user, asset) -> bool:
    """
    Check if user can view asset details.
    
    Same as can_view - returns HTTP 403 for VIEWER.
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can view asset details
    """
    return can_view(user, asset)


def can_view_logs(user, asset) -> bool:
    """
    Check if user can view asset logs/history.
    
    Rules:
    - IT_ADMIN and above: always allowed
    - TECHNICIAN: NOT allowed
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can view asset logs
    """
    # IT_ADMIN and above can view logs
    return has_higher_role(user.role, _ROLE_IT_ADMIN)


# =============================================================================
# CREATE PERMISSIONS
# =============================================================================

def can_create(user) -> bool:
    """
    Check if user can create assets.
    
    Rules:
    - VIEWER: NOT allowed
    - TECHNICIAN and above: allowed
    
    Args:
        user: User instance
        
    Returns:
        bool: True if user can create assets
    """
    return user.role != _ROLE_VIEWER


# =============================================================================
# EDIT PERMISSIONS
# =============================================================================

def can_edit(user, asset) -> bool:
    """
    Check if user can edit an asset.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full asset access)
    - TECHNICIAN: allowed ONLY if asset.assigned_to == user
    - VIEWER: NOT allowed
    
    IMPORTANT: Technician ownership is determined by assigned_to,
    NOT created_by.
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can edit the asset
    """
    # VIEWER cannot edit
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN has full asset access
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: can only edit if assigned to them
    if user.role == _ROLE_TECHNICIAN:
        return asset.assigned_to_id == user.id
    
    return False


def can_update(user, asset) -> bool:
    """
    Alias for can_edit - check if user can update an asset.
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can update the asset
    """
    return can_edit(user, asset)


def can_modify(user, asset) -> bool:
    """
    Alias for can_edit - check if user can modify an asset.
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can modify the asset
    """
    return can_edit(user, asset)


# =============================================================================
# DELETE PERMISSIONS
# =============================================================================

def can_delete(user, asset) -> bool:
    """
    Check if user can delete an asset.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full asset access)
    - TECHNICIAN: allowed ONLY if asset.assigned_to == user
    - VIEWER: NOT allowed
    
    IMPORTANT: Technician ownership is determined by assigned_to,
    NOT created_by.
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can delete the asset
    """
    # VIEWER cannot delete
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN has full asset access
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: can only delete if assigned to them
    if user.role == _ROLE_TECHNICIAN:
        return asset.assigned_to_id == user.id
    
    return False


# =============================================================================
# ASSIGN / UNASSIGN PERMISSIONS
# =============================================================================

def can_assign(user, asset, assignee) -> bool:
    """
    Check if user can assign an asset to a user.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full asset access)
    - TECHNICIAN: NEVER allowed (cannot assign to others)
    - VIEWER: NOT allowed
    
    Args:
        user: User instance attempting to assign
        asset: Asset instance being assigned
        assignee: User instance to assign the asset to
        
    Returns:
        bool: True if user can assign the asset
    """
    # VIEWER cannot assign
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN has full asset access
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: NEVER can assign to others
    return False


def can_unassign(user, asset) -> bool:
    """
    Check if user can unassign an asset.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full asset access)
    - TECHNICIAN: allowed ONLY if asset.assigned_to == user
    - VIEWER: NOT allowed
    
    Args:
        user: User instance attempting to unassign
        asset: Asset instance
        
    Returns:
        bool: True if user can unassign the asset
    """
    # VIEWER cannot unassign
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN has full asset access
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: can only unassign if assigned to them
    if user.role == _ROLE_TECHNICIAN:
        return asset.assigned_to_id == user.id
    
    return False


def can_self_assign(user, asset) -> bool:
    """
    Check if user can self-assign an asset.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full asset access)
    - TECHNICIAN: allowed ONLY if asset.assigned_to == user
      (technician can claim unassigned asset)
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can self-assign the asset
    """
    # VIEWER cannot self-assign
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER can always self-assign
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN can always self-assign
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: can only self-assign if unassigned
    if user.role == _ROLE_TECHNICIAN:
        return asset.assigned_to_id is None
    
    return False


def can_unassign_self(user, asset) -> bool:
    """
    Check if user can unassign themselves from an asset.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: allowed ONLY if asset.assigned_to == user
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can unassign themselves from the asset
    """
    # VIEWER cannot unassign
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER can always unassign
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN can always unassign
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: can only unassign if assigned to them
    if user.role == _ROLE_TECHNICIAN:
        return asset.assigned_to_id == user.id
    
    return False


def can_assign_to_self(user, asset) -> bool:
    """
    Check if user can assign the asset to themselves.
    
    Used by the UI self-assign action. Delegates to can_self_assign
    for consistent authorization logic.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full asset access)
    - TECHNICIAN: allowed ONLY if asset is unassigned
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can self-assign the asset
    """
    return can_self_assign(user, asset)


def can_reassign(user, asset) -> bool:
    """
    Check if user can reassign an asset to another user.
    
    Same as can_assign - TECHNICIAN cannot reassign.
    
    Args:
        user: User instance attempting to reassign
        asset: Asset instance
        
    Returns:
        bool: True if user can reassign the asset
    """
    # TECHNICIAN cannot reassign
    if user.role == _ROLE_TECHNICIAN:
        return False
    
    # Other roles can reassign (checked by can_assign)
    return can_assign(user, asset, None)


# =============================================================================
# MAINTENANCE PERMISSIONS
# =============================================================================

def can_add_maintenance(user, asset) -> bool:
    """
    Check if user can add maintenance records.
    
    Rules:
    - VIEWER: NOT allowed
    - TECHNICIAN: only if asset.assigned_to == user
    - IT_ADMIN and above: allowed
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can add maintenance records
    """
    # VIEWER cannot add maintenance
    if user.role == _ROLE_VIEWER:
        return False
    
    # TECHNICIAN: can only add if assigned
    if user.role == _ROLE_TECHNICIAN:
        return asset.assigned_to_id == user.id
    
    # Other roles can add maintenance
    return True


def can_view_maintenance(user, asset) -> bool:
    """
    Check if user can view maintenance records.
    
    Rules:
    - VIEWER: NOT allowed
    - TECHNICIAN: only if asset.assigned_to == user
    - IT_ADMIN and above: allowed
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        bool: True if user can view maintenance records
    """
    # VIEWER cannot view maintenance
    if user.role == _ROLE_VIEWER:
        return False
    
    # TECHNICIAN: can only view if assigned
    if user.role == _ROLE_TECHNICIAN:
        return asset.assigned_to_id == user.id
    
    # Other roles can view maintenance
    return True


# =============================================================================
# PERMISSION AGGREGATION
# =============================================================================

def get_permissions(user, asset) -> dict:
    """
    Get all permissions for a user on a specific asset.
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        dict: Dictionary with permission keys and boolean values
    """
    return {
        'can_view': can_view(user, asset),
        'can_edit': can_edit(user, asset),
        'can_delete': can_delete(user, asset),
        'can_assign': can_assign(user, asset, None),
        'can_unassign': can_unassign(user, asset),
        'can_self_assign': can_self_assign(user, asset),
        'can_unassign_self': can_unassign_self(user, asset),
        'can_view_logs': can_view_logs(user, asset),
        'can_add_maintenance': can_add_maintenance(user, asset),
        'can_view_maintenance': can_view_maintenance(user, asset),
    }


def get_list_permissions(user) -> dict:
    """
    Get all list-level permissions for a user.
    
    Args:
        user: User instance
        
    Returns:
        dict: Dictionary with permission keys and boolean values
    """
    return {
        'can_view_list': can_view_list(user),
        'can_create': can_create(user),
    }


# =============================================================================
# ASSERTION HELPERS (Raise AuthorizationError)
# =============================================================================

def assert_can_view(user, asset) -> None:
    """
    Assert that user can view the asset.
    
    Raises:
        AuthorizationError: If user cannot view the asset
    """
    if not can_view(user, asset):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to view asset"
        )


def assert_can_create(user) -> None:
    """
    Assert that user can create assets.
    
    Raises:
        AuthorizationError: If user cannot create assets
    """
    if not can_create(user):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to create assets"
        )


def assert_can_edit(user, asset) -> None:
    """
    Assert that user can edit the asset.
    
    Raises:
        AuthorizationError: If user cannot edit the asset
    """
    if not can_edit(user, asset):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to edit asset"
        )


def assert_can_delete(user, asset) -> None:
    """
    Assert that user can delete the asset.
    
    Raises:
        AuthorizationError: If user cannot delete the asset
    """
    if not can_delete(user, asset):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to delete asset"
        )


def assert_can_assign(user, asset, assignee) -> None:
    """
    Assert that user can assign the asset.
    
    Raises:
        AuthorizationError: If user cannot assign the asset
    """
    if not can_assign(user, asset, assignee):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to assign asset"
        )


def assert_can_unassign(user, asset) -> None:
    """
    Assert that user can unassign the asset.
    
    Raises:
        AuthorizationError: If user cannot unassign the asset
    """
    if not can_unassign(user, asset):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to unassign asset"
        )


def assert_can_self_assign(user, asset) -> None:
    """
    Assert that user can self-assign the asset.
    
    Raises:
        AuthorizationError: If user cannot self-assign the asset
    """
    if not can_self_assign(user, asset):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to self-assign asset"
        )


# =============================================================================
# LEGACY ALIASES (for backward compatibility)
# =============================================================================

def can_read_asset(user, asset) -> bool:
    """Alias for can_view."""
    return can_view(user, asset)


def can_create_asset(user) -> bool:
    """Alias for can_create."""
    return can_create(user)


def can_update_asset(user, asset) -> bool:
    """Alias for can_edit."""
    return can_edit(user, asset)


def can_delete_asset(user, asset) -> bool:
    """Alias for can_delete."""
    return can_delete(user, asset)


def can_assign_asset(user, asset) -> bool:
    """Alias for can_assign."""
    return can_assign(user, asset, None)


def can_self_assign_asset(user, asset) -> bool:
    """Alias for can_self_assign."""
    return can_self_assign(user, asset)


def can_reassign_asset(user, asset) -> bool:
    """Alias for can_reassign."""
    return can_reassign(user, asset)


def can_unassign_asset(user, asset) -> bool:
    """Alias for can_unassign."""
    return can_unassign(user, asset)


def can_edit_assigned_asset(user, asset) -> bool:
    """Alias for can_edit."""
    return can_edit(user, asset)


def get_asset_permissions(user, asset) -> dict:
    """Alias for get_permissions."""
    return get_permissions(user, asset)


# Legacy assertion aliases
def assert_can_update_asset(user, asset) -> None:
    return assert_can_edit(user, asset)


def assert_can_delete_asset(user, asset) -> None:
    return assert_can_delete(user, asset)


def assert_can_assign_asset(user, asset) -> None:
    return assert_can_assign(user, asset, None)


# Additional legacy alias for backward compatibility
def can_view_asset_logs(user, asset) -> bool:
    """Alias for can_view_logs."""
    return can_view_logs(user, asset)

