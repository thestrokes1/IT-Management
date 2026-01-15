"""
Asset authorization domain service.

Pure domain layer authorization for asset management.
No Django dependencies.

Asset ownership is determined by `created_by`,
consistent with ticket_authority where `created_by`
represents record ownership.
"""

from apps.core.domain.authority_base import (
    is_admin_override,
    is_owner,
    can_modify_subordinate,
)
from apps.core.domain.roles import has_higher_role, has_strictly_higher_role
from apps.core.domain.authorization import AuthorizationError


# Role constants
_ROLE_IT_ADMIN = 'IT_ADMIN'
_ROLE_TECHNICIAN = 'TECHNICIAN'
_ROLE_VIEWER = 'VIEWER'


def can_create_asset(user) -> bool:
    """
    Check if user can create assets.

    Rules:
    - TECHNICIAN and above can create assets

    Args:
        user: User instance

    Returns:
        bool: True if user can create assets
    """
    return has_strictly_higher_role(user.role, _ROLE_VIEWER)


def can_read_asset(user, asset) -> bool:
    """
    Check if user can read/view an asset.

    Rules:
    - All roles can read assets

    Args:
        user: User instance
        asset: Asset instance

    Returns:
        bool: True if user can view the asset
    """
    return True


def can_update_asset(user, asset) -> bool:
    """
    Check if user can update an asset.

    Rules:
    - Owner can update their own asset
    - Admin override (SUPERADMIN, MANAGER) can update any asset
    - User with strictly higher role can update

    Args:
        user: User instance attempting the action
        asset: Asset instance with created_by attribute

    Returns:
        bool: True if user can update the asset
    """
    # Admin override
    if is_admin_override(user):
        return True

    # Owner can update
    if is_owner(user, asset.created_by):
        return True

    # Strictly higher role can update
    if can_modify_subordinate(user, asset.created_by):
        return True

    return False


def can_delete_asset(user, asset) -> bool:
    """
    Check if user can delete an asset.

    Rules:
    - Admin override (SUPERADMIN, MANAGER) can delete any asset
    - User with strictly higher role can delete
    - Owner alone is NOT enough to delete

    Args:
        user: User instance attempting the action
        asset: Asset instance with created_by attribute

    Returns:
        bool: True if user can delete the asset
    """
    # Admin override
    if is_admin_override(user):
        return True

    # Strictly higher role can delete
    # Note: Owner alone is NOT enough
    return can_modify_subordinate(user, asset.created_by)


def can_assign_asset(user, asset) -> bool:
    """
    Check if user can assign/transfer an asset.

    Rules:
    - IT_ADMIN and above can assign assets

    Args:
        user: User instance attempting the action
        asset: Asset instance

    Returns:
        bool: True if user can assign the asset
    """
    return has_higher_role(user.role, _ROLE_IT_ADMIN)


def can_view_asset_logs(user, asset) -> bool:
    """
    Check if user can view asset logs/history.

    Rules:
    - IT_ADMIN and above can view asset logs

    Args:
        user: User instance
        asset: Asset instance

    Returns:
        bool: True if user can view asset logs
    """
    return has_higher_role(user.role, _ROLE_IT_ADMIN)


def get_asset_permissions(user, asset) -> dict:
    """
    Get all permissions for a user on a specific asset.

    Args:
        user: User instance
        asset: Asset instance with created_by attribute

    Returns:
        dict: Dictionary with permission keys and boolean values
    """
    return {
        'can_create': can_create_asset(user),
        'can_read': can_read_asset(user, asset),
        'can_update': can_update_asset(user, asset),
        'can_delete': can_delete_asset(user, asset),
        'can_assign': can_assign_asset(user, asset),
        'can_view_logs': can_view_asset_logs(user, asset),
    }


def assert_can_update_asset(user, asset) -> None:
    """
    Assert that user can update the asset.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_update_asset(user, asset):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to update asset"
        )


def assert_can_delete_asset(user, asset) -> None:
    """
    Assert that user can delete the asset.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_delete_asset(user, asset):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to delete asset"
        )


def assert_can_assign_asset(user, asset) -> None:
    """
    Assert that user can assign the asset.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_assign_asset(user, asset):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to assign asset"
        )

