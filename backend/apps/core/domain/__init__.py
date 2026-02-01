"""
Core domain utilities.

Contains pure domain logic without Django dependencies.
"""

from apps.core.domain.roles import (
    ROLE_RANKS,
    VALID_ROLES,
    ROLE_HIERARCHY,
    get_role_rank,
    has_higher_role,
    has_strictly_higher_role,
    is_admin_role,
    is_superadmin_or_manager,
    is_lowest_role,
    compare_roles,
    get_role_display_name,
)

from apps.core.domain.authorization import (
    AuthorizationError,
    can_modify_resource,
    can_delete_resource,
    can_view_resource,
    assert_can_modify,
    assert_can_delete,
)

from apps.core.domain.authority_base import (
    is_admin_override,
    is_owner,
    can_modify_subordinate,
    can_modify_owned_or_subordinate,
)

__all__ = [
    # Roles
    'ROLE_RANKS',
    'VALID_ROLES',
    'ROLE_HIERARCHY',
    'get_role_rank',
    'has_higher_role',
    'has_strictly_higher_role',
    'is_admin_role',
    'is_superadmin_or_manager',
    'is_lowest_role',
    'compare_roles',
    'get_role_display_name',
    # Authorization
    'AuthorizationError',
    'can_modify_resource',
    'can_delete_resource',
    'can_view_resource',
    'assert_can_modify',
    'assert_can_delete',
    # Authority Base
    'is_admin_override',
    'is_owner',
    'can_modify_subordinate',
    'can_modify_owned_or_subordinate',
]

