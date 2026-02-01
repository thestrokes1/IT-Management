"""
Project authorization domain service.

Pure domain layer authorization for project management.
No Django dependencies.

Role Hierarchy (highest to lowest):
    - SUPERADMIN (rank 4) - Full access, no restrictions
    - MANAGER (rank 4) - Same as SUPERADMIN
    - IT_ADMIN (rank 3) - Can view and edit projects
    - TECHNICIAN (rank 2) - Read-only access to projects
    - VIEWER (rank 1) - No project access
"""

from apps.core.domain.roles import (
    has_higher_role, 
    has_strictly_higher_role,
    is_superadmin_or_manager,
    is_admin_role,
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

def can_view(user, project) -> bool:
    """
    Check if user can view a project.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed (full access)
    - IT_ADMIN: always allowed (can view projects)
    - TECHNICIAN: always allowed (read-only project access)
    - VIEWER: NOT allowed - VIEWER has no project access
    
    Args:
        user: User instance
        project: Project instance
        
    Returns:
        bool: True if user can view the project
    """
    # VIEWER has no project access
    if user.role == _ROLE_VIEWER:
        return False
    
    # All other roles can view projects
    return True


def can_view_list(user) -> bool:
    """
    Check if user can view the project list.
    
    Rules:
    - VIEWER: NOT allowed
    - All other authenticated roles: allowed
    
    Args:
        user: User instance
        
    Returns:
        bool: True if user can view project list
    """
    return user.role != _ROLE_VIEWER


def can_view_details(user, project) -> bool:
    """
    Check if user can view project details.
    
    Same as can_view.
    
    Args:
        user: User instance
        project: Project instance
        
    Returns:
        bool: True if user can view project details
    """
    return can_view(user, project)


# =============================================================================
# CREATE PERMISSIONS
# =============================================================================

def can_create(user) -> bool:
    """
    Check if user can create projects.

    Rules:
    - MANAGER and above can create projects

    Args:
        user: User instance

    Returns:
        bool: True if user can create projects
    """
    return has_higher_role(user.role, _ROLE_MANAGER)


# =============================================================================
# EDIT / UPDATE PERMISSIONS
# =============================================================================

def can_edit(user, project) -> bool:
    """
    Check if user can edit a project.

    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (can edit projects)
    - TECHNICIAN: NOT allowed (read-only)
    - VIEWER: NOT allowed

    Args:
        user: User instance attempting the action
        project: Project instance

    Returns:
        bool: True if user can edit the project
    """
    # VIEWER cannot edit
    if user.role == _ROLE_VIEWER:
        return False
    
    # TECHNICIAN cannot edit (read-only)
    if user.role == _ROLE_TECHNICIAN:
        return False
    
    # SUPERADMIN, MANAGER, IT_ADMIN can edit
    return True


def can_update(user, project) -> bool:
    """
    Alias for can_edit.
    
    Args:
        user: User instance
        project: Project instance
        
    Returns:
        bool: True if user can update the project
    """
    return can_edit(user, project)


# =============================================================================
# DELETE PERMISSIONS
# =============================================================================

def can_delete(user, project) -> bool:
    """
    Check if user can delete a project.

    Rules:
    - SUPERADMIN: always allowed
    - MANAGER: NOT allowed (per spec)
    - IT_ADMIN: NOT allowed (per spec: cannot delete unless stated later)
    - TECHNICIAN: NOT allowed
    - VIEWER: NOT allowed

    Args:
        user: User instance attempting the action
        project: Project instance

    Returns:
        bool: True if user can delete the project
    """
    # Only SUPERADMIN can delete projects
    return user.role == _ROLE_SUPERADMIN


# =============================================================================
# ASSIGN / UNASSIGN PERMISSIONS
# =============================================================================

def can_assign(user, project, assignee) -> bool:
    """
    Check if user can assign project members.

    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (can assign project members)
    - TECHNICIAN: NEVER allowed (cannot assign)
    - VIEWER: NOT allowed

    Args:
        user: User instance attempting to assign
        project: Project instance being modified
        assignee: User instance to assign to project (unused but required by interface)
        
    Returns:
        bool: True if user can assign project members
    """
    # VIEWER cannot assign
    if user.role == _ROLE_VIEWER:
        return False
    
    # TECHNICIAN cannot assign
    if user.role == _ROLE_TECHNICIAN:
        return False
    
    # SUPERADMIN, MANAGER, IT_ADMIN can assign
    return True


def can_unassign(user, project) -> bool:
    """
    Check if user can unassign project members.

    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (can unassign project members)
    - TECHNICIAN: NEVER allowed
    - VIEWER: NOT allowed

    Args:
        user: User instance attempting to unassign
        project: Project instance
        
    Returns:
        bool: True if user can unassign project members
    """
    # VIEWER cannot unassign
    if user.role == _ROLE_VIEWER:
        return False
    
    # TECHNICIAN cannot unassign
    if user.role == _ROLE_TECHNICIAN:
        return False
    
    # SUPERADMIN, MANAGER, IT_ADMIN can unassign
    return True


def can_assign_to_self(user, project) -> bool:
    """
    Check if user can self-assign to a project.
    
    For projects, this typically means joining as a team member.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: allowed (can join projects)
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        project: Project instance
        
    Returns:
        bool: True if user can self-assign to the project
    """
    # VIEWER cannot self-assign
    if user.role == _ROLE_VIEWER:
        return False
    
    # All other roles can self-assign to projects
    return True


def can_unassign_self(user, project) -> bool:
    """
    Check if user can unassign themselves from a project.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: allowed (can leave projects)
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        project: Project instance
        
    Returns:
        bool: True if user can unassign themselves from the project
    """
    # VIEWER cannot unassign
    if user.role == _ROLE_VIEWER:
        return False
    
    # All other roles can unassign themselves
    return True


# =============================================================================
# PROJECT MEMBER PERMISSIONS
# =============================================================================

def can_manage_members(user, project) -> bool:
    """
    Check if user can manage project team members.
    
    Same as can_assign.
    
    Args:
        user: User instance
        project: Project instance
        
    Returns:
        bool: True if user can manage project members
    """
    return can_assign(user, project, None)


# =============================================================================
# PROJECT LOGS / HISTORY
# =============================================================================

def can_view_logs(user, project) -> bool:
    """
    Check if user can view project logs/history.

    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: NOT allowed
    - VIEWER: NOT allowed

    Args:
        user: User instance
        project: Project instance

    Returns:
        bool: True if user can view project logs
    """
    # VIEWER and TECHNICIAN cannot view logs
    if user.role in (_ROLE_VIEWER, _ROLE_TECHNICIAN):
        return False
    
    # SUPERADMIN, MANAGER, IT_ADMIN can view logs
    return True


# =============================================================================
# PERMISSION AGGREGATION
# =============================================================================

def get_permissions(user, project) -> dict:
    """
    Get all permissions for a user on a specific project.

    Args:
        user: User instance
        project: Project instance

    Returns:
        dict: Dictionary with permission keys and boolean values
    """
    return {
        'can_view': can_view(user, project),
        'can_edit': can_edit(user, project),
        'can_delete': can_delete(user, project),
        'can_assign': can_assign(user, project, None),
        'can_unassign': can_unassign(user, project),
        'can_assign_to_self': can_assign_to_self(user, project),
        'can_unassign_self': can_unassign_self(user, project),
        'can_manage_members': can_manage_members(user, project),
        'can_view_logs': can_view_logs(user, project),
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

def assert_can_view(user, project) -> None:
    """
    Assert that user can view the project.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_view(user, project):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to view project"
        )


def assert_can_create(user) -> None:
    """
    Assert that user can create projects.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_create(user):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to create projects"
        )


def assert_can_edit(user, project) -> None:
    """
    Assert that user can edit the project.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_edit(user, project):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to edit project"
        )


def assert_can_delete(user, project) -> None:
    """
    Assert that user can delete the project.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_delete(user, project):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to delete project"
        )


def assert_can_assign(user, project, assignee) -> None:
    """
    Assert that user can assign project members.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_assign(user, project, assignee):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to assign project members"
        )


def assert_can_unassign(user, project) -> None:
    """
    Assert that user can unassign project members.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_unassign(user, project):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to unassign project members"
        )


def assert_can_view_logs(user, project) -> None:
    """
    Assert that user can view project logs.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_view_logs(user, project):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to view project logs"
        )


# =============================================================================
# LEGACY ALIASES (for backward compatibility)
# =============================================================================

def can_read_project(user, project) -> bool:
    """Alias for can_view."""
    return can_view(user, project)


def can_update_project(user, project) -> bool:
    """Alias for can_edit."""
    return can_edit(user, project)


def can_delete_project(user, project) -> bool:
    """Alias for can_delete."""
    return can_delete(user, project)


def can_assign_project_members(user, project) -> bool:
    """Alias for can_assign."""
    return can_assign(user, project, None)


def can_view_project_logs(user, project) -> bool:
    """Alias for can_view_logs."""
    return can_view_logs(user, project)


def get_project_permissions(user, project) -> dict:
    """Alias for get_permissions."""
    return get_permissions(user, project)


def can_create_project(user) -> bool:
    """Alias for can_create."""
    return can_create(user)


# Legacy assertion aliases
def assert_can_update_project(user, project) -> None:
    return assert_can_edit(user, project)


def assert_can_delete_project(user, project) -> None:
    return assert_can_delete(user, project)


def assert_can_assign_project_members(user, project) -> None:
    return assert_can_assign(user, project, None)


def assert_can_read_project(user, project) -> None:
    return assert_can_view(user, project)


def assert_can_create_project(user) -> None:
    return assert_can_create(user)

