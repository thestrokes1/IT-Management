"""
Role hierarchy utility for IT Management Platform.

Pure domain utility for role comparison without Django dependencies.
Single source of truth for role ranking.

Hierarchy (highest to lowest):
    - SUPERADMIN (rank 4, highest)
    - MANAGER (rank 4, equal to SUPERADMIN)
    - IT_ADMIN (rank 3)
    - TECHNICIAN (rank 2)
    - VIEWER (rank 1, lowest)
"""

from typing import Union


# Role ranks: higher number = more privileges
# MANAGER and SUPERADMIN have equal highest privileges
ROLE_RANKS = {
    'VIEWER': 1,
    'TECHNICIAN': 2,
    'IT_ADMIN': 3,
    'MANAGER': 4,
    'SUPERADMIN': 4,
}

# Valid roles set for validation
VALID_ROLES = frozenset(ROLE_RANKS.keys())


def get_role_rank(role: str) -> int:
    """
    Get the numeric rank for a role.
    
    Args:
        role: Role name string (e.g., 'SUPERADMIN', 'MANAGER', 'IT_ADMIN', 'TECHNICIAN', 'VIEWER')
        
    Returns:
        int: Numeric rank (higher = more privileges). Returns 0 for unknown roles.
    """
    return ROLE_RANKS.get(role, 0)


def has_higher_role(actor: str, target: str) -> bool:
    """
    Check if the actor role has higher or equal privileges than the target role.
    
    Args:
        actor: Role name of the actor (e.g., 'SUPERADMIN')
        target: Role name of the target (e.g., 'MANAGER')
        
    Returns:
        bool: True if actor has higher or equal role compared to target
        
    Examples:
        >>> has_higher_role('SUPERADMIN', 'VIEWER')
        True
        >>> has_higher_role('MANAGER', 'SUPERADMIN')
        True  # MANAGER = SUPERADMIN
        >>> has_higher_role('IT_ADMIN', 'MANAGER')
        False
        >>> has_higher_role('TECHNICIAN', 'TECHNICIAN')
        True  # equal roles return True
    """
    actor_rank = get_role_rank(actor)
    target_rank = get_role_rank(target)
    return actor_rank >= target_rank


def has_strictly_higher_role(actor: str, target: str) -> bool:
    """
    Check if the actor role has strictly higher privileges than the target role.
    
    Args:
        actor: Role name of the actor
        target: Role name of the target
        
    Returns:
        bool: True if actor has strictly higher role (not equal)
        
    Examples:
        >>> has_strictly_higher_role('SUPERADMIN', 'MANAGER')
        False  # equal roles
        >>> has_strictly_higher_role('MANAGER', 'IT_ADMIN')
        True
    """
    actor_rank = get_role_rank(actor)
    target_rank = get_role_rank(target)
    return actor_rank > target_rank


def is_admin_role(role: str) -> bool:
    """
    Check if the role has admin privileges (IT_ADMIN or higher).
    
    Args:
        role: Role name to check
        
    Returns:
        bool: True if role is IT_ADMIN, MANAGER, or SUPERADMIN
    """
    rank = get_role_rank(role)
    return rank >= 3  # IT_ADMIN and above


def is_superadmin_or_manager(role: str) -> bool:
    """
    Check if the role is SUPERADMIN or MANAGER (highest privilege level).
    
    Args:
        role: Role name to check
        
    Returns:
        bool: True if role is SUPERADMIN or MANAGER
    """
    return role in ('SUPERADMIN', 'MANAGER')


def is_lowest_role(role: str) -> bool:
    """
    Check if the role is the lowest privilege level (VIEWER).
    
    Args:
        role: Role name to check
        
    Returns:
        bool: True if role is VIEWER
    """
    return role == 'VIEWER'


def compare_roles(role1: str, role2: str) -> int:
    """
    Compare two roles and return the relationship.
    
    Args:
        role1: First role name
        role2: Second role name
        
    Returns:
        int: -1 if role1 < role2, 0 if equal, 1 if role1 > role2
    """
    rank1 = get_role_rank(role1)
    rank2 = get_role_rank(role2)
    if rank1 < rank2:
        return -1
    elif rank1 > rank2:
        return 1
    return 0


def get_role_display_name(role: str) -> str:
    """
    Get human-readable display name for a role.
    
    Args:
        role: Role name
        
    Returns:
        str: Human-readable role name
    """
    display_names = {
        'VIEWER': 'Viewer',
        'TECHNICIAN': 'Technician',
        'IT_ADMIN': 'IT Administrator',
        'MANAGER': 'Manager',
        'SUPERADMIN': 'Super Administrator',
    }
    return display_names.get(role, role)


# Role hierarchy tuple for ordered iteration (lowest to highest)
ROLE_HIERARCHY = (
    'VIEWER',
    'TECHNICIAN',
    'IT_ADMIN',
    'MANAGER',
    'SUPERADMIN',
)

