"""
Shared authority base helpers for IT Management Platform.

Pure domain layer authorization helpers that can be reused across
Tickets, Assets, Projects, Users applications.

Contains pure domain logic without Django dependencies.
"""

from apps.core.domain.roles import (
    is_superadmin_or_manager,
    has_strictly_higher_role,
)


def is_admin_override(user) -> bool:
    """
    Check if user has admin override privileges.

    SUPERADMIN and MANAGER roles have full access to modify
    any resource regardless of ownership or hierarchy.

    Args:
        user: User instance to check

    Returns:
        bool: True if user.role is SUPERADMIN or MANAGER

    Examples:
        >>> is_admin_override(superadmin_user)
        True
        >>> is_admin_override(manager_user)
        True
        >>> is_admin_override(technician_user)
        False
    """
    return is_superadmin_or_manager(user.role)


def is_owner(user, resource_owner) -> bool:
    """
    Check if user is the owner of a resource via identity comparison.

    Args:
        user: User instance attempting the action
        resource_owner: User instance who owns the resource

    Returns:
        bool: True if user == resource_owner (identity comparison)

    Examples:
        >>> is_owner(john, john)
        True
        >>> is_owner(john, jane)
        False
    """
    return user == resource_owner


def can_modify_subordinate(actor, target) -> bool:
    """
    Check if actor can modify a target based on strict role hierarchy.

    Actor must have a strictly higher role rank than the target.
    Note: SUPERADMIN and MANAGER have equal rank, so neither can
    modify the other using this function.

    Args:
        actor: User instance attempting the action
        target: User instance being evaluated as subordinate

    Returns:
        bool: True only if actor has STRICTLY higher role rank

    Examples:
        >>> # Manager can modify IT Admin
        >>> can_modify_subordinate(manager, it_admin)
        True

        >>> # IT Admin can modify Technician
        >>> can_modify_subordinate(it_admin, technician)
        True

        >>> # Same rank cannot modify (SUPERADMIN vs MANAGER)
        >>> can_modify_subordinate(superadmin, manager)
        False

        >>> # Lower rank cannot modify higher
        >>> can_modify_subordinate(technician, manager)
        False
    """
    return has_strictly_higher_role(actor.role, target.role)


def can_modify_owned_or_subordinate(actor, resource_owner) -> bool:
    """
    Check if actor can modify a resource owned by another user.

    Authorization rules:
    1. Allow if actor has admin override (SUPERADMIN or MANAGER)
    2. Allow if actor is the resource owner
    3. Allow if actor has strictly higher role rank than resource_owner
    4. Deny otherwise

    This is the most common authorization pattern for resource modification.

    Args:
        actor: User instance attempting the action
        resource_owner: User instance who owns the resource

    Returns:
        bool: True if actor is authorized to modify the resource

    Examples:
        >>> # Admin override
        >>> can_modify_owned_or_subordinate(superadmin, regular_user)
        True

        >>> # Owner can modify their own resource
        >>> can_modify_owned_or_subordinate(john, john)
        True

        >>> # Higher role can modify lower role
        >>> can_modify_owned_or_subordinate(manager, technician)
        True

        >>> # Same rank cannot modify
        >>> can_modify_owned_or_subordinate(technician_a, technician_b)
        False

        >>> # Lower rank cannot modify higher
        >>> can_modify_owned_or_subordinate(technician, manager)
        False
    """
    # Rule 1: Admin override (SUPERADMIN or MANAGER)
    if is_admin_override(actor):
        return True

    # Rule 2: Owner can modify their own resource
    if is_owner(actor, resource_owner):
        return True

    # Rule 3: Higher role can modify lower role (strictly higher)
    if can_modify_subordinate(actor, resource_owner):
        return True

    # Deny otherwise
    return False

