"""
User domain package for IT Management Platform.

Pure domain layer authorization for user management.
No Django dependencies.
"""

from apps.users.domain.services import (
    can_view_user,
    can_update_user,
    can_change_role,
    can_deactivate_user,
    can_delete_user,
    get_user_permissions,
    assert_can_update_user,
    assert_can_change_role,
    assert_can_deactivate_user,
    assert_can_delete_user,
)

__all__ = [
    'can_view_user',
    'can_update_user',
    'can_change_role',
    'can_deactivate_user',
    'can_delete_user',
    'get_user_permissions',
    'assert_can_update_user',
    'assert_can_change_role',
    'assert_can_deactivate_user',
    'assert_can_delete_user',
]

