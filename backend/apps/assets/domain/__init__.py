"""
Assets domain layer.

Pure domain logic for asset management.
"""

from apps.assets.domain.services import (
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

