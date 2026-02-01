"""
Assets domain services.

Pure domain layer authorization for asset management.
No Django dependencies.
"""

from apps.assets.domain.services.asset_authority import (
    can_create_asset,
    can_read_asset,
    can_update_asset,
    can_delete_asset,
    can_assign_asset,
    can_view_asset_logs,
    assert_can_update_asset,
    assert_can_delete_asset,
    assert_can_assign_asset,
    get_asset_permissions,
)

__all__ = [
    'can_create_asset',
    'can_read_asset',
    'can_update_asset',
    'can_delete_asset',
    'can_assign_asset',
    'can_view_asset_logs',
    'assert_can_update_asset',
    'assert_can_delete_asset',
    'assert_can_assign_asset',
    'get_asset_permissions',
]

